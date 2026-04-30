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
    
    patient = relationship("app.modules.patients.models.models.Patient", back_populates="insurance_details")
    claims = relationship("app.modules.insurance.models.insurance_claim.InsuranceClaim", back_populates="insurance_detail")