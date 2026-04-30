from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.inventory import InventoryItemNotFoundError, InventoryTransactionNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.inventory.schemas.base import (
    InventoryTransactionCreate,
    InventoryTransactionResponse,
    InventoryTransactionUpdate,
)
from app.modules.inventory.services.inventory_transaction import InventoryTransactionService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: InventoryTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
) -> SuccessResponse[InventoryTransactionResponse]:
    service = InventoryTransactionService(db)
    try:
        transaction = await service.create_transaction(data)
        return success_response(data=transaction, message="Transaction created")
    except InventoryItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_transactions(
    item_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    performed_by_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
) -> SuccessResponse[PaginatedResponse[InventoryTransactionResponse]]:
    filters = {}
    if item_id:
        filters["item_id"] = item_id
    if transaction_type:
        filters["transaction_type"] = transaction_type
    if performed_by_id:
        filters["performed_by_id"] = performed_by_id

    service = InventoryTransactionService(db)
    paginated = await service.get_transactions(
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return success_response(data=paginated, message="Transactions retrieved")


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
) -> SuccessResponse[InventoryTransactionResponse]:
    service = InventoryTransactionService(db)
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return success_response(data=transaction, message="Transaction retrieved")


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    data: InventoryTransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[InventoryTransactionResponse]:
    service = InventoryTransactionService(db)
    try:
        transaction = await service.update_transaction(transaction_id, data)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return success_response(data=transaction, message="Transaction updated")
    except InventoryTransactionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = InventoryTransactionService(db)
    deleted = await service.delete_transaction(transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None