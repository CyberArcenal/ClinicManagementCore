# app/modules/billing/billing_item_service.py
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.common.exceptions.billing import (
    BillingItemNotFoundError,
    InvoiceNotFoundError,
    InvoiceAlreadyPaidError,
    OverpaymentError,
    InvalidPaymentAmountError,
)
from app.modules.billing.enums.base import InvoiceStatus, PaymentMethod
from app.modules.billing.models.base import BillingItem, Invoice, Payment
from app.modules.billing.schemas.base import BillingItemCreate, BillingItemUpdate, InvoiceCreate, InvoiceUpdate, PaymentCreate, PaymentUpdate
from app.modules.billing.services.invoice import InvoiceService
from app.modules.patients.models.models import Patient

class BillingItemService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.invoice_service = InvoiceService(db)

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_item(self, item_id: int) -> Optional[BillingItem]:
        result = await self.db.execute(
            select(BillingItem).where(BillingItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_items_by_invoice(self, invoice_id: int) -> List[BillingItem]:
        result = await self.db.execute(
            select(BillingItem)
            .where(BillingItem.invoice_id == invoice_id)
            .order_by(BillingItem.id)
        )
        return result.scalars().all()

    async def create_item(self, data: BillingItemCreate) -> BillingItem:
        # Validate invoice exists
        invoice = await self.db.get(Invoice, data.invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {data.invoice_id} not found")
        if invoice.status in ["paid", "cancelled"]:
            raise ValueError("Cannot add items to a paid or cancelled invoice")
        # Calculate total if not provided
        total = data.total or (data.quantity * data.unit_price)
        item = BillingItem(
            invoice_id=data.invoice_id,
            description=data.description,
            quantity=data.quantity,
            unit_price=data.unit_price,
            total=total,
            appointment_id=data.appointment_id,
            treatment_id=data.treatment_id,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        # Update invoice subtotal and total
        await self._recalculate_invoice_totals(data.invoice_id)
        return item

    async def update_item(self, item_id: int, data: BillingItemUpdate) -> Optional[BillingItem]:
        item = await self.get_item(item_id)
        if not item:
            raise BillingItemNotFoundError(f"Item {item_id} not found")
        invoice = await self.db.get(Invoice, item.invoice_id)
        if invoice.status in ["paid", "cancelled"]:
            raise ValueError("Cannot modify items on paid or cancelled invoice")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        # Recalculate total if quantity or unit_price changed
        if "quantity" in update_data or "unit_price" in update_data:
            item.total = item.quantity * item.unit_price
        await self.db.commit()
        await self.db.refresh(item)
        await self._recalculate_invoice_totals(item.invoice_id)
        return item

    async def delete_item(self, item_id: int) -> bool:
        item = await self.get_item(item_id)
        if not item:
            return False
        invoice = await self.db.get(Invoice, item.invoice_id)
        if invoice.status in ["paid", "cancelled"]:
            raise ValueError("Cannot delete items from paid or cancelled invoice")
        await self.db.delete(item)
        await self.db.commit()
        await self._recalculate_invoice_totals(item.invoice_id)
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def _recalculate_invoice_totals(self, invoice_id: int) -> None:
        """Update invoice subtotal and total based on current items."""
        stmt = select(func.sum(BillingItem.total)).where(BillingItem.invoice_id == invoice_id)
        result = await self.db.execute(stmt)
        subtotal = result.scalar() or Decimal("0.00")
        invoice = await self.db.get(Invoice, invoice_id)
        if invoice:
            invoice.subtotal = subtotal
            invoice.total = subtotal + invoice.tax
            await self.db.commit()