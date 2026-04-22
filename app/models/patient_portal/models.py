from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from app.models.base import BaseModel

class PatientPortalAccess(BaseModel):
    __tablename__ = "patient_portal_access"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    login_time = Column(DateTime)
    logout_time = Column(DateTime)