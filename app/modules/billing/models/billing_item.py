from sqlalchemy import Column, Integer, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class BillingItem(BaseModel):
    __tablename__ = "billing_items"
    
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10,2), nullable=False)
    total = Column(Numeric(10,2), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    treatment_id = Column(Integer, ForeignKey("treatments.id"), nullable=True)
    
    invoice = relationship("app.modules.billing.models.invoice.Invoice", back_populates="items")
    appointment = relationship("app.modules.appointment.models.base.Appointment", back_populates="billing_item")
    treatment = relationship("app.modules.treatment.models.models.Treatment", back_populates="billing_item")