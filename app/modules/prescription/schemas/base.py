# app/schemas/prescription.py
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel
from app.common.schema.base import BaseSchema, TimestampSchema
# PrescriptionItem
class PrescriptionItemBase(BaseSchema):
    prescription_id: int
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None

class PrescriptionItemCreate(PrescriptionItemBase):
    pass

class PrescriptionItemUpdate(BaseSchema):
    drug_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None

class PrescriptionItemResponse(TimestampSchema, PrescriptionItemBase):
    pass

# Prescription
class PrescriptionBase(BaseSchema):
    patient_id: int
    doctor_id: int
    ehr_id: Optional[int] = None
    issue_date: date
    notes: Optional[str] = None
    is_dispensed: bool = False

class PrescriptionCreate(PrescriptionBase):
    items: List[PrescriptionItemCreate] = []

class PrescriptionUpdate(BaseSchema):
    notes: Optional[str] = None
    is_dispensed: Optional[bool] = None

class PrescriptionResponse(TimestampSchema, PrescriptionBase):
    items: List[PrescriptionItemResponse] = []