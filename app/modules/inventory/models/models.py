from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, DateTime, Boolean, Text
from app.common.models.base import BaseModel

class InventoryItem(BaseModel):
    __tablename__ = "inventory_items"
    
    name = Column(String, nullable=False)
    category = Column(String)  # medicine, equipment, supply
    sku = Column(String, unique=True)
    quantity_on_hand = Column(Integer, default=0)
    unit = Column(String)  # pieces, bottles, boxes
    reorder_level = Column(Integer)
    unit_cost = Column(Numeric(10,2))
    selling_price = Column(Numeric(10,2))
    expiry_date = Column(DateTime)
    location = Column(String)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

class InventoryTransaction(BaseModel):
    __tablename__ = "inventory_transactions"
    
    item_id = Column(Integer, ForeignKey("inventory_items.id"))
    transaction_type = Column(String)  # purchase, sale, adjustment, return
    quantity = Column(Integer)
    transaction_date = Column(DateTime, nullable=False)
    reference_document = Column(String)  # invoice number, PO number
    performed_by_id = Column(Integer, ForeignKey("users.id"))