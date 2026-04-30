from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
from app.modules.billing.enums.base import PaymentMethod

class Payment(BaseModel):
    __tablename__ = "payments"
    
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    reference_number = Column(String)
    notes = Column(Text)
    
    invoice = relationship("app.modules.billing.models.invoice.Invoice", back_populates="payments")
    patient = relationship("app.modules.patients.models.models.Patient", back_populates="payments")