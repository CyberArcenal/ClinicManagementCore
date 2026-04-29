# app/schemas/treatment.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.common.schema.base import BaseSchema, TimestampSchema
class TreatmentBase(BaseSchema):
    patient_id: int
    doctor_id: int
    ehr_id: Optional[int] = None
    nurse_id: Optional[int] = None
    treatment_type: Optional[str] = None
    procedure_name: Optional[str] = None
    performed_date: Optional[datetime] = None
    notes: Optional[str] = None

class TreatmentCreate(TreatmentBase):
    pass

class TreatmentUpdate(BaseSchema):
    nurse_id: Optional[int] = None
    treatment_type: Optional[str] = None
    procedure_name: Optional[str] = None
    performed_date: Optional[datetime] = None
    notes: Optional[str] = None

class TreatmentResponse(TimestampSchema, TreatmentBase):
    pass