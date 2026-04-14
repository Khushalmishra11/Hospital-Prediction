from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from .model_service import LoadPredictorService, ModelNotTrainedError
from .schemas import PredictionRequest, PredictionResponse, TrainResponse
from .auth_service import AuthService, UserRegisterRequest
from .database import PredictionDatabase
from .firebase_config import initialize_firebase


app = FastAPI(title="Smart Appointment & Load Prediction API", version="1.0.0")
service = LoadPredictorService()
db_service = PredictionDatabase()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(authorization: str = Header(None)) -> str:
    """Extract and verify user from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        token = authorization.replace("Bearer ", "")
        decoded = AuthService.verify_token(token)
        return decoded.get("uid")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@app.on_event("startup")
def startup_event() -> None:
    try:
        initialize_firebase()
        service._ensure_model_loaded()
    except ModelNotTrainedError:
        service.train_and_save()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ==================== Authentication Endpoints ====================

@app.post("/auth/register")
def register(request: UserRegisterRequest) -> dict:
    """Register a new user."""
    try:
        user_data = AuthService.register_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        return {"status": "success", "user": user_data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/verify-token")
def verify_token(authorization: str = Header(None)) -> dict:
    """Verify Firebase ID token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        token = authorization.replace("Bearer ", "")
        decoded = AuthService.verify_token(token)
        return {"status": "valid", "user_id": decoded.get("uid"), "email": decoded.get("email")}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/auth/profile")
def get_profile(user_id: str = Depends(get_current_user)) -> dict:
    """Get current user profile."""
    try:
        profile = AuthService.get_user_profile(user_id)
        return {"status": "success", "profile": profile}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Prediction Endpoints ====================
@app.post("/train", response_model=TrainResponse)
def train_model() -> TrainResponse:
    result = service.train_and_save()
    return TrainResponse(**result)


@app.post("/predict", response_model=PredictionResponse)
def predict_load(payload: PredictionRequest, user_id: str = Depends(get_current_user)) -> PredictionResponse:
    try:
        feature_dict = payload.model_dump()
        feature_dict["is_holiday"] = int(payload.is_holiday)

        predicted_load = service.predict_load(feature_dict)
        wait_minutes = service.estimate_wait_minutes(
            predicted_load=predicted_load,
            doctor_count=payload.doctor_count,
            avg_consultation_minutes=payload.avg_consultation_minutes,
        )
        risk = service.risk_level(predicted_load)

        result = PredictionResponse(
            predicted_load_score=round(predicted_load, 2),
            expected_wait_minutes=wait_minutes,
            risk_level=risk,
        )

        # Save to Firestore
        db_service.save_prediction(
            user_id=user_id,
            input_data=feature_dict,
            prediction_result=result.model_dump()
        )

        return result
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/predictions/history")
def get_prediction_history(user_id: str = Depends(get_current_user), limit: int = 50):
    """Get user's prediction history."""
    try:
        predictions = db_service.get_user_predictions(user_id, limit)
        return {"status": "success", "predictions": predictions, "count": len(predictions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/statistics")
def get_statistics(user_id: str = Depends(get_current_user)):
    """Get user's prediction statistics."""
    try:
        stats = db_service.get_statistics(user_id)
        return {"status": "success", "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/predictions/{prediction_id}")
def delete_prediction(prediction_id: str, user_id: str = Depends(get_current_user)):
    """Delete a specific prediction."""
    try:
        db_service.delete_prediction(user_id, prediction_id)
        return {"status": "success", "message": "Prediction deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
