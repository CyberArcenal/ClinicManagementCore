# app/schemas/lab.py
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema

class LabStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class LabResultBase(BaseSchema):
    patient_id: int
    ehr_id: Optional[int] = None
    test_name: str
    requested_by_id: int
    performed_by_id: Optional[int] = None
    requested_date: datetime
    completed_date: Optional[datetime] = None
    status: LabStatus = LabStatus.PENDING
    result_data: Optional[str] = None
    normal_range: Optional[str] = None
    remarks: Optional[str] = None

class LabResultCreate(LabResultBase):
    pass

class LabResultUpdate(BaseSchema):
    performed_by_id: Optional[int] = None
    completed_date: Optional[datetime] = None
    status: Optional[LabStatus] = None
    result_data: Optional[str] = None
    normal_range: Optional[str] = None
    remarks: Optional[str] = None

class LabResultResponse(TimestampSchema, LabResultBase):
    pass