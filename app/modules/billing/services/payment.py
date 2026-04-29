# app/modules/billing/payment_service.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import (
    InvoiceNotFoundError,
    InvoiceAlreadyPaidError,
    OverpaymentError,
    InvalidPaymentAmountError,
)
from app.common.schema.base import PaginatedResponse
from app.modules.billing.enums.base import InvoiceStatus, PaymentMethod
from app.modules.billing.models.base import BillingItem, Invoice, Payment
from app.modules.billing.schemas.base import BillingItemCreate, BillingItemUpdate, InvoiceCreate, InvoiceUpdate, PaymentCreate, PaymentUpdate
from app.modules.billing.services.invoice import InvoiceService
from app.modules.patients.models.models import Patient

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.invoice_service = InvoiceService(db)

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payments_by_invoice(self, invoice_id: int) -> List[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.payment_date.desc())
        )
        return result.scalars().all()


    async def get_payments(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> PaginatedResponse[Payment]:
        query = select(Payment)
        if filters:
            if "invoice_id" in filters:
                query = query.where(Payment.invoice_id == filters["invoice_id"])
            if "method" in filters:
                query = query.where(Payment.method == filters["method"])
            if "date_from" in filters:
                query = query.where(Payment.payment_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(Payment.payment_date <= filters["date_to"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(Payment.payment_date.desc())
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

    async def create_payment(self, data: PaymentCreate) -> Payment:
        # Validate invoice exists
        invoice = await self.db.get(Invoice, data.invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {data.invoice_id} not found")
        if invoice.status == "paid":
            raise ValueError("Invoice already fully paid")
        if invoice.status == "cancelled":
            raise ValueError("Cannot pay a cancelled invoice")
        # Check overpayment
        total_paid = await self._get_total_paid(data.invoice_id)
        new_total = total_paid + data.amount
        if new_total > invoice.total:
            raise OverpaymentError(
                f"Payment would exceed invoice total. Already paid {total_paid}, attempting to add {data.amount}"
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
        # Update invoice status
        await self.invoice_service.update_invoice_status_from_payments(data.invoice_id)
        return payment

    async def update_payment(self, payment_id: int, data: PaymentUpdate) -> Optional[Payment]:
        payment = await self.get_payment(payment_id)
        if not payment:
            raise PatientNotFoundError(f"Payment {payment_id} not found")
        invoice = await self.db.get(Invoice, payment.invoice_id)
        if invoice.status == "paid":
            raise ValueError("Cannot update payment on fully paid invoice")
        old_amount = payment.amount
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(payment, key, value)
        # If amount changed, check overpayment
        if "amount" in update_data and update_data["amount"] != old_amount:
            total_paid_excluding_this = await self._get_total_paid(payment.invoice_id) - old_amount
            new_total = total_paid_excluding_this + payment.amount
            if new_total > invoice.total:
                raise OverpaymentError("Updated payment amount would exceed invoice total")
        await self.db.commit()
        await self.db.refresh(payment)
        await self.invoice_service.update_invoice_status_from_payments(payment.invoice_id)
        return payment

    async def delete_payment(self, payment_id: int) -> bool:
        payment = await self.get_payment(payment_id)
        if not payment:
            return False
        invoice = await self.db.get(Invoice, payment.invoice_id)
        if invoice.status == "paid":
            raise ValueError("Cannot delete payment from fully paid invoice")
        await self.db.delete(payment)
        await self.db.commit()
        await self.invoice_service.update_invoice_status_from_payments(payment.invoice_id)
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def _get_total_paid(self, invoice_id: int) -> Decimal:
        stmt = select(func.sum(Payment.amount)).where(Payment.invoice_id == invoice_id)
        result = await self.db.execute(stmt)
        return result.scalar() or Decimal("0.00")