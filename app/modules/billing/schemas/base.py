# app/schemas/billing.py
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel
from app.common.schema.base import BaseSchema, TimestampSchema
from app.common.schema.base import BaseSchema
from app.modules.billing.enums.base import InvoiceStatus, PaymentMethod

# ----- Invoice -----
class InvoiceBase(BaseSchema):
    patient_id: int
    invoice_number: str
    issue_date: datetime
    due_date: Optional[datetime] = None
    subtotal: Decimal
    tax: Decimal = 0
    total: Decimal
    status: InvoiceStatus = InvoiceStatus.DRAFT
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseSchema):
    due_date: Optional[datetime] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None

class InvoiceResponse(TimestampSchema, InvoiceBase):
    items: List["BillingItemResponse"] = []
    payments: List["PaymentResponse"] = []

# ----- BillingItem -----
class BillingItemBase(BaseSchema):
    invoice_id: int
    description: str
    quantity: int = 1
    unit_price: Decimal
    total: Decimal
    appointment_id: Optional[int] = None
    treatment_id: Optional[int] = None

class BillingItemCreate(BillingItemBase):
    pass

class BillingItemUpdate(BaseSchema):
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total: Optional[Decimal] = None

class BillingItemResponse(TimestampSchema, BillingItemBase):
    pass

# ----- Payment -----
class PaymentBase(BaseSchema):
    invoice_id: int
    amount: Decimal
    payment_date: datetime
    method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseSchema):
    amount: Optional[Decimal] = None
    method: Optional[PaymentMethod] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(TimestampSchema, PaymentBase):
    pass