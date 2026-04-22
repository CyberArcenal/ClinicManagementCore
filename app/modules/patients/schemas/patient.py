from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Base schema with common attributes
class PatientBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str

# Schema for creating a new patient (input validation)
class PatientCreate(PatientBase):
    date_of_birth: datetime

# Schema for returning patient data (output serialization)
class PatientResponse(PatientBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True