from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import InvoiceNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.schemas.base import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.modules.billing.services.invoice import InvoiceService
from app.modules.user.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[InvoiceResponse]:
    service = InvoiceService(db)
    try:
        invoice = await service.create_invoice(data)
        return success_response(data=invoice, message="Invoice created")
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_invoices(
    patient_id: Optional[int] = Query(None),
    status_filter: Optional[InvoiceStatus] = Query(None, alias="status"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[InvoiceResponse]]:
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if status_filter:
        filters["status"] = status_filter
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    service = InvoiceService(db)
    paginated = await service.get_invoices(
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return success_response(data=paginated, message="Invoices retrieved")


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[InvoiceResponse]:
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id, load_relations=True)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return success_response(data=invoice, message="Invoice retrieved")


@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[InvoiceResponse]:
    service = InvoiceService(db)
    try:
        invoice = await service.update_invoice(invoice_id, data)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return success_response(data=invoice, message="Invoice updated")
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = InvoiceService(db)
    deleted = await service.delete_invoice(invoice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return None


@router.get("/{invoice_id}/totals")
async def get_invoice_totals(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict]:
    service = InvoiceService(db)
    totals = await service.get_invoice_totals(invoice_id)
    return success_response(data=totals, message="Invoice totals")