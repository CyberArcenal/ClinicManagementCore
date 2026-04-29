# app/schemas/ehr.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema

class EHRBase(BaseSchema):
    patient_id: int
    doctor_id: int
    visit_date: datetime
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    clinical_notes: Optional[str] = None
    vital_signs: Optional[str] = None   # JSON string, or use dict if parsed
    symptoms: Optional[str] = None

class EHRCreate(EHRBase):
    pass

class EHRUpdate(BaseSchema):
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    clinical_notes: Optional[str] = None
    vital_signs: Optional[str] = None
    symptoms: Optional[str] = None

class EHRResponse(TimestampSchema, EHRBase):
    pass