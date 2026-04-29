# app/schemas/report.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.common.schema.base import BaseSchema, TimestampSchema
class ReportLogBase(BaseSchema):
    report_name: str
    generated_by_id: int
    parameters: Optional[str] = None
    file_path: Optional[str] = None
    generated_at: datetime

class ReportLogCreate(ReportLogBase):
    pass

class ReportLogUpdate(BaseSchema):
    file_path: Optional[str] = None

class ReportLogResponse(TimestampSchema, ReportLogBase):
    pass