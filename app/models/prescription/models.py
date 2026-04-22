from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Prescription(BaseModel):
    __tablename__ = "prescriptions"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    ehr_id = Column(Integer, ForeignKey("ehr.id"))
    issue_date = Column(Date, nullable=False)
    notes = Column(Text)
    is_dispensed = Column(Boolean, default=False)
    
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("DoctorProfile", back_populates="prescriptions")
    ehr_visit = relationship("EHR", back_populates="prescriptions")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

class PrescriptionItem(BaseModel):
    __tablename__ = "prescription_items"
    
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    drug_name = Column(String, nullable=False)
    dosage = Column(String)
    frequency = Column(String)
    duration_days = Column(Integer)
    instructions = Column(Text)
    
    prescription = relationship("Prescription", back_populates="items")