# app/modules/staff/api/v1/endpoints/doctor_profile.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import User


router = APIRouter()


@router.post("/", response_model=DoctorProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor_profile(
    data: DoctorProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = DoctorProfileService(db)
    try:
        doctor = await service.create_doctor(data)
        return doctor
    except (UserNotFoundError, DuplicateLicenseError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DoctorProfileResponse])
async def list_doctor_profiles(
    specialization: Optional[str] = Query(None),
    min_experience: Optional[int] = Query(None),
    name: Optional[str] = Query(None, description="Search by user full name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if specialization:
        filters["specialization"] = specialization
    if min_experience:
        filters["min_experience"] = min_experience
    if name:
        filters["user__full_name"] = name
    service = DoctorProfileService(db)
    doctors = await service.get_doctors(filters=filters, skip=skip, limit=limit)
    return doctors


@router.get("/{doctor_id}", response_model=DoctorProfileResponse)
async def get_doctor_profile(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DoctorProfileService(db)
    doctor = await service.get_doctor(doctor_id, load_user=True)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.get("/license/{license_number}", response_model=DoctorProfileResponse)
async def get_doctor_by_license(
    license_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DoctorProfileService(db)
    doctor = await service.get_doctor_by_license(license_number)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.put("/{doctor_id}", response_model=DoctorProfileResponse)
async def update_doctor_profile(
    doctor_id: int,
    data: DoctorProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = DoctorProfileService(db)
    try:
        doctor = await service.update_doctor(doctor_id, data)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return doctor
    except (DoctorNotFoundError, DuplicateLicenseError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor_profile(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = DoctorProfileService(db)
    deleted = await service.delete_doctor(doctor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return None