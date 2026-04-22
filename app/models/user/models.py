from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    PATIENT = "patient"
    LAB_TECH = "lab_tech"
    PHARMACIST = "pharmacist"

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
    receptionist_profile = relationship("ReceptionistProfile", back_populates="user", uselist=False)
    lab_tech_profile = relationship("LabTechProfile", back_populates="user", uselist=False)
    pharmacist_profile = relationship("PharmacistProfile", back_populates="user", uselist=False)
    patient_record = relationship("Patient", back_populates="user", uselist=False)
    created_appointments = relationship("Appointment", foreign_keys="Appointment.created_by_id")
    notifications = relationship("Notification", back_populates="user")

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

class NurseProfile(BaseModel):
    __tablename__ = "nurse_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    license_number = Column(String, unique=True)
    
    user = relationship("User", back_populates="nurse_profile")
    assigned_treatments = relationship("Treatment", back_populates="nurse")

class ReceptionistProfile(BaseModel):
    __tablename__ = "receptionist_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="receptionist_profile")

class LabTechProfile(BaseModel):
    __tablename__ = "lab_tech_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="lab_tech_profile")
    lab_results = relationship("LabResult", back_populates="lab_tech")

class PharmacistProfile(BaseModel):
    __tablename__ = "pharmacist_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="pharmacist_profile")