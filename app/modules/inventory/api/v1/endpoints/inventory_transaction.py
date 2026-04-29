# app/modules/inventory/api/v1/endpoints/inventory_transaction.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.inventory import InsufficientStockError, InventoryItemNotFoundError, InventoryTransactionNotFoundError
from app.modules.inventory.schemas.base import InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate, InventoryTransactionCreate, InventoryTransactionResponse, InventoryTransactionUpdate
from app.modules.inventory.services.inventory_item import InventoryItemService
from app.modules.inventory.services.inventory_transaction import InventoryTransactionService
from app.modules.user.models import User


router = APIRouter()


@router.post("/", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: InventoryTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    service = InventoryTransactionService(db)
    try:
        transaction = await service.create_transaction(data)
        return transaction
    except InventoryItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[InventoryTransactionResponse])
async def list_transactions(
    item_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    performed_by_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    filters = {}
    if item_id:
        filters["item_id"] = item_id
    if transaction_type:
        filters["transaction_type"] = transaction_type
    if performed_by_id:
        filters["performed_by_id"] = performed_by_id

    service = InventoryTransactionService(db)
    transactions = await service.get_transactions(filters=filters, skip=skip, limit=limit)
    return transactions


@router.get("/{transaction_id}", response_model=InventoryTransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    service = InventoryTransactionService(db)
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/{transaction_id}", response_model=InventoryTransactionResponse)
async def update_transaction(
    transaction_id: int,
    data: InventoryTransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InventoryTransactionService(db)
    try:
        transaction = await service.update_transaction(transaction_id, data)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except InventoryTransactionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = InventoryTransactionService(db)
    deleted = await service.delete_transaction(transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None