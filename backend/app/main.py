from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from .model_service import LoadPredictorService, ModelNotTrainedError
from .schemas import (
    AppointmentCreateRequest,
    AppointmentStatusUpdateRequest,
    DoctorCreateRequest,
    DoctorStatusUpdateRequest,
    OptimizerResponse,
    PredictionRequest,
    PredictionResponse,
    QueueEventRequest,
    QueueSummaryResponse,
    ShiftUpsertRequest,
    TrainResponse,
)
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
        total_patients = payload.scheduled_appointments + payload.walk_in_patients

        predicted_load = service.predict_load(feature_dict)

        # Operational guardrail for low-volume scenarios: when patients are fewer
        # than or equal to available doctors, cap the displayed load to a realistic level.
        if total_patients <= payload.doctor_count:
            predicted_load = min(predicted_load, float(total_patients))

        wait_minutes = service.estimate_wait_minutes(
            predicted_load=predicted_load,
            doctor_count=payload.doctor_count,
            avg_consultation_minutes=payload.avg_consultation_minutes,
            demand_patients=float(total_patients),
        )
        service_capacity = max(payload.doctor_count, 1) * (
            60.0 / max(payload.avg_consultation_minutes, 1.0)
        )
        demand_utilization = float(total_patients) / max(service_capacity, 0.1)
        if total_patients <= payload.doctor_count or demand_utilization <= 0.40:
            risk = "LOW"
        else:
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


# ==================== Lightweight Operations Endpoints ====================

@app.post("/doctors")
def create_or_update_doctor(payload: DoctorCreateRequest, user_id: str = Depends(get_current_user)):
    """Create or update doctor profile for scheduling and queue dashboards."""
    try:
        doctor = db_service.create_or_update_doctor(payload.model_dump())
        return {"status": "success", "doctor": doctor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/doctors/{doctor_id}/status")
def update_doctor_status(doctor_id: str, payload: DoctorStatusUpdateRequest, user_id: str = Depends(get_current_user)):
    try:
        doctor = db_service.update_doctor_status(doctor_id, payload.status)
        return {"status": "success", "doctor": doctor}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/doctors/availability")
def get_doctor_availability(specialty: str | None = None, user_id: str = Depends(get_current_user)):
    try:
        data = db_service.get_doctor_availability(specialty=specialty)
        return {"status": "success", "doctors": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/doctors/available-slot")
def get_available_doctors_for_slot(
    slot_start: str,
    slot_end: str,
    specialty: str | None = None,
    user_id: str = Depends(get_current_user),
):
    try:
        doctors = db_service.get_available_doctors_for_slot(
            slot_start=slot_start,
            slot_end=slot_end,
            specialty=specialty,
        )
        return {"status": "success", "doctors": doctors, "count": len(doctors)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/shifts")
def upsert_shift(payload: ShiftUpsertRequest, user_id: str = Depends(get_current_user)):
    try:
        shift_id = db_service.upsert_shift(payload.model_dump())
        return {"status": "success", "shift_id": shift_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/slots")
def get_slots(date: str, specialty: str | None = None, user_id: str = Depends(get_current_user)):
    try:
        from datetime import date as dt_date

        parsed = dt_date.fromisoformat(date)
        slots = db_service.get_available_slots(parsed, specialty=specialty)
        return {"status": "success", "slots": slots, "count": len(slots)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/appointments")
def create_appointment(payload: AppointmentCreateRequest, user_id: str = Depends(get_current_user)):
    try:
        appointment_id = db_service.create_appointment(
            {
                **payload.model_dump(),
                "slot_start": payload.slot_start.isoformat(),
                "slot_end": payload.slot_end.isoformat(),
            }
        )
        return {"status": "success", "appointment_id": appointment_id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointments")
def list_appointments(
    date: str | None = None,
    doctor_id: str | None = None,
    status: str | None = None,
    limit: int = 200,
    user_id: str = Depends(get_current_user),
):
    try:
        items = db_service.get_appointments(
            target_date=date,
            doctor_id=doctor_id,
            status=status,
            limit=limit,
        )
        return {"status": "success", "appointments": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: str, payload: AppointmentStatusUpdateRequest, user_id: str = Depends(get_current_user)):
    try:
        appointment = db_service.update_appointment_status(appointment_id, payload.status)
        return {"status": "success", "appointment": appointment}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/queue/events")
def create_queue_event(payload: QueueEventRequest, user_id: str = Depends(get_current_user)):
    try:
        event_id = db_service.log_queue_event(payload.model_dump())
        return {"status": "success", "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/live", response_model=QueueSummaryResponse)
def queue_live(user_id: str = Depends(get_current_user)):
    try:
        return QueueSummaryResponse(**db_service.get_live_queue_summary())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/optimizer/recommend-doctor", response_model=OptimizerResponse)
def recommend_doctor(specialty: str, user_id: str = Depends(get_current_user)):
    try:
        return OptimizerResponse(**db_service.recommend_doctor(specialty=specialty))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
