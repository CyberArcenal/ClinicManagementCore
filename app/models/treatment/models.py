from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Treatment(BaseModel):
    __tablename__ = "treatments"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    ehr_id = Column(Integer, ForeignKey("ehr.id"))
    nurse_id = Column(Integer, ForeignKey("nurse_profiles.id"))
    treatment_type = Column(String)  # e.g., "surgery", "therapy", "injection"
    procedure_name = Column(String)
    performed_date = Column(DateTime)
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="treatments")
    doctor = relationship("DoctorProfile", back_populates="treatments")
    ehr_visit = relationship("EHR", back_populates="treatments")
    nurse = relationship("NurseProfile", back_populates="assigned_treatments")
    billing_item = relationship("BillingItem", back_populates="treatment", uselist=False)