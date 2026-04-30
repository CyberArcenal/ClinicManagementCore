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
    allergies = Column(Text)
    medical_history = Column(Text)
    
    user = relationship("app.modules.user.models.base.User", back_populates="patient_record")
    appointments = relationship("app.modules.appointment.models.base.Appointment", back_populates="patient")
    prescriptions = relationship("app.modules.prescription.models.prescription.Prescription", back_populates="patient")
    ehr_records = relationship("app.modules.ehr.models.base.EHR", back_populates="patient")
    lab_results = relationship("app.modules.lab.models.models.LabResult", back_populates="patient")
    treatments = relationship("app.modules.treatment.models.models.Treatment", back_populates="patient")
    invoices = relationship("app.modules.billing.models.invoice.Invoice", back_populates="patient")
    payments = relationship("app.modules.billing.models.payment.Payment", back_populates="patient")
    insurance_details = relationship("app.modules.insurance.models.insurance_detail.InsuranceDetail", back_populates="patient")