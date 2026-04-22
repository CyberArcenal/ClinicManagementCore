from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class NotificationType(str, enum.Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    LAB_RESULT_READY = "lab_result_ready"
    PRESCRIPTION_READY = "prescription_ready"
    GENERAL = "general"

class Notification(BaseModel):
    __tablename__ = "notifications"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # staff
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_via = Column(String)  # email, sms, push
    sent_at = Column(DateTime)
    
    user = relationship("User", back_populates="notifications")
    patient = relationship("Patient", back_populates="notifications")