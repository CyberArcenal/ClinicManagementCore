# app/modules/inventory/api/v1/endpoints/inventory_item.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.inventory import InsufficientStockError, InventoryItemNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.inventory.schemas.base import InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate
from app.modules.inventory.services.inventory_item import InventoryItemService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    data: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InventoryItemService(db)
    try:
        item = await service.create_item(data)
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/", response_model=PaginatedResponse[InventoryItemResponse])
async def list_inventory_items(
    category: Optional[str] = Query(None),
    name_contains: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    expired_only: bool = Query(False),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if category:
        filters["category"] = category
    if name_contains:
        filters["name_contains"] = name_contains
    if low_stock_only:
        filters["low_stock_only"] = True
    if expired_only:
        filters["expired_only"] = True
    filters["is_active"] = is_active

    service = InventoryItemService(db)
    paginated = await service.get_items(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return paginated


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.put("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    data: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InventoryItemService(db)
    try:
        item = await service.update_item(item_id, data)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return item
    except (InventoryItemNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InventoryItemService(db)
    deleted = await service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return None


@router.patch("/{item_id}/add-stock", response_model=InventoryItemResponse)
async def add_stock(
    item_id: int,
    quantity: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    service = InventoryItemService(db)
    try:
        item = await service.add_stock(item_id, quantity, performed_by_id=current_user.id)
        return item
    except (InventoryItemNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{item_id}/remove-stock", response_model=InventoryItemResponse)
async def remove_stock(
    item_id: int,
    quantity: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    service = InventoryItemService(db)
    try:
        item = await service.remove_stock(item_id, quantity, performed_by_id=current_user.id)
        return item
    except (InventoryItemNotFoundError, InsufficientStockError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{item_id}/adjust-stock", response_model=InventoryItemResponse)
async def adjust_stock(
    item_id: int,
    new_quantity: int = Query(..., ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InventoryItemService(db)
    try:
        item = await service.adjust_stock(item_id, new_quantity, performed_by_id=current_user.id)
        return item
    except InventoryItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))