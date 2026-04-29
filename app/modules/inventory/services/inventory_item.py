# app/modules/inventory/inventory_item_service.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.common.exceptions.inventory import InsufficientStockError, InventoryItemNotFoundError
from app.modules.inventory.models.models import InventoryItem, InventoryTransaction
from app.modules.inventory.schemas.base import InventoryItemCreate, InventoryItemUpdate
from sqlchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

class InventoryItemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_item(self, item_id: int) -> Optional[InventoryItem]:
        result = await self.db.execute(
            select(InventoryItem).where(InventoryItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_item_by_sku(self, sku: str) -> Optional[InventoryItem]:
        result = await self.db.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        )
        return result.scalar_one_or_none()

    async def get_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "name",
        descending: bool = False,
    ) -> List[InventoryItem]:
        query = select(InventoryItem)
        if filters:
            if "category" in filters:
                query = query.where(InventoryItem.category == filters["category"])
            if "is_active" in filters:
                query = query.where(InventoryItem.is_active == filters["is_active"])
            if "name_contains" in filters:
                query = query.where(InventoryItem.name.ilike(f"%{filters['name_contains']}%"))
            if "low_stock_only" in filters and filters["low_stock_only"]:
                query = query.where(InventoryItem.quantity_on_hand <= InventoryItem.reorder_level)
            if "expired_only" in filters and filters["expired_only"]:
                query = query.where(InventoryItem.expiry_date < datetime.utcnow())
        order_col = getattr(InventoryItem, order_by, InventoryItem.name)
        if descending:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_item(self, data: InventoryItemCreate) -> InventoryItem:
        if data.sku:
            existing = await self.get_item_by_sku(data.sku)
            if existing:
                raise ValueError(f"Item with SKU {data.sku} already exists")
        item = InventoryItem(
            name=data.name,
            category=data.category,
            sku=data.sku,
            quantity_on_hand=data.quantity_on_hand or 0,
            unit=data.unit,
            reorder_level=data.reorder_level,
            unit_cost=data.unit_cost,
            selling_price=data.selling_price,
            expiry_date=data.expiry_date,
            location=data.location,
            is_active=data.is_active,
            notes=data.notes,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_item(self, item_id: int, data: InventoryItemUpdate) -> Optional[InventoryItem]:
        item = await self.get_item(item_id)
        if not item:
            raise InventoryItemNotFoundError(f"Item {item_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        if "sku" in update_data and update_data["sku"] != item.sku:
            existing = await self.get_item_by_sku(update_data["sku"])
            if existing:
                raise ValueError(f"SKU {update_data['sku']} already exists")
        for key, value in update_data.items():
            setattr(item, key, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item_id: int) -> bool:
        item = await self.get_item(item_id)
        if not item:
            return False
        # Soft delete
        item.is_active = False
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Stock Management
    # ------------------------------------------------------------------
    async def add_stock(
        self,
        item_id: int,
        quantity: int,
        performed_by_id: Optional[int] = None,
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        item = await self.get_item(item_id)
        if not item:
            raise InventoryItemNotFoundError(f"Item {item_id} not found")
        item.quantity_on_hand += quantity
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def remove_stock(
        self,
        item_id: int,
        quantity: int,
        performed_by_id: Optional[int] = None,
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        item = await self.get_item(item_id)
        if not item:
            raise InventoryItemNotFoundError(f"Item {item_id} not found")
        if item.quantity_on_hand < quantity:
            raise InsufficientStockError(
                f"Insufficient stock: available {item.quantity_on_hand}, requested {quantity}"
            )
        item.quantity_on_hand -= quantity
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def adjust_stock(
        self,
        item_id: int,
        new_quantity: int,
        performed_by_id: Optional[int] = None,
    ) -> InventoryItem:
        item = await self.get_item(item_id)
        if not item:
            raise InventoryItemNotFoundError(f"Item {item_id} not found")
        item.quantity_on_hand = new_quantity
        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    async def get_low_stock_items(self) -> List[InventoryItem]:
        query = select(InventoryItem).where(
            InventoryItem.is_active == True,
            InventoryItem.quantity_on_hand <= InventoryItem.reorder_level,
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_expired_items(self) -> List[InventoryItem]:
        query = select(InventoryItem).where(
            InventoryItem.expiry_date.isnot(None),
            InventoryItem.expiry_date < datetime.utcnow(),
            InventoryItem.quantity_on_hand > 0,
            InventoryItem.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalars().all()