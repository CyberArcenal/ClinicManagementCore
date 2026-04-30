from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.billing import BillingItemNotFoundError, InvoiceNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.billing.schemas.base import BillingItemCreate, BillingItemResponse, BillingItemUpdate
from app.modules.billing.services.billing import BillingItemService
from app.modules.user.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_billing_item(
    data: BillingItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[BillingItemResponse]:
    service = BillingItemService(db)
    try:
        item = await service.create_item(data)
        return success_response(data=item, message="Billing item created")
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_billing_items(
    invoice_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[BillingItemResponse]]:
    service = BillingItemService(db)
    if invoice_id:
        items = await service.get_items_by_invoice(invoice_id)
        return success_response(data=items, message="Billing items retrieved")
    else:
        return success_response(data=[], message="No billing items (filter by invoice_id)")


@router.get("/{item_id}")
async def get_billing_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[BillingItemResponse]:
    service = BillingItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Billing item not found")
    return success_response(data=item, message="Billing item retrieved")


@router.put("/{item_id}")
async def update_billing_item(
    item_id: int,
    data: BillingItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[BillingItemResponse]:
    service = BillingItemService(db)
    try:
        item = await service.update_item(item_id, data)
        if not item:
            raise HTTPException(status_code=404, detail="Billing item not found")
        return success_response(data=item, message="Billing item updated")
    except BillingItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = BillingItemService(db)
    deleted = await service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Billing item not found")
    return None