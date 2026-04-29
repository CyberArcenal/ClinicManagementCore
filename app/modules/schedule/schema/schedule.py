# app/schemas/schedule.py
from typing import Optional
from enum import Enum
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema

class WeekDay(str, Enum):
    MON = "monday"
    TUE = "tuesday"
    WED = "wednesday"
    THU = "thursday"
    FRI = "friday"
    SAT = "saturday"
    SUN = "sunday"

class DoctorScheduleBase(BaseSchema):
    doctor_id: int
    day_of_week: WeekDay
    start_time: str   # "09:00"
    end_time: str     # "17:00"
    is_available: bool = True

class DoctorScheduleCreate(DoctorScheduleBase):
    pass

class DoctorScheduleUpdate(BaseSchema):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_available: Optional[bool] = None

class DoctorScheduleResponse(TimestampSchema, DoctorScheduleBase):
    pass