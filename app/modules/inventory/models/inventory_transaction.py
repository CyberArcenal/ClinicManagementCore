from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class InventoryTransaction(BaseModel):
    __tablename__ = "inventory_transactions"
    
    item_id = Column(Integer, ForeignKey("inventory_items.id"))
    transaction_type = Column(String)  # purchase, sale, adjustment, return
    quantity = Column(Integer)
    transaction_date = Column(DateTime, nullable=False)
    reference_document = Column(String)
    performed_by_id = Column(Integer, ForeignKey("users.id"))
    
    item = relationship("app.modules.inventory.models.inventory_item.InventoryItem")