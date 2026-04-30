from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class NurseProfile(BaseModel):
    __tablename__ = "nurse_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    license_number = Column(String, unique=True)

    user = relationship("app.modules.user.models.base.User", back_populates="nurse_profile")
    assigned_treatments = relationship("app.modules.treatment.models.models.Treatment", back_populates="nurse")