from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
import enum

class ReceptionistProfile(BaseModel):
    __tablename__ = "receptionist_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="receptionist_profile")