# app/modules/insurance/insurance_claim_api.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.billing import InvoiceNotFoundError
from app.common.exceptions.insurance import ClaimAmountExceedsInvoiceError, InsuranceClaimNotFoundError, InsuranceCoverageExpiredError, InsuranceDetailNotFoundError
from app.modules.insurance.schemas.base import InsuranceClaimCreate, InsuranceClaimResponse, InsuranceClaimUpdate
from app.modules.insurance.services.insurance_claim import InsuranceClaimService
from app.modules.user.models.base import User


router = APIRouter(prefix="/insurance-claims", tags=["Insurance Claims"])


@router.post("/", response_model=InsuranceClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_insurance_claim(
    data: InsuranceClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("billing_staff")),
):
    """
    Create a new insurance claim.
    Requires role: billing_staff or admin.
    """
    service = InsuranceClaimService(db)
    try:
        claim = await service.create_claim(data)
        return claim
    except (InsuranceDetailNotFoundError, InvoiceNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (InsuranceCoverageExpiredError, ClaimAmountExceedsInvoiceError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedResponse[InsuranceClaimResponse])
async def list_insurance_claims(
    invoice_id: Optional[int] = Query(None),
    insurance_detail_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    submitted_date_from: Optional[str] = Query(None),
    submitted_date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if invoice_id:
        filters["invoice_id"] = invoice_id
    if insurance_detail_id:
        filters["insurance_detail_id"] = insurance_detail_id
    if status_filter:
        filters["status"] = status_filter
    if submitted_date_from:
        filters["submitted_date_from"] = submitted_date_from
    if submitted_date_to:
        filters["submitted_date_to"] = submitted_date_to

    service = InsuranceClaimService(db)
    paginated = await service.get_claims(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return paginated


@router.get("/{claim_id}", response_model=InsuranceClaimResponse)
async def get_insurance_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InsuranceClaimService(db)
    claim = await service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Insurance claim not found")
    return claim


@router.put("/{claim_id}", response_model=InsuranceClaimResponse)
async def update_insurance_claim(
    claim_id: int,
    data: InsuranceClaimUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("billing_staff")),
):
    service = InsuranceClaimService(db)
    try:
        claim = await service.update_claim(claim_id, data)
        if not claim:
            raise HTTPException(status_code=404, detail="Insurance claim not found")
        return claim
    except InsuranceClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{claim_id}/status", response_model=InsuranceClaimResponse)
async def update_claim_status(
    claim_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("billing_staff")),
):
    service = InsuranceClaimService(db)
    try:
        claim = await service.update_claim_status(claim_id, new_status)
        if not claim:
            raise HTTPException(status_code=404, detail="Insurance claim not found")
        return claim
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insurance_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InsuranceClaimService(db)
    try:
        deleted = await service.delete_claim(claim_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Insurance claim not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))