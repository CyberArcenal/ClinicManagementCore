from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel

class LabTechProfile(BaseModel):
    __tablename__ = "lab_tech_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    user = relationship("app.modules.user.models.base.User", back_populates="lab_tech_profile")
    lab_results = relationship("app.modules.lab.models.models.LabResult", back_populates="performed_by")