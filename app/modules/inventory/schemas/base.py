# app/schemas/inventory.py
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema

# InventoryItem
class InventoryItemBase(BaseSchema):
    name: str
    category: Optional[str] = None
    sku: Optional[str] = None
    quantity_on_hand: int = 0
    unit: Optional[str] = None
    reorder_level: Optional[int] = None
    unit_cost: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    expiry_date: Optional[datetime] = None
    location: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseSchema):
    name: Optional[str] = None
    quantity_on_hand: Optional[int] = None
    reorder_level: Optional[int] = None
    unit_cost: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class InventoryItemResponse(TimestampSchema, InventoryItemBase):
    pass

# InventoryTransaction
class InventoryTransactionBase(BaseSchema):
    item_id: int
    transaction_type: str   # purchase, sale, adjustment, return
    quantity: int
    transaction_date: datetime
    reference_document: Optional[str] = None
    performed_by_id: int

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransactionUpdate(BaseSchema):
    transaction_type: Optional[str] = None
    quantity: Optional[int] = None
    reference_document: Optional[str] = None

class InventoryTransactionResponse(TimestampSchema, InventoryTransactionBase):
    pass