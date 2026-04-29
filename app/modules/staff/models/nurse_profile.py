from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
import enum

class NurseProfile(BaseModel):
    __tablename__ = "nurse_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    license_number = Column(String, unique=True)

    user = relationship("User", back_populates="nurse_profile")
    assigned_treatments = relationship("Treatment", back_populates="nurse")