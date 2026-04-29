# app/modules/billing/invoice_service.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

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
from app.modules.patients.models.models import Patient

class InvoiceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
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

    async def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        )
        return result.scalar_one_or_none()


    async def get_invoices(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "issue_date",
        descending: bool = True,
    ) -> PaginatedResponse[Invoice]:
        """
        List invoices with pagination (page/page_size) and optional filters.
        """
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

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Ordering
        order_col = getattr(Invoice, order_by, Invoice.issue_date)
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

    async def create_invoice(self, data: InvoiceCreate) -> Invoice:
        # Validate patient exists
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")
        # Generate invoice number if not provided
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

    async def update_invoice(self, invoice_id: int, data: InvoiceUpdate) -> Optional[Invoice]:
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        # Prevent changing status to PAID if not fully paid; can be overridden by manual update
        for key, value in update_data.items():
            setattr(invoice, key, value)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def delete_invoice(self, invoice_id: int) -> bool:
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return False
        # Prevent deletion if payments exist
        if invoice.payments:
            raise ValueError("Cannot delete invoice with existing payments")
        await self.db.delete(invoice)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def _generate_invoice_number(self) -> str:
        year = datetime.utcnow().year
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

    async def get_invoice_totals(self, invoice_id: int) -> Dict[str, Decimal]:
        """Calculate subtotal and total from items (without relying on stored values)."""
        stmt = select(func.sum(BillingItem.total)).where(BillingItem.invoice_id == invoice_id)
        result = await self.db.execute(stmt)
        subtotal = result.scalar() or Decimal("0.00")
        invoice = await self.get_invoice(invoice_id)
        tax = invoice.tax if invoice else Decimal("0.00")
        total = subtotal + tax
        return {"subtotal": subtotal, "tax": tax, "total": total}

    async def update_invoice_status_from_payments(self, invoice_id: int) -> Invoice:
        """Recalculate paid amount and set invoice status accordingly."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")
        total_paid_stmt = select(func.sum(Payment.amount)).where(Payment.invoice_id == invoice_id)
        total_paid = (await self.db.execute(total_paid_stmt)).scalar() or Decimal("0.00")
        if total_paid >= invoice.total:
            invoice.status = InvoiceStatus.PAID
        elif total_paid > 0:
            invoice.status = InvoiceStatus.PARTIAL
        else:
            # Keep current status if no payment, but don't override DRAFT/SENT
            if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.PARTIAL]:
                invoice.status = InvoiceStatus.SENT
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice