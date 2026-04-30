# app/modules/inventory/inventory_transaction_service.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.common.exceptions.inventory import InsufficientStockError, InventoryItemNotFoundError, InventoryTransactionNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.inventory.models.inventory_item import InventoryItem
from app.modules.inventory.models.inventory_transaction import InventoryTransaction
from app.modules.inventory.schemas.base import InventoryItemCreate, InventoryItemUpdate, InventoryTransactionCreate, InventoryTransactionUpdate
from sqlalchemy.orm import selectinload


class InventoryTransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_transaction(self, transaction_id: int) -> Optional[InventoryTransaction]:
        result = await self.db.execute(
            select(InventoryTransaction).where(InventoryTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def get_transactions_by_item(
        self, item_id: int, skip: int = 0, limit: int = 100
    ) -> List[InventoryTransaction]:
        query = (
            select(InventoryTransaction)
            .where(InventoryTransaction.item_id == item_id)
            .order_by(InventoryTransaction.transaction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "transaction_date",
        descending: bool = True,
    ) -> PaginatedResponse[InventoryTransaction]:
        query = select(InventoryTransaction)
        if filters:
            if "item_id" in filters:
                query = query.where(InventoryTransaction.item_id == filters["item_id"])
            if "transaction_type" in filters:
                query = query.where(InventoryTransaction.transaction_type == filters["transaction_type"])
            if "performed_by_id" in filters:
                query = query.where(InventoryTransaction.performed_by_id == filters["performed_by_id"])
            if "date_from" in filters:
                query = query.where(InventoryTransaction.transaction_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(InventoryTransaction.transaction_date <= filters["date_to"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_col = getattr(InventoryTransaction, order_by, InventoryTransaction.transaction_date)
        if descending:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=page_size,
            pages=pages
        )

    async def create_transaction(self, data: InventoryTransactionCreate) -> InventoryTransaction:
        # Validate item exists if item_id provided
        if data.item_id:
            from app.modules.inventory.services.inventory_item import InventoryItemService
            item_svc = InventoryItemService(self.db)
            item = await item_svc.get_item(data.item_id)
            if not item:
                raise InventoryItemNotFoundError(f"Item {data.item_id} not found")
        transaction = InventoryTransaction(
            item_id=data.item_id,
            transaction_type=data.transaction_type,
            quantity=data.quantity,
            transaction_date=data.transaction_date or datetime.utcnow(),
            reference_document=data.reference_document,
            performed_by_id=data.performed_by_id,
        )
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def update_transaction(
        self, transaction_id: int, data: InventoryTransactionUpdate
    ) -> Optional[InventoryTransaction]:
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise InventoryTransactionNotFoundError(f"Transaction {transaction_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(transaction, key, value)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def delete_transaction(self, transaction_id: int) -> bool:
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            return False
        await self.db.delete(transaction)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def get_transactions_by_type(
        self, transaction_type: str, from_date: Optional[datetime] = None
    ) -> List[InventoryTransaction]:
        query = select(InventoryTransaction).where(
            InventoryTransaction.transaction_type == transaction_type
        )
        if from_date:
            query = query.where(InventoryTransaction.transaction_date >= from_date)
        query = query.order_by(InventoryTransaction.transaction_date.desc())
        result = await self.db.execute(query)
        return result.scalars().all()