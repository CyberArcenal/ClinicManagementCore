from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
from app.modules.billing.enums.base import InvoiceStatus

class Invoice(BaseModel):
    __tablename__ = "invoices"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    invoice_number = Column(String, unique=True, nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    subtotal = Column(Numeric(10,2), nullable=False)
    tax = Column(Numeric(10,2), default=0)
    total = Column(Numeric(10,2), nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    notes = Column(Text)
    
    patient = relationship("app.modules.patients.models.models.Patient", back_populates="invoices")
    items = relationship("app.modules.billing.models.billing_item.BillingItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("app.modules.billing.models.payment.Payment", back_populates="invoice")