from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
import enum

class DoctorProfile(BaseModel):
    __tablename__ = "doctor_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    specialization = Column(String)
    license_number = Column(String, unique=True)
    years_of_experience = Column(Integer)

    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")
    prescriptions = relationship("Prescription", back_populates="doctor")
    treatments = relationship("Treatment", back_populates="doctor")
    ehr_entries = relationship("EHR", back_populates="doctor")