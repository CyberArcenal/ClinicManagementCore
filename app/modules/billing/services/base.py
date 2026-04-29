# app/modules/billing/service.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import (
    InvoiceNotFoundError,
    InvoiceAlreadyPaidError,
    OverpaymentError,
    InvalidPaymentAmountError,
)
from app.modules.billing.enums.base import InvoiceStatus, PaymentMethod
from app.modules.billing.models.base import BillingItem, Invoice, Payment
from app.modules.billing.schemas.base import BillingItemCreate, BillingItemUpdate, InvoiceCreate, InvoiceUpdate, PaymentCreate, PaymentUpdate
from app.modules.patients.models.models import Patient


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Invoice CRUD + Utilities
    # ------------------------------------------------------------------
    async def get_invoice(
        self, invoice_id: int, load_relations: bool = False
    ) -> Optional[Invoice]:
        query = select(Invoice).where(Invoice.id == invoice_id)
        if load_relations:
            query = query.options(
                selectinload(Invoice.patient),
                selectinload(Invoice.items),
                selectinload(Invoice.payments),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_invoices(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "issue_date",
        descending: bool = True,
    ) -> List[Invoice]:
        query = select(Invoice)
        if filters:
            if "patient_id" in filters:
                query = query.where(Invoice.patient_id == filters["patient_id"])
            if "status" in filters:
                query = query.where(Invoice.status == filters["status"])
            if "date_from" in filters:
                query = query.where(Invoice.issue_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(Invoice.issue_date <= filters["date_to"])

        order_column = getattr(Invoice, order_by, Invoice.issue_date)
        if descending:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_invoice(self, data: InvoiceCreate) -> Invoice:
        # Validate patient exists
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")

        # Generate unique invoice number if not provided
        invoice_number = data.invoice_number or await self._generate_invoice_number()

        invoice = Invoice(
            patient_id=data.patient_id,
            invoice_number=invoice_number,
            issue_date=data.issue_date or datetime.utcnow(),
            due_date=data.due_date,
            subtotal=data.subtotal,
            tax=data.tax,
            total=data.total,
            status=data.status,
            notes=data.notes,
        )
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def update_invoice(
        self, invoice_id: int, data: InvoiceUpdate
    ) -> Optional[Invoice]:
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")

        # Don't allow update if already paid or partially paid? (optional rule)
        if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID]:
            # you can allow updating notes only, but not financial fields
            if data.due_date is not None or data.status is not None:
                raise ValueError("Cannot modify paid/partially paid invoice")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(invoice, key, value)

        # If status is changed to PAID, ensure total paid equals invoice total
        if data.status == InvoiceStatus.PAID:
            total_paid = await self._get_total_paid(invoice_id)
            if total_paid < invoice.total:
                raise InvalidPaymentAmountError(
                    f"Cannot mark as PAID: total paid ({total_paid}) < invoice total ({invoice.total})"
                )

        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def delete_invoice(self, invoice_id: int) -> bool:
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return False
        # Optional: prevent deletion if payments exist
        if invoice.payments:
            raise ValueError("Cannot delete invoice with existing payments")
        await self.db.delete(invoice)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # BillingItem CRUD
    # ------------------------------------------------------------------
    async def add_billing_item(self, data: BillingItemCreate) -> BillingItem:
        invoice = await self.get_invoice(data.invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {data.invoice_id} not found")
        if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            raise ValueError("Cannot add items to paid or cancelled invoice")

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

        # Update invoice totals
        await self._recalculate_invoice_totals(invoice.id)
        return item

    async def update_billing_item(
        self, item_id: int, data: BillingItemUpdate
    ) -> Optional[BillingItem]:
        item = await self.db.get(BillingItem, item_id)
        if not item:
            return None

        invoice = await self.get_invoice(item.invoice_id)
        if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            raise ValueError("Cannot modify items on paid or cancelled invoice")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        # Recalculate total if quantity or unit_price changed
        if "quantity" in update_data or "unit_price" in update_data:
            item.total = item.quantity * item.unit_price

        await self.db.commit()
        await self.db.refresh(item)

        # Update invoice totals
        await self._recalculate_invoice_totals(invoice.id)
        return item

    async def remove_billing_item(self, item_id: int) -> bool:
        item = await self.db.get(BillingItem, item_id)
        if not item:
            return False
        invoice = await self.get_invoice(item.invoice_id)
        if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            raise ValueError("Cannot remove items from paid or cancelled invoice")

        await self.db.delete(item)
        await self.db.commit()
        await self._recalculate_invoice_totals(invoice.id)
        return True

    # ------------------------------------------------------------------
    # Payment CRUD + Utilities
    # ------------------------------------------------------------------
    async def add_payment(self, data: PaymentCreate) -> Payment:
        invoice = await self.get_invoice(data.invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {data.invoice_id} not found")

        # Prevent payment if invoice is already paid or cancelled
        if invoice.status == InvoiceStatus.PAID:
            raise InvoiceAlreadyPaidError("Invoice already fully paid")
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ValueError("Cannot pay a cancelled invoice")

        # Calculate total paid so far
        total_paid = await self._get_total_paid(invoice.id)
        new_total_paid = total_paid + data.amount

        if new_total_paid > invoice.total:
            raise OverpaymentError(
                f"Payment amount {data.amount} would exceed invoice total {invoice.total} (already paid {total_paid})"
            )

        payment = Payment(
            invoice_id=data.invoice_id,
            amount=data.amount,
            payment_date=data.payment_date or datetime.utcnow(),
            method=data.method,
            reference_number=data.reference_number,
            notes=data.notes,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        # Update invoice status based on new total paid
        await self._update_invoice_status_from_payments(invoice.id)
        return payment

    async def update_payment(
        self, payment_id: int, data: PaymentUpdate
    ) -> Optional[Payment]:
        payment = await self.db.get(Payment, payment_id)
        if not payment:
            return None

        invoice = await self.get_invoice(payment.invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot modify payment on fully paid invoice")

        old_amount = payment.amount
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(payment, key, value)

        # If amount changed, check new total
        if "amount" in update_data:
            total_paid_excluding_this = await self._get_total_paid(invoice.id) - old_amount
            new_total = total_paid_excluding_this + payment.amount
            if new_total > invoice.total:
                raise OverpaymentError("Updated payment would exceed invoice total")
            if new_total < 0:
                raise InvalidPaymentAmountError("Total paid cannot be negative")

        await self.db.commit()
        await self.db.refresh(payment)
        await self._update_invoice_status_from_payments(invoice.id)
        return payment

    async def delete_payment(self, payment_id: int) -> bool:
        payment = await self.db.get(Payment, payment_id)
        if not payment:
            return False
        invoice = await self.get_invoice(payment.invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot delete payment from fully paid invoice")

        await self.db.delete(payment)
        await self.db.commit()
        await self._update_invoice_status_from_payments(invoice.id)
        return True

    # ------------------------------------------------------------------
    # Internal Utilities
    # ------------------------------------------------------------------
    async def _generate_invoice_number(self) -> str:
        """Generate unique invoice number, e.g., INV-20240001"""
        year = datetime.utcnow().year
        # Get max sequential number for this year
        stmt = select(func.max(Invoice.invoice_number)).where(
            Invoice.invoice_number.like(f"INV-{year}%")
        )
        result = await self.db.execute(stmt)
        max_num = result.scalar()
        if max_num:
            seq = int(max_num.split("-")[1]) + 1
        else:
            seq = 1
        return f"INV-{year}{seq:04d}"

    async def _recalculate_invoice_totals(self, invoice_id: int) -> None:
        """Recalculate subtotal, total based on billing items."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return

        # Sum all item totals
        stmt = select(func.sum(BillingItem.total)).where(BillingItem.invoice_id == invoice_id)
        result = await self.db.execute(stmt)
        subtotal = result.scalar() or Decimal("0.00")

        # Assume tax is stored as a percentage? For simplicity, use invoice.tax as fixed amount
        # But we can keep existing tax value or recompute.
        # Here we keep existing tax value (manual override allowed)
        total = subtotal + invoice.tax

        invoice.subtotal = subtotal
        invoice.total = total
        await self.db.commit()

    async def _get_total_paid(self, invoice_id: int) -> Decimal:
        stmt = select(func.sum(Payment.amount)).where(Payment.invoice_id == invoice_id)
        result = await self.db.execute(stmt)
        return result.scalar() or Decimal("0.00")

    async def _update_invoice_status_from_payments(self, invoice_id: int) -> None:
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return

        total_paid = await self._get_total_paid(invoice_id)
        if total_paid >= invoice.total:
            invoice.status = InvoiceStatus.PAID
        elif total_paid > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        else:
            # Keep original status (e.g., DRAFT, SENT) – only change if it was previously paid
            if invoice.status == InvoiceStatus.PAID:
                invoice.status = InvoiceStatus.SENT  # or DRAFT? decide
        await self.db.commit()