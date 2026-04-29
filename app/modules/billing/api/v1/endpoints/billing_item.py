# app/modules/billing/invoice_api.py
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import BillingItemNotFoundError, InvoiceNotFoundError
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.schemas.base import BillingItemCreate, BillingItemResponse, BillingItemUpdate, InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.modules.billing.services.billing import BillingItemService
from app.modules.billing.services.invoice import InvoiceService
from app.modules.user.models.base import User

router = APIRouter(prefix="/billing-items", tags=["Billing Items"])


@router.post("/", response_model=BillingItemResponse, status_code=status.HTTP_201_CREATED)
async def create_billing_item(
    data: BillingItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = BillingItemService(db)
    try:
        item = await service.create_item(data)
        return item
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[BillingItemResponse])
async def list_billing_items(
    invoice_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BillingItemService(db)
    if invoice_id:
        items = await service.get_items_by_invoice(invoice_id)
    else:
        # If no filter, maybe limited query – we can implement a general get_all
        items = []  # optionally implement get_all_items in service
    return items


@router.get("/{item_id}", response_model=BillingItemResponse)
async def get_billing_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BillingItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Billing item not found")
    return item


@router.put("/{item_id}", response_model=BillingItemResponse)
async def update_billing_item(
    item_id: int,
    data: BillingItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = BillingItemService(db)
    try:
        item = await service.update_item(item_id, data)
        if not item:
            raise HTTPException(status_code=404, detail="Billing item not found")
        return item
    except BillingItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = BillingItemService(db)
    deleted = await service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Billing item not found")
    return None