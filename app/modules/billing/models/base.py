from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
from app.modules.billing.enums.base import InvoiceStatus, PaymentMethod


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
    
    patient = relationship("Patient", back_populates="invoices")
    items = relationship("BillingItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class BillingItem(BaseModel):
    __tablename__ = "billing_items"
    
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10,2), nullable=False)
    total = Column(Numeric(10,2), nullable=False)
    # Optional links to other modules
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    treatment_id = Column(Integer, ForeignKey("treatments.id"), nullable=True)
    
    invoice = relationship("Invoice", back_populates="items")
    appointment = relationship("Appointment", back_populates="billing_item")
    treatment = relationship("Treatment", back_populates="billing_item")

class Payment(BaseModel):
    __tablename__ = "payments"
    
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    reference_number = Column(String)
    notes = Column(Text)
    
    invoice = relationship("Invoice", back_populates="payments")
    patient = relationship("Patient", back_populates="payments")