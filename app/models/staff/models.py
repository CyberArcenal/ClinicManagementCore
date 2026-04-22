from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class WeekDay(str, enum.Enum):
    MON = "monday"
    TUE = "tuesday"
    WED = "wednesday"
    THU = "thursday"
    FRI = "friday"
    SAT = "saturday"
    SUN = "sunday"

class DoctorSchedule(BaseModel):
    __tablename__ = "doctor_schedules"
    
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    day_of_week = Column(Enum(WeekDay))
    start_time = Column(String(5))  # "09:00"
    end_time = Column(String(5))    # "17:00"
    is_available = Column(DateTime, default=True)
    
    doctor = relationship("DoctorProfile", back_populates="schedules")

# Add to DoctorProfile model: schedules = relationship("DoctorSchedule", back_populates="doctor")