from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
import enum

class LabTechProfile(BaseModel):
    __tablename__ = "lab_tech_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="lab_tech_profile")
    lab_results = relationship("LabResult", back_populates="lab_tech")