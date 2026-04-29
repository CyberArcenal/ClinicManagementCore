# app/modules/staff/api/v1/endpoints/pharmacist_profile.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=PharmacistProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_pharmacist_profile(
    data: PharmacistProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PharmacistProfileService(db)
    try:
        pharmacist = await service.create_pharmacist(data)
        return pharmacist
    except UserNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[PharmacistProfileResponse])
async def list_pharmacist_profiles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PharmacistProfileService(db)
    pharmacists = await service.get_all_pharmacists(skip=skip, limit=limit)
    return pharmacists


@router.get("/{pharmacist_id}", response_model=PharmacistProfileResponse)
async def get_pharmacist_profile(
    pharmacist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PharmacistProfileService(db)
    pharmacist = await service.get_pharmacist(pharmacist_id)
    if not pharmacist:
        raise HTTPException(status_code=404, detail="Pharmacist not found")
    return pharmacist


@router.put("/{pharmacist_id}", response_model=PharmacistProfileResponse)
async def update_pharmacist_profile(
    pharmacist_id: int,
    data: PharmacistProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PharmacistProfileService(db)
    pharmacist = await service.update_pharmacist(pharmacist_id, data)
    if not pharmacist:
        raise HTTPException(status_code=404, detail="Pharmacist not found")
    return pharmacist


@router.delete("/{pharmacist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pharmacist_profile(
    pharmacist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PharmacistProfileService(db)
    deleted = await service.delete_pharmacist(pharmacist_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pharmacist not found")
    return None