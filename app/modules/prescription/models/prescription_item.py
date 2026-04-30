from sqlalchemy import Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class PrescriptionItem(BaseModel):
    __tablename__ = "prescription_items"
    
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    drug_name = Column(String, nullable=False)
    dosage = Column(String)
    frequency = Column(String)
    duration_days = Column(Integer)
    instructions = Column(Text)
    
    prescription = relationship("app.modules.prescription.models.prescription.Prescription", back_populates="items")