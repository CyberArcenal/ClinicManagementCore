from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
from app.modules.user.enums.base import UserRole



class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    is_active = Column(Boolean, default=True)
    phone_number = Column(String)

    # Relationships
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)
    nurse_profile = relationship("NurseProfile", back_populates="user", uselist=False)
    receptionist_profile = relationship(
        "ReceptionistProfile", back_populates="user", uselist=False
    )
    lab_tech_profile = relationship(
        "LabTechProfile", back_populates="user", uselist=False
    )
    pharmacist_profile = relationship(
        "PharmacistProfile", back_populates="user", uselist=False
    )
    patient_record = relationship("Patient", back_populates="user", uselist=False)
    created_appointments = relationship(
        "Appointment", foreign_keys="Appointment.created_by_id"
    )
    received_inapp_notifications = relationship(
        "InAppNotification",
        foreign_keys="[InAppNotification.user_id]",
        back_populates="user",
    )
    sent_inapp_notifications = relationship(
        "InAppNotification",
        foreign_keys="[InAppNotification.actor_id]",
        back_populates="actor",
    )














