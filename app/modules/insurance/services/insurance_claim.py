# app/modules/insurance/insurance_claim_service.py
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import InvoiceNotFoundError
from app.common.exceptions.insurance import ClaimAmountExceedsInvoiceError, DuplicateInsuranceError, InsuranceClaimNotFoundError, InsuranceCoverageExpiredError, InsuranceDetailNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.billing.models.base import Invoice
from app.modules.insurance.models.models import InsuranceClaim, InsuranceDetail
from app.modules.insurance.schemas.base import InsuranceClaimCreate, InsuranceClaimUpdate, InsuranceDetailCreate, InsuranceDetailUpdate
from app.modules.patients.models.models import Patient


class InsuranceClaimService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # We need a reference to InsuranceDetailService for coverage check
        from app.modules.insurance.services.insurance_detail import InsuranceDetailService
        self.detail_service = InsuranceDetailService(db)

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_claim(self, claim_id: int) -> Optional[InsuranceClaim]:
        result = await self.db.execute(
            select(InsuranceClaim).where(InsuranceClaim.id == claim_id)
        )
        return result.scalar_one_or_none()

    async def get_claims_by_invoice(self, invoice_id: int) -> List[InsuranceClaim]:
        result = await self.db.execute(
            select(InsuranceClaim).where(InsuranceClaim.invoice_id == invoice_id)
        )
        return result.scalars().all()

    async def get_claims_by_insurance_detail(self, insurance_detail_id: int) -> List[InsuranceClaim]:
        result = await self.db.execute(
            select(InsuranceClaim).where(InsuranceClaim.insurance_detail_id == insurance_detail_id)
        )
        return result.scalars().all()

    async def get_claims(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "submitted_date",
        descending: bool = True,
    ) -> PaginatedResponse[InsuranceClaim]:
        query = select(InsuranceClaim)
        if filters:
            if "status" in filters:
                query = query.where(InsuranceClaim.status == filters["status"])
            if "invoice_id" in filters:
                query = query.where(InsuranceClaim.invoice_id == filters["invoice_id"])
            if "submitted_date_from" in filters:
                query = query.where(InsuranceClaim.submitted_date >= filters["submitted_date_from"])
            if "submitted_date_to" in filters:
                query = query.where(InsuranceClaim.submitted_date <= filters["submitted_date_to"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Ordering
        order_col = getattr(InsuranceClaim, order_by, InsuranceClaim.submitted_date)
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

    async def create_claim(self, data: InsuranceClaimCreate) -> InsuranceClaim:
        # Validate insurance detail exists and is active
        detail = await self.detail_service.get_insurance_detail(data.insurance_detail_id)
        if not detail:
            raise InsuranceDetailNotFoundError(f"Insurance detail {data.insurance_detail_id} not found")
        if not self.detail_service.is_coverage_active(detail):
            raise InsuranceCoverageExpiredError("Insurance coverage is not active")
        # Validate invoice exists and is not fully paid
        invoice = await self.db.get(Invoice, data.invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {data.invoice_id} not found")
        if invoice.status == "paid":
            raise ValueError("Cannot create claim for already paid invoice")
        # Validate claim amount
        if data.approved_amount and data.approved_amount > invoice.total:
            raise ClaimAmountExceedsInvoiceError(
                f"Claim amount {data.approved_amount} exceeds invoice total {invoice.total}"
            )
        # Generate claim number if not provided
        claim_number = data.claim_number or await self._generate_claim_number()
        claim = InsuranceClaim(
            insurance_detail_id=data.insurance_detail_id,
            invoice_id=data.invoice_id,
            claim_number=claim_number,
            submitted_date=data.submitted_date or date.today(),
            approved_amount=data.approved_amount,
            status=data.status or "submitted",
            notes=data.notes,
        )
        self.db.add(claim)
        await self.db.commit()
        await self.db.refresh(claim)
        return claim

    async def update_claim(self, claim_id: int, data: InsuranceClaimUpdate) -> Optional[InsuranceClaim]:
        claim = await self.get_claim(claim_id)
        if not claim:
            raise InsuranceClaimNotFoundError(f"Claim {claim_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(claim, key, value)
        await self.db.commit()
        await self.db.refresh(claim)
        return claim

    async def delete_claim(self, claim_id: int) -> bool:
        claim = await self.get_claim(claim_id)
        if not claim:
            return False
        # Optional: prevent deletion if claim is already paid or approved
        if claim.status in ["approved", "paid"]:
            raise ValueError("Cannot delete claim that is already approved or paid")
        await self.db.delete(claim)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def _generate_claim_number(self) -> str:
        year = date.today().year
        stmt = select(func.max(InsuranceClaim.claim_number)).where(
            InsuranceClaim.claim_number.like(f"CLM-{year}%")
        )
        result = await self.db.execute(stmt)
        max_num = result.scalar()
        if max_num:
            seq = int(max_num.split("-")[1]) + 1
        else:
            seq = 1
        return f"CLM-{year}{seq:04d}"

    async def update_claim_status(self, claim_id: int, new_status: str) -> Optional[InsuranceClaim]:
        claim = await self.get_claim(claim_id)
        if not claim:
            raise InsuranceClaimNotFoundError(f"Claim {claim_id} not found")
        allowed_statuses = ["submitted", "approved", "denied", "paid"]
        if new_status not in allowed_statuses:
            raise ValueError(f"Invalid status. Allowed: {allowed_statuses}")
        claim.status = new_status
        await self.db.commit()
        await self.db.refresh(claim)
        return claim