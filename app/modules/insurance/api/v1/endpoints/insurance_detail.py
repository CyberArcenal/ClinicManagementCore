from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.insurance import DuplicateInsuranceError, InsuranceDetailNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.insurance.schemas.base import (
    InsuranceDetailCreate,
    InsuranceDetailResponse,
    InsuranceDetailUpdate,
)
from app.modules.insurance.services.insurance_detail import InsuranceDetailService
from app.modules.user.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_insurance_detail(
    data: InsuranceDetailCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[InsuranceDetailResponse]:
    service = InsuranceDetailService(db)
    try:
        detail = await service.create_insurance_detail(data)
        return success_response(data=detail, message="Insurance detail created")
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateInsuranceError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/")
async def list_insurance_details(
    patient_id: Optional[int] = Query(None),
    provider_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[InsuranceDetailResponse]]:
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if provider_name:
        filters["provider_name"] = provider_name
    service = InsuranceDetailService(db)
    paginated = await service.get_all_insurance_details(
        filters=filters, page=page, page_size=page_size
    )
    return success_response(data=paginated, message="Insurance details retrieved")


@router.get("/{detail_id}")
async def get_insurance_detail(
    detail_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[InsuranceDetailResponse]:
    service = InsuranceDetailService(db)
    detail = await service.get_insurance_detail(detail_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Insurance detail not found")
    return success_response(data=detail, message="Insurance detail retrieved")


@router.get("/patient/{patient_id}")
async def get_patient_insurance_details(
    patient_id: int,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[InsuranceDetailResponse]]:
    service = InsuranceDetailService(db)
    details = await service.get_insurance_details_by_patient(
        patient_id, active_only=active_only
    )
    return success_response(data=details, message="Patient insurance details retrieved")


@router.put("/{detail_id}")
async def update_insurance_detail(
    detail_id: int,
    data: InsuranceDetailUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[InsuranceDetailResponse]:
    service = InsuranceDetailService(db)
    try:
        detail = await service.update_insurance_detail(detail_id, data)
        if not detail:
            raise HTTPException(status_code=404, detail="Insurance detail not found")
        return success_response(data=detail, message="Insurance detail updated")
    except InsuranceDetailNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insurance_detail(
    detail_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = InsuranceDetailService(db)
    try:
        deleted = await service.delete_insurance_detail(detail_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Insurance detail not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))