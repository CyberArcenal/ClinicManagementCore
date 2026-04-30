from sqlalchemy import Column, Integer, ForeignKey, String, Date, Numeric
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class InsuranceClaim(BaseModel):
    __tablename__ = "insurance_claims"
    
    insurance_detail_id = Column(Integer, ForeignKey("insurance_details.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    claim_number = Column(String, unique=True)
    submitted_date = Column(Date)
    approved_amount = Column(Numeric(10,2))
    status = Column(String)  # submitted, approved, denied, paid
    notes = Column(String)
    
    insurance_detail = relationship("app.modules.insurance.models.insurance_detail.InsuranceDetail", back_populates="claims")
    invoice = relationship("app.modules.billing.models.invoice.Invoice")