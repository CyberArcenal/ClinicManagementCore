# app/modules/billing/invoice_api.py
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import InvoiceNotFoundError
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.schemas.base import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.modules.billing.services.invoice import InvoiceService
from app.modules.user.models.base import User


router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InvoiceService(db)
    try:
        invoice = await service.create_invoice(data)
        return invoice
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    patient_id: Optional[int] = Query(None),
    status_filter: Optional[InvoiceStatus] = Query(None, alias="status"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if status_filter:
        filters["status"] = status_filter
    # date parsing could be added via datetime
    service = InvoiceService(db)
    invoices = await service.get_invoices(filters=filters, skip=skip, limit=limit)
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id, load_relations=True)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InvoiceService(db)
    try:
        invoice = await service.update_invoice(invoice_id, data)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InvoiceService(db)
    deleted = await service.delete_invoice(invoice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return None


@router.get("/{invoice_id}/totals", response_model=dict)
async def get_invoice_totals(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InvoiceService(db)
    totals = await service.get_invoice_totals(invoice_id)
    return totals