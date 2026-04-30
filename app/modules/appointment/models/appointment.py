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
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships with full module paths
    patient = relationship("app.modules.patients.models.models.Patient", back_populates="appointments")
    doctor = relationship("app.modules.staff.models.doctor_profile.DoctorProfile", back_populates="appointments")
    created_by = relationship("app.modules.user.models.base.User", foreign_keys=[created_by_id])
    billing_item = relationship("app.modules.billing.models.billing_item.BillingItem", back_populates="appointment", uselist=False)