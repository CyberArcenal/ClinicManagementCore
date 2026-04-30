from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.staff.services.doctor_profile import DoctorProfileService
from app.modules.user.models import User
from app.modules.user.schemas.base import (
    DoctorProfileCreate,
    DoctorProfileResponse,
    DoctorProfileUpdate,
)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_doctor_profile(
    data: DoctorProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[DoctorProfileResponse]:
    service = DoctorProfileService(db)
    try:
        doctor = await service.create_doctor(data)
        return success_response(data=doctor, message="Doctor profile created")
    except (UserNotFoundError, DuplicateLicenseError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_doctor_profiles(
    specialization: Optional[str] = Query(None),
    min_experience: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[DoctorProfileResponse]]:
    filters = {}
    if specialization:
        filters["specialization"] = specialization
    if min_experience:
        filters["min_experience"] = min_experience
    if name:
        filters["user__full_name"] = name
    service = DoctorProfileService(db)
    paginated = await service.get_doctors(
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return success_response(data=paginated, message="Doctor profiles retrieved")


@router.get("/{doctor_id}")
async def get_doctor_profile(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[DoctorProfileResponse]:
    service = DoctorProfileService(db)
    doctor = await service.get_doctor(doctor_id, load_user=True)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return success_response(data=doctor, message="Doctor profile retrieved")


@router.get("/license/{license_number}")
async def get_doctor_by_license(
    license_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[DoctorProfileResponse]:
    service = DoctorProfileService(db)
    doctor = await service.get_doctor_by_license(license_number)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return success_response(data=doctor, message="Doctor profile retrieved by license")


@router.put("/{doctor_id}")
async def update_doctor_profile(
    doctor_id: int,
    data: DoctorProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[DoctorProfileResponse]:
    service = DoctorProfileService(db)
    try:
        doctor = await service.update_doctor(doctor_id, data)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return success_response(data=doctor, message="Doctor profile updated")
    except (DoctorNotFoundError, DuplicateLicenseError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor_profile(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = DoctorProfileService(db)
    deleted = await service.delete_doctor(doctor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return None