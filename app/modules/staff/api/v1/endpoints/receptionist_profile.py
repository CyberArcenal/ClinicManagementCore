# app/modules/staff/api/v1/endpoints/receptionist_profile.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=ReceptionistProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_receptionist_profile(
    data: ReceptionistProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReceptionistProfileService(db)
    try:
        receptionist = await service.create_receptionist(data)
        return receptionist
    except UserNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ReceptionistProfileResponse])
async def list_receptionist_profiles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReceptionistProfileService(db)
    receptionists = await service.get_all_receptionists(skip=skip, limit=limit)
    return receptionists


@router.get("/{receptionist_id}", response_model=ReceptionistProfileResponse)
async def get_receptionist_profile(
    receptionist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReceptionistProfileService(db)
    receptionist = await service.get_receptionist(receptionist_id)
    if not receptionist:
        raise HTTPException(status_code=404, detail="Receptionist not found")
    return receptionist


@router.put("/{receptionist_id}", response_model=ReceptionistProfileResponse)
async def update_receptionist_profile(
    receptionist_id: int,
    data: ReceptionistProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReceptionistProfileService(db)
    receptionist = await service.update_receptionist(receptionist_id, data)
    if not receptionist:
        raise HTTPException(status_code=404, detail="Receptionist not found")
    return receptionist


@router.delete("/{receptionist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receptionist_profile(
    receptionist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReceptionistProfileService(db)
    deleted = await service.delete_receptionist(receptionist_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Receptionist not found")
    return None