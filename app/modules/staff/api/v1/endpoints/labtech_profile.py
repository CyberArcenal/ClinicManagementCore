# app/modules/staff/api/v1/endpoints/labtech_profile.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


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


@router.get("/", response_model=List[LabTechProfileResponse])
async def list_labtech_profiles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LabTechProfileService(db)
    techs = await service.get_all_lab_techs(skip=skip, limit=limit)
    return techs


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