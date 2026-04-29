# app/schemas/insurance.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.common.schema.base import BaseSchema, TimestampSchema

# InsuranceDetail
class InsuranceDetailBase(BaseSchema):
    patient_id: int
    provider_name: str
    policy_number: str
    group_number: Optional[str] = None
    coverage_start: Optional[date] = None
    coverage_end: Optional[date] = None
    copay_percent: Decimal = 0

class InsuranceDetailCreate(InsuranceDetailBase):
    pass

class InsuranceDetailUpdate(BaseSchema):
    provider_name: Optional[str] = None
    policy_number: Optional[str] = None
    group_number: Optional[str] = None
    coverage_start: Optional[date] = None
    coverage_end: Optional[date] = None
    copay_percent: Optional[Decimal] = None

class InsuranceDetailResponse(TimestampSchema, InsuranceDetailBase):
    pass

# InsuranceClaim
class InsuranceClaimBase(BaseSchema):
    insurance_detail_id: int
    invoice_id: int
    claim_number: Optional[str] = None
    submitted_date: Optional[date] = None
    approved_amount: Optional[Decimal] = None
    status: Optional[str] = None   # "submitted", "approved", etc.
    notes: Optional[str] = None

class InsuranceClaimCreate(InsuranceClaimBase):
    pass

class InsuranceClaimUpdate(BaseSchema):
    claim_number: Optional[str] = None
    submitted_date: Optional[date] = None
    approved_amount: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class InsuranceClaimResponse(TimestampSchema, InsuranceClaimBase):
    pass