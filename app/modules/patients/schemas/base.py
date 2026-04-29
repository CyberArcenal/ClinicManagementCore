# app/schemas/patient.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema

class PatientBase(BaseSchema):
    user_id: Optional[int] = None
    date_of_birth: datetime
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies: Optional[str] = None   # JSON
    medical_history: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseSchema):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None

class PatientResponse(TimestampSchema, PatientBase):
    pass