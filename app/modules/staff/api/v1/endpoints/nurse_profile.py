# app/modules/staff/api/v1/endpoints/nurse_profile.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.user.models import User

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


@router.get("/", response_model=List[NurseProfileResponse])
async def list_nurse_profiles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NurseProfileService(db)
    nurses = await service.get_nurses(skip=skip, limit=limit)
    return nurses


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