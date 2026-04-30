from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, Boolean
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class Prescription(BaseModel):
    __tablename__ = "prescriptions"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    ehr_id = Column(Integer, ForeignKey("ehr.id"))
    issue_date = Column(Date, nullable=False)
    notes = Column(Text)
    is_dispensed = Column(Boolean, default=False)
    
    patient = relationship("app.modules.patients.models.models.Patient", back_populates="prescriptions")
    doctor = relationship("app.modules.staff.models.doctor_profile.DoctorProfile", back_populates="prescriptions")
    ehr_visit = relationship("app.modules.ehr.models.base.EHR", back_populates="prescriptions")
    items = relationship("app.modules.prescription.models.prescription_item.PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")