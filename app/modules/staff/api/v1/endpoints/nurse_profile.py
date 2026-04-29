# app/modules/staff/api/v1/endpoints/nurse_profile.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession


from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.staff import DuplicateLicenseError, NurseNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.staff.services.nurse_profile import NurseProfileService
from app.modules.user.models import User
from app.modules.user.schemas.base import NurseProfileCreate, NurseProfileResponse, NurseProfileUpdate

router = APIRouter()


@router.post("/", response_model=NurseProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_nurse_profile(
    data: NurseProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NurseProfileService(db)
    try:
        nurse = await service.create_nurse(data)
        return nurse
    except (UserNotFoundError, DuplicateLicenseError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedResponse[NurseProfileResponse])
async def list_nurse_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NurseProfileService(db)
    paginated = await service.get_nurses(page=page, page_size=page_size)
    return paginated


@router.get("/{nurse_id}", response_model=NurseProfileResponse)
async def get_nurse_profile(
    nurse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NurseProfileService(db)
    nurse = await service.get_nurse(nurse_id)
    if not nurse:
        raise HTTPException(status_code=404, detail="Nurse not found")
    return nurse


@router.put("/{nurse_id}", response_model=NurseProfileResponse)
async def update_nurse_profile(
    nurse_id: int,
    data: NurseProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NurseProfileService(db)
    try:
        nurse = await service.update_nurse(nurse_id, data)
        if not nurse:
            raise HTTPException(status_code=404, detail="Nurse not found")
        return nurse
    except (NurseNotFoundError, DuplicateLicenseError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{nurse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nurse_profile(
    nurse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NurseProfileService(db)
    deleted = await service.delete_nurse(nurse_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Nurse not found")
    return None