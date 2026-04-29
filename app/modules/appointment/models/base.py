from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum, Text
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
from app.modules.appointment.enums.base import AppointmentStatus


class Appointment(BaseModel):
    __tablename__ = "appointments"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    appointment_datetime = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reason = Column(Text)
    notes = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"))  # receptionist or admin
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("DoctorProfile", back_populates="appointments")
    created_by = relationship("User", foreign_keys=[created_by_id])
    billing_item = relationship("BillingItem", back_populates="appointment", uselist=False)