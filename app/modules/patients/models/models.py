from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class Patient(BaseModel):
    __tablename__ = "patients"
    
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(10))
    blood_type = Column(String(5))
    address = Column(Text)
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    allergies = Column(Text)  # Store as JSON string or separate table
    medical_history = Column(Text)  # JSON or text
    
    # Relationships
    user = relationship("User", back_populates="patient_record")
    appointments = relationship("Appointment", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    ehr_records = relationship("EHR", back_populates="patient")
    lab_results = relationship("LabResult", back_populates="patient")
    treatments = relationship("Treatment", back_populates="patient")
    invoices = relationship("Invoice", back_populates="patient")
    payments = relationship("Payment", back_populates="patient")
    insurance_details = relationship("InsuranceDetail", back_populates="patient")
    notifications = relationship("Notification", back_populates="patient")