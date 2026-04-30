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

    # Relationships with full module paths
    doctor_profile = relationship("app.modules.staff.models.doctor_profile.DoctorProfile", back_populates="user", uselist=False)
    nurse_profile = relationship("app.modules.staff.models.nurse_profile.NurseProfile", back_populates="user", uselist=False)
    receptionist_profile = relationship("app.modules.staff.models.receptionist_profile.ReceptionistProfile", back_populates="user", uselist=False)
    lab_tech_profile = relationship("app.modules.staff.models.labtech_profile.LabTechProfile", back_populates="user", uselist=False)
    pharmacist_profile = relationship("app.modules.staff.models.pharmacist_profile.PharmacistProfile", back_populates="user", uselist=False)
    patient_record = relationship("app.modules.patients.models.models.Patient", back_populates="user", uselist=False)
    created_appointments = relationship(
        "app.modules.appointment.models.base.Appointment",
        foreign_keys="app.modules.appointment.models.base.Appointment.created_by_id",
        back_populates="created_by"
    )
    received_inapp_notifications = relationship(
        "app.modules.notifications.models.inapp_notification.Notification",
        foreign_keys="app.modules.notifications.models.inapp_notification.Notification.user_id",
        back_populates="user",
    )
    sent_inapp_notifications = relationship(
        "app.modules.notifications.models.inapp_notification.Notification",
        foreign_keys="app.modules.notifications.models.inapp_notification.Notification.actor_id",
        back_populates="actor",
    )