# app/schemas/appointment.py
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema
from app.modules.appointment.enums.base import AppointmentStatus  # your existing enum

class AppointmentBase(BaseSchema):
    patient_id: int
    doctor_id: int
    appointment_datetime: datetime
    duration_minutes: int = 30
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_by_id: Optional[int] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseSchema):
    appointment_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

class AppointmentResponse(TimestampSchema, AppointmentBase):
    pass