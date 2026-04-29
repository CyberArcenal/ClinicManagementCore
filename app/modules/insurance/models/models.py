from sqlalchemy import Column, Integer, ForeignKey, String, Date, Numeric
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class InsuranceDetail(BaseModel):
    __tablename__ = "insurance_details"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_name = Column(String, nullable=False)
    policy_number = Column(String, nullable=False)
    group_number = Column(String)
    coverage_start = Column(Date)
    coverage_end = Column(Date)
    copay_percent = Column(Numeric(5,2), default=0)
    
    patient = relationship("Patient", back_populates="insurance_details")
    claims = relationship("InsuranceClaim", back_populates="insurance_detail")

class InsuranceClaim(BaseModel):
    __tablename__ = "insurance_claims"
    
    insurance_detail_id = Column(Integer, ForeignKey("insurance_details.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    claim_number = Column(String, unique=True)
    submitted_date = Column(Date)
    approved_amount = Column(Numeric(10,2))
    status = Column(String)  # submitted, approved, denied, paid
    notes = Column(String)
    
    insurance_detail = relationship("InsuranceDetail", back_populates="claims")
    invoice = relationship("Invoice")