from datetime import date, datetime
from typing import Optional

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


class DoctorCreateRequest(BaseModel):
    doctor_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    specialty: str = Field(..., min_length=1)
    avg_consultation_minutes: float = Field(15, gt=0, le=120)
    shift_start: str = Field(..., description="HH:MM")
    shift_end: str = Field(..., description="HH:MM")


class DoctorStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(available|busy|break|offline)$")


class DoctorAvailabilityItem(BaseModel):
    doctor_id: str
    name: str
    specialty: str
    status: str
    current_queue_count: int
    avg_consultation_minutes: float
    shift_start: str
    shift_end: str
    updated_at: Optional[str] = None


class ShiftUpsertRequest(BaseModel):
    doctor_id: str = Field(..., min_length=1)
    date: date
    start_time: str = Field(..., description="HH:MM")
    end_time: str = Field(..., description="HH:MM")
    slot_duration_minutes: int = Field(15, ge=5, le=60)
    is_available: bool = True


class SlotItem(BaseModel):
    doctor_id: str
    doctor_name: str
    specialty: str
    slot_start: str
    slot_end: str


class AppointmentCreateRequest(BaseModel):
    patient_id: str = Field(..., min_length=1)
    doctor_id: str = Field(..., min_length=1)
    slot_start: datetime
    slot_end: datetime
    booking_channel: str = Field("web", min_length=1)


class AppointmentStatusUpdateRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(booked|checked_in|in_consult|completed|cancelled|no_show)$",
    )


class QueueEventRequest(BaseModel):
    appointment_id: str = Field(..., min_length=1)
    doctor_id: str = Field(..., min_length=1)
    event_type: str = Field(
        ...,
        pattern="^(check_in|called|consult_start|consult_end|no_show|cancel)$",
    )
    source: str = Field("system", min_length=1)


class QueueSummaryResponse(BaseModel):
    total_waiting: int
    in_consult: int
    completed_today: int
    no_show_today: int
    avg_wait_minutes_checked_in: float
    by_doctor: dict[str, int]


class OptimizerResponse(BaseModel):
    doctor_id: str
    name: str
    specialty: str
    status: str
    weighted_load_score: float
