from __future__ import annotations

from datetime import datetime
from typing import Any

from firebase_admin import firestore

from .firebase_config import get_firestore_db


class PredictionDatabase:
    """Service for storing and retrieving predictions from Firestore."""

    @staticmethod
    def _to_json_safe(value: Any) -> Any:
        """Convert Firestore values into JSON-safe structures."""
        if isinstance(value, dict):
            return {k: PredictionDatabase._to_json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [PredictionDatabase._to_json_safe(v) for v in value]
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                return str(value)
        return value

    @staticmethod
    def save_prediction(
        user_id: str,
        input_data: dict[str, Any],
        prediction_result: dict[str, Any],
    ) -> str:
        """Save prediction to Firestore."""
        db = get_firestore_db()
        
        prediction_doc = {
            "user_id": user_id,
            "input_data": input_data,
            "predicted_load_score": prediction_result["predicted_load_score"],
            "expected_wait_minutes": prediction_result["expected_wait_minutes"],
            "risk_level": prediction_result["risk_level"],
            "timestamp": firestore.SERVER_TIMESTAMP,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Add to predictions collection
        doc_ref = db.collection("predictions").add(prediction_doc)
        
        # Update user's prediction count
        db.collection("users").document(user_id).update({
            "predictions_count": firestore.Increment(1),
            "last_prediction_at": firestore.SERVER_TIMESTAMP,
        })

        return doc_ref[1].id if isinstance(doc_ref, tuple) else str(doc_ref)

    @staticmethod
    def get_user_predictions(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get all predictions for a user."""
        db = get_firestore_db()

        # Try indexed query first. If composite index is unavailable, fallback to
        # a plain where-query and sort in memory to keep the app usable.
        try:
            docs = (
                db.collection("predictions")
                .where("user_id", "==", user_id)
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            docs_list = list(docs)
        except Exception:
            docs_list = list(
                db.collection("predictions")
                .where("user_id", "==", user_id)
                .stream()
            )
            docs_list.sort(
                key=lambda d: (d.to_dict().get("timestamp") or d.to_dict().get("created_at") or ""),
                reverse=True,
            )
            docs_list = docs_list[:limit]

        predictions = []
        for doc in docs_list:
            data = PredictionDatabase._to_json_safe(doc.to_dict())
            data["id"] = doc.id
            predictions.append(data)

        return predictions

    @staticmethod
    def delete_prediction(user_id: str, prediction_id: str) -> bool:
        """Delete a prediction."""
        db = get_firestore_db()
        
        # Verify ownership
        doc = db.collection("predictions").document(prediction_id).get()
        if not doc.exists or doc.to_dict().get("user_id") != user_id:
            raise ValueError("Prediction not found or unauthorized")

        db.collection("predictions").document(prediction_id).delete()
        
        # Update user's prediction count
        db.collection("users").document(user_id).update({
            "predictions_count": firestore.Increment(-1),
        })

        return True

    @staticmethod
    def get_statistics(user_id: str) -> dict[str, Any]:
        """Get statistics for a user."""
        db = get_firestore_db()
        
        predictions = (
            db.collection("predictions")
            .where("user_id", "==", user_id)
            .stream()
        )

        data = list(predictions)
        if not data:
            return {
                "total_predictions": 0,
                "avg_wait_time": 0,
                "high_risk_count": 0,
            }

        records = [doc.to_dict() for doc in data]
        wait_times = [
            r.get("expected_wait_minutes", 0)
            for r in records
            if r.get("expected_wait_minutes") is not None
        ]
        high_risk = sum(
            1 for r in records if r.get("risk_level") == "HIGH"
        )

        return {
            "total_predictions": len(records),
            "avg_wait_time": sum(wait_times) / len(wait_times) if wait_times else 0,
            "high_risk_count": high_risk,
        }
