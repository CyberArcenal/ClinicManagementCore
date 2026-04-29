# app/schemas/user.py
import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr
from app.common.schema.base import BaseSchema, TimestampSchema


class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    PATIENT = "patient"
    LAB_TECH = "lab_tech"
    PHARMACIST = "pharmacist"


# ----- User -----
class UserBase(BaseSchema):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.PATIENT
    is_active: bool = True
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str  # plain password, will be hashed in service


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None  # for password change


class UserResponse(TimestampSchema, UserBase):
    # Exclude hashed_password
    pass


# ----- DoctorProfile -----
class DoctorProfileBase(BaseSchema):
    user_id: int
    specialization: Optional[str] = None
    license_number: str
    years_of_experience: Optional[int] = None


class DoctorProfileCreate(DoctorProfileBase):
    pass


class DoctorProfileUpdate(BaseSchema):
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[int] = None


class DoctorProfileResponse(TimestampSchema, DoctorProfileBase):
    user: Optional[UserResponse] = None


# ----- NurseProfile -----
class NurseProfileBase(BaseSchema):
    user_id: int
    license_number: str


class NurseProfileCreate(NurseProfileBase):
    pass


class NurseProfileUpdate(BaseSchema):
    license_number: Optional[str] = None


class NurseProfileResponse(TimestampSchema, NurseProfileBase):
    user: Optional[UserResponse] = None


# ----- ReceptionistProfile -----
class ReceptionistProfileBase(BaseSchema):
    user_id: int


class ReceptionistProfileCreate(ReceptionistProfileBase):
    pass


class ReceptionistProfileUpdate(BaseSchema):
    pass


class ReceptionistProfileResponse(TimestampSchema, ReceptionistProfileBase):
    user: Optional[UserResponse] = None


# ----- LabTechProfile -----
class LabTechProfileBase(BaseSchema):
    user_id: int


class LabTechProfileCreate(LabTechProfileBase):
    pass


class LabTechProfileUpdate(BaseSchema):
    pass


class LabTechProfileResponse(TimestampSchema, LabTechProfileBase):
    user: Optional[UserResponse] = None


# ----- PharmacistProfile -----
class PharmacistProfileBase(BaseSchema):
    user_id: int


class PharmacistProfileCreate(PharmacistProfileBase):
    pass


class PharmacistProfileUpdate(BaseSchema):
    pass


class PharmacistProfileResponse(TimestampSchema, PharmacistProfileBase):
    user: Optional[UserResponse] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: str
    role: str
