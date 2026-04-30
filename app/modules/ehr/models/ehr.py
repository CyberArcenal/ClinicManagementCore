from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, String
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

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
    
    # Relationships with full module paths
    patient = relationship("app.modules.patients.models.models.Patient", back_populates="ehr_records")
    doctor = relationship("app.modules.staff.models.doctor_profile.DoctorProfile", back_populates="ehr_entries")
    prescriptions = relationship("app.modules.prescription.models.models.Prescription", back_populates="ehr_visit")
    lab_requests = relationship("app.modules.lab.models.models.LabResult", back_populates="ehr_visit")
    treatments = relationship("app.modules.treatment.models.models.Treatment", back_populates="ehr_visit")