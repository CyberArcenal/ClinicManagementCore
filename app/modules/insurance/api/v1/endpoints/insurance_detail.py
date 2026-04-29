# app/modules/insurance/insurance_detail_api.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.insurance import DuplicateInsuranceError, InsuranceDetailNotFoundError
from app.modules.insurance.schemas.base import InsuranceDetailCreate, InsuranceDetailResponse, InsuranceDetailUpdate
from app.modules.insurance.services.insurance_detail import InsuranceDetailService
from app.modules.user.models.base import User

router = APIRouter(prefix="/insurance-details", tags=["Insurance Details"])


@router.post("/", response_model=InsuranceDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_insurance_detail(
    data: InsuranceDetailCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    """
    Create a new insurance detail for a patient.
    Requires role: receptionist, admin.
    """
    service = InsuranceDetailService(db)
    try:
        detail = await service.create_insurance_detail(data)
        return detail
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateInsuranceError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=List[InsuranceDetailResponse])
async def list_insurance_details(
    patient_id: Optional[int] = Query(None),
    provider_name: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if provider_name:
        filters["provider_name"] = provider_name
    service = InsuranceDetailService(db)
    details = await service.get_all_insurance_details(filters=filters, skip=skip, limit=limit)
    return details


@router.get("/{detail_id}", response_model=InsuranceDetailResponse)
async def get_insurance_detail(
    detail_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InsuranceDetailService(db)
    detail = await service.get_insurance_detail(detail_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Insurance detail not found")
    return detail


@router.get("/patient/{patient_id}", response_model=List[InsuranceDetailResponse])
async def get_patient_insurance_details(
    patient_id: int,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all insurance details for a patient. Optionally only active ones.
    """
    service = InsuranceDetailService(db)
    details = await service.get_insurance_details_by_patient(patient_id, active_only=active_only)
    return details


@router.put("/{detail_id}", response_model=InsuranceDetailResponse)
async def update_insurance_detail(
    detail_id: int,
    data: InsuranceDetailUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = InsuranceDetailService(db)
    try:
        detail = await service.update_insurance_detail(detail_id, data)
        if not detail:
            raise HTTPException(status_code=404, detail="Insurance detail not found")
        return detail
    except InsuranceDetailNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insurance_detail(
    detail_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InsuranceDetailService(db)
    try:
        deleted = await service.delete_insurance_detail(detail_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Insurance detail not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))