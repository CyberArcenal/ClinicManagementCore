# app/schemas/patient_portal.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema

class PatientPortalAccessBase(BaseSchema):
    patient_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_time: Optional[datetime] = None
    logout_time: Optional[datetime] = None

class PatientPortalAccessCreate(PatientPortalAccessBase):
    pass

class PatientPortalAccessUpdate(BaseSchema):
    logout_time: Optional[datetime] = None

class PatientPortalAccessResponse(TimestampSchema, PatientPortalAccessBase):
    pass