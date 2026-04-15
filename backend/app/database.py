from __future__ import annotations

from datetime import date, datetime, timedelta
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

    @staticmethod
    def create_or_update_doctor(payload: dict[str, Any]) -> dict[str, Any]:
        """Create or update a doctor profile used by availability and optimization flows."""
        db = get_firestore_db()
        doc = {
            "doctor_id": payload["doctor_id"],
            "name": payload["name"],
            "specialty": payload["specialty"],
            "status": payload.get("status", "available"),
            "current_queue_count": int(payload.get("current_queue_count", 0)),
            "avg_consultation_minutes": float(payload.get("avg_consultation_minutes", 15)),
            "shift_start": payload["shift_start"],
            "shift_end": payload["shift_end"],
            "updated_at": datetime.utcnow().isoformat(),
        }
        db.collection("doctors").document(payload["doctor_id"]).set(doc, merge=True)
        return doc

    @staticmethod
    def update_doctor_status(doctor_id: str, status: str) -> dict[str, Any]:
        db = get_firestore_db()
        ref = db.collection("doctors").document(doctor_id)
        if not ref.get().exists:
            raise ValueError("Doctor not found")
        ref.set({"status": status, "updated_at": datetime.utcnow().isoformat()}, merge=True)
        return PredictionDatabase._to_json_safe(ref.get().to_dict())

    @staticmethod
    def get_doctor_availability(specialty: str | None = None) -> list[dict[str, Any]]:
        db = get_firestore_db()
        docs = db.collection("doctors").stream()
        doctors: list[dict[str, Any]] = []
        for doc in docs:
            data = PredictionDatabase._to_json_safe(doc.to_dict())
            if specialty and data.get("specialty") != specialty:
                continue
            doctors.append(data)
        doctors.sort(key=lambda d: (d.get("specialty", ""), d.get("name", "")))
        return doctors

    @staticmethod
    def upsert_shift(payload: dict[str, Any]) -> str:
        db = get_firestore_db()
        key = f"{payload['doctor_id']}_{payload['date']}"
        doc = {
            "doctor_id": payload["doctor_id"],
            "date": str(payload["date"]),
            "start_time": payload["start_time"],
            "end_time": payload["end_time"],
            "slot_duration_minutes": int(payload.get("slot_duration_minutes", 15)),
            "is_available": bool(payload.get("is_available", True)),
            "updated_at": datetime.utcnow().isoformat(),
        }
        db.collection("doctor_shifts").document(key).set(doc, merge=True)
        return key

    @staticmethod
    def _combine_dt(d: date, hhmm: str) -> datetime:
        parsed_time = datetime.strptime(hhmm, "%H:%M").time()
        return datetime.combine(d, parsed_time)

    @staticmethod
    def get_available_slots(target_date: date, specialty: str | None = None) -> list[dict[str, Any]]:
        """Generate free slots by subtracting booked appointment windows from shift windows."""
        db = get_firestore_db()
        date_str = str(target_date)
        shifts = list(
            db.collection("doctor_shifts")
            .where("date", "==", date_str)
            .where("is_available", "==", True)
            .stream()
        )
        doctors = {
            doc.id: doc.to_dict()
            for doc in db.collection("doctors").stream()
        }

        slots: list[dict[str, Any]] = []
        for shift_doc in shifts:
            shift = shift_doc.to_dict()
            doctor_id = shift["doctor_id"]
            doctor = doctors.get(doctor_id)
            if not doctor:
                continue
            if specialty and doctor.get("specialty") != specialty:
                continue
            if doctor.get("status") in {"offline", "break"}:
                continue

            start_dt = PredictionDatabase._combine_dt(target_date, shift["start_time"])
            end_dt = PredictionDatabase._combine_dt(target_date, shift["end_time"])
            slot_step = timedelta(minutes=int(shift.get("slot_duration_minutes", 15)))

            appointments = list(
                db.collection("appointments")
                .where("doctor_id", "==", doctor_id)
                .where("slot_date", "==", date_str)
                .stream()
            )
            blocked_ranges = []
            for appt in appointments:
                a = appt.to_dict()
                if a.get("status") in {"cancelled", "no_show"}:
                    continue
                blocked_ranges.append((a.get("slot_start"), a.get("slot_end")))

            current = start_dt
            while current + slot_step <= end_dt:
                slot_start = current.isoformat()
                slot_end = (current + slot_step).isoformat()
                overlaps = any(not (slot_end <= b_start or slot_start >= b_end) for b_start, b_end in blocked_ranges)
                if not overlaps:
                    slots.append(
                        {
                            "doctor_id": doctor_id,
                            "doctor_name": doctor.get("name", doctor_id),
                            "specialty": doctor.get("specialty", "General"),
                            "slot_start": slot_start,
                            "slot_end": slot_end,
                        }
                    )
                current += slot_step

        slots.sort(key=lambda s: (s["slot_start"], s["doctor_name"]))
        return slots

    @staticmethod
    def create_appointment(payload: dict[str, Any]) -> str:
        """Create appointment after conflict check for same doctor and time window."""
        db = get_firestore_db()
        slot_start = payload["slot_start"]
        slot_end = payload["slot_end"]
        slot_date = datetime.fromisoformat(slot_start).date().isoformat()

        existing = list(
            db.collection("appointments")
            .where("doctor_id", "==", payload["doctor_id"])
            .where("slot_date", "==", slot_date)
            .stream()
        )
        for appt in existing:
            row = appt.to_dict()
            if row.get("status") in {"cancelled", "no_show"}:
                continue
            if not (slot_end <= row.get("slot_start") or slot_start >= row.get("slot_end")):
                raise ValueError("Selected slot is already booked")

        doc = {
            "patient_id": payload["patient_id"],
            "doctor_id": payload["doctor_id"],
            "slot_start": slot_start,
            "slot_end": slot_end,
            "slot_date": slot_date,
            "status": "booked",
            "booking_channel": payload.get("booking_channel", "web"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        doc_ref = db.collection("appointments").add(doc)
        return doc_ref[1].id if isinstance(doc_ref, tuple) else str(doc_ref)

    @staticmethod
    def update_appointment_status(appointment_id: str, status: str) -> dict[str, Any]:
        db = get_firestore_db()
        ref = db.collection("appointments").document(appointment_id)
        snap = ref.get()
        if not snap.exists:
            raise ValueError("Appointment not found")

        existing = snap.to_dict()
        updates = {"status": status, "updated_at": datetime.utcnow().isoformat()}
        if status == "checked_in":
            updates["check_in_at"] = datetime.utcnow().isoformat()
        elif status == "in_consult":
            updates["consult_start_at"] = datetime.utcnow().isoformat()
        elif status == "completed":
            updates["consult_end_at"] = datetime.utcnow().isoformat()

        ref.set(updates, merge=True)
        return PredictionDatabase._to_json_safe({**existing, **updates})

    @staticmethod
    def get_appointments(
        target_date: str | None = None,
        doctor_id: str | None = None,
        status: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Fetch appointments with optional filters, defaulting to today's date."""
        db = get_firestore_db()
        resolved_date = target_date or datetime.utcnow().date().isoformat()

        docs = list(
            db.collection("appointments")
            .where("slot_date", "==", resolved_date)
            .stream()
        )

        rows: list[dict[str, Any]] = []
        for snap in docs:
            item = PredictionDatabase._to_json_safe(snap.to_dict())
            item["id"] = snap.id
            if doctor_id and item.get("doctor_id") != doctor_id:
                continue
            if status and item.get("status") != status:
                continue
            rows.append(item)

        rows.sort(key=lambda r: (r.get("slot_start", ""), r.get("doctor_id", "")))
        return rows[:limit]

    @staticmethod
    def log_queue_event(payload: dict[str, Any]) -> str:
        db = get_firestore_db()
        doc = {
            "appointment_id": payload["appointment_id"],
            "doctor_id": payload["doctor_id"],
            "event_type": payload["event_type"],
            "source": payload.get("source", "system"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        doc_ref = db.collection("queue_events").add(doc)
        return doc_ref[1].id if isinstance(doc_ref, tuple) else str(doc_ref)

    @staticmethod
    def get_live_queue_summary() -> dict[str, Any]:
        db = get_firestore_db()
        today = datetime.utcnow().date().isoformat()
        appointments = list(
            db.collection("appointments").where("slot_date", "==", today).stream()
        )

        total_waiting = 0
        in_consult = 0
        completed = 0
        no_show = 0
        wait_samples: list[float] = []
        by_doctor: dict[str, int] = {}
        now = datetime.utcnow()

        for snap in appointments:
            appt = snap.to_dict()
            doctor_id = appt.get("doctor_id", "unknown")
            status = appt.get("status")
            by_doctor[doctor_id] = by_doctor.get(doctor_id, 0)

            if status in {"booked", "checked_in"}:
                total_waiting += 1
                by_doctor[doctor_id] += 1
            if status == "in_consult":
                in_consult += 1
            if status == "completed":
                completed += 1
            if status == "no_show":
                no_show += 1

            if status == "checked_in" and appt.get("check_in_at"):
                try:
                    checked_in_at = datetime.fromisoformat(appt["check_in_at"])
                    wait_samples.append((now - checked_in_at).total_seconds() / 60.0)
                except Exception:
                    pass

        avg_wait = sum(wait_samples) / len(wait_samples) if wait_samples else 0.0
        return {
            "total_waiting": total_waiting,
            "in_consult": in_consult,
            "completed_today": completed,
            "no_show_today": no_show,
            "avg_wait_minutes_checked_in": round(avg_wait, 2),
            "by_doctor": by_doctor,
        }

    @staticmethod
    def recommend_doctor(specialty: str) -> dict[str, Any]:
        """Recommend doctor by lowest weighted load among available doctors in specialty."""
        doctors = PredictionDatabase.get_doctor_availability(specialty=specialty)
        candidates = [
            d for d in doctors if d.get("status") in {"available", "busy"}
        ]
        if not candidates:
            raise ValueError("No available doctors for requested specialty")

        best: dict[str, Any] | None = None
        best_score = float("inf")
        for doc in candidates:
            queue = float(doc.get("current_queue_count", 0))
            consult = float(doc.get("avg_consultation_minutes", 15))
            status_penalty = 0.0 if doc.get("status") == "available" else 5.0
            score = queue * consult + status_penalty
            if score < best_score:
                best_score = score
                best = doc

        assert best is not None
        return {
            "doctor_id": best.get("doctor_id", ""),
            "name": best.get("name", ""),
            "specialty": best.get("specialty", ""),
            "status": best.get("status", ""),
            "weighted_load_score": round(best_score, 2),
        }

    @staticmethod
    def get_available_doctors_for_slot(
        slot_start: str,
        slot_end: str,
        specialty: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return doctors who are available and free for a specific slot interval."""
        db = get_firestore_db()
        start_dt = datetime.fromisoformat(slot_start)
        end_dt = datetime.fromisoformat(slot_end)
        if end_dt <= start_dt:
            raise ValueError("slot_end must be greater than slot_start")

        date_str = start_dt.date().isoformat()
        wanted_specialty = specialty.strip().lower() if specialty else None
        doctors = {
            doc.id: PredictionDatabase._to_json_safe(doc.to_dict())
            for doc in db.collection("doctors").stream()
        }

        shifts = list(
            db.collection("doctor_shifts")
            .where("date", "==", date_str)
            .where("is_available", "==", True)
            .stream()
        )

        appointments = list(
            db.collection("appointments")
            .where("slot_date", "==", date_str)
            .stream()
        )

        blocked_by_doctor: dict[str, list[tuple[str, str]]] = {}
        for appt in appointments:
            row = appt.to_dict()
            if row.get("status") in {"cancelled", "no_show"}:
                continue
            doctor_id = row.get("doctor_id")
            if not doctor_id:
                continue
            blocked_by_doctor.setdefault(doctor_id, []).append(
                (row.get("slot_start"), row.get("slot_end"))
            )

        # Build shift map for the target date; if a doctor has no entry in
        # doctor_shifts, fallback to profile-level shift_start/shift_end.
        shift_map: dict[str, dict[str, Any]] = {}
        for shift_doc in shifts:
            shift = PredictionDatabase._to_json_safe(shift_doc.to_dict())
            doctor_id = shift.get("doctor_id")
            if doctor_id:
                shift_map[doctor_id] = shift

        available: list[dict[str, Any]] = []
        for doctor_id, doctor in doctors.items():
            status = str(doctor.get("status", "")).lower()
            if status != "available":
                continue

            doctor_specialty = str(doctor.get("specialty", "")).strip()
            if wanted_specialty and doctor_specialty.lower() != wanted_specialty:
                continue

            shift = shift_map.get(doctor_id)
            start_hhmm = None
            end_hhmm = None
            if shift:
                start_hhmm = shift.get("start_time")
                end_hhmm = shift.get("end_time")
            else:
                # Fallback: use shift window from doctor profile if per-day shift
                # rows were not created.
                start_hhmm = doctor.get("shift_start")
                end_hhmm = doctor.get("shift_end")

            if not start_hhmm or not end_hhmm:
                continue

            shift_start_dt = PredictionDatabase._combine_dt(start_dt.date(), start_hhmm)
            shift_end_dt = PredictionDatabase._combine_dt(start_dt.date(), end_hhmm)
            if start_dt < shift_start_dt or end_dt > shift_end_dt:
                continue

            overlap = False
            for b_start, b_end in blocked_by_doctor.get(doctor_id, []):
                if not b_start or not b_end:
                    continue
                if not (slot_end <= b_start or slot_start >= b_end):
                    overlap = True
                    break

            if overlap:
                continue

            available.append(
                {
                    "doctor_id": doctor.get("doctor_id", doctor_id),
                    "name": doctor.get("name", doctor_id),
                    "specialty": doctor_specialty or "General",
                    "status": doctor.get("status", "available"),
                    "shift_start": start_hhmm,
                    "shift_end": end_hhmm,
                    "slot_date": date_str,
                }
            )

        available.sort(key=lambda d: (d.get("specialty", ""), d.get("name", "")))
        return available
