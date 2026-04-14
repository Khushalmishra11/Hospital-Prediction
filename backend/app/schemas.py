from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    hour: int = Field(..., ge=0, le=23)
    doctor_count: int = Field(..., ge=1, le=50)
    scheduled_appointments: int = Field(..., ge=0, le=500)
    walk_in_patients: int = Field(..., ge=0, le=500)
    avg_consultation_minutes: float = Field(..., gt=0, le=120)
    is_holiday: bool = False
    rain_intensity: float = Field(0.0, ge=0.0, le=1.0)


class PredictionResponse(BaseModel):
    predicted_load_score: float
    expected_wait_minutes: float
    risk_level: str


class TrainResponse(BaseModel):
    status: str
    samples: int
    r2_score: float
    mae: float
