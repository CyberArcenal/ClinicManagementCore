from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class DoctorProfile(BaseModel):
    __tablename__ = "doctor_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    specialization = Column(String)
    license_number = Column(String, unique=True)
    years_of_experience = Column(Integer)

    user = relationship("app.modules.user.models.base.User", back_populates="doctor_profile")
    appointments = relationship("app.modules.appointment.models.base.Appointment", back_populates="doctor")
    prescriptions = relationship("app.modules.prescription.models.prescription.Prescription", back_populates="doctor")
    treatments = relationship("app.modules.treatment.models.models.Treatment", back_populates="doctor")
    ehr_entries = relationship("app.modules.ehr.models.base.EHR", back_populates="doctor")
    schedules = relationship("app.modules.schedule.models.schedule.DoctorSchedule", back_populates="doctor")