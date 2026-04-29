# app/modules/staff/api/v1/endpoints/labtech_profile.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.staff.services.doctor_profile import DoctorProfileService
from app.modules.staff.services.labtech_profile import LabTechProfileService
from app.modules.user.models import User
from app.modules.user.schemas.base import DoctorProfileCreate, DoctorProfileResponse, DoctorProfileUpdate, LabTechProfileCreate, LabTechProfileResponse, LabTechProfileUpdate


router = APIRouter()


@router.post("/", response_model=LabTechProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_labtech_profile(
    data: LabTechProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = LabTechProfileService(db)
    try:
        tech = await service.create_lab_tech(data)
        return tech
    except UserNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedResponse[LabTechProfileResponse])
async def list_labtech_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LabTechProfileService(db)
    paginated = await service.get_all_lab_techs(page=page, page_size=page_size)
    return paginated


@router.get("/{tech_id}", response_model=LabTechProfileResponse)
async def get_labtech_profile(
    tech_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LabTechProfileService(db)
    tech = await service.get_lab_tech(tech_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Lab technician not found")
    return tech


@router.put("/{tech_id}", response_model=LabTechProfileResponse)
async def update_labtech_profile(
    tech_id: int,
    data: LabTechProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = LabTechProfileService(db)
    tech = await service.update_lab_tech(tech_id, data)
    if not tech:
        raise HTTPException(status_code=404, detail="Lab technician not found")
    return tech


@router.delete("/{tech_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_labtech_profile(
    tech_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = LabTechProfileService(db)
    deleted = await service.delete_lab_tech(tech_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lab technician not found")
    return None