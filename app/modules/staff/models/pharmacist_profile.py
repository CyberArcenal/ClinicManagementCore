from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class PharmacistProfile(BaseModel):
    __tablename__ = "pharmacist_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    user = relationship("app.modules.user.models.base.User", back_populates="pharmacist_profile")