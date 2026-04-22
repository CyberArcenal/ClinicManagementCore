from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.models.base import BaseModel

class ReportLog(BaseModel):
    __tablename__ = "report_logs"
    
    report_name = Column(String, nullable=False)
    generated_by_id = Column(Integer, ForeignKey("users.id"))
    parameters = Column(Text)  # JSON of filters
    file_path = Column(String)  # if stored as PDF/CSV
    generated_at = Column(DateTime, nullable=False)