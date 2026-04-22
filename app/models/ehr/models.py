from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class EHR(BaseModel):
    __tablename__ = "ehr"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    visit_date = Column(DateTime, nullable=False)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    clinical_notes = Column(Text)
    vital_signs = Column(Text)  # JSON: BP, HR, temp, etc.
    symptoms = Column(Text)
    
    patient = relationship("Patient", back_populates="ehr_records")
    doctor = relationship("DoctorProfile", back_populates="ehr_entries")
    prescriptions = relationship("Prescription", back_populates="ehr_visit")
    lab_requests = relationship("LabResult", back_populates="ehr_visit")
    treatments = relationship("Treatment", back_populates="ehr_visit")