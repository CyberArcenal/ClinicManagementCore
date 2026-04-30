from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text
from app.common.models.base import BaseModel

class InventoryItem(BaseModel):
    __tablename__ = "inventory_items"
    
    name = Column(String, nullable=False)
    category = Column(String)
    sku = Column(String, unique=True)
    quantity_on_hand = Column(Integer, default=0)
    unit = Column(String)
    reorder_level = Column(Integer)
    unit_cost = Column(Numeric(10,2))
    selling_price = Column(Numeric(10,2))
    expiry_date = Column(DateTime)
    location = Column(String)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)