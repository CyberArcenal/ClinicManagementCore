# app/modules/insurance/service.py
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import InvoiceNotFoundError
from app.common.exceptions.insurance import ClaimAmountExceedsInvoiceError, DuplicateInsuranceError, InsuranceCoverageExpiredError, InsuranceDetailNotFoundError
from app.modules.billing.models.base import Invoice
from app.modules.insurance.models.models import InsuranceClaim, InsuranceDetail
from app.modules.insurance.schemas.base import InsuranceClaimCreate, InsuranceClaimUpdate, InsuranceDetailCreate, InsuranceDetailUpdate
from app.modules.patients.models.models import Patient

class InsuranceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # InsuranceDetail CRUD + Utilities
    # ------------------------------------------------------------------
    async def get_insurance_detail(
        self, detail_id: int, load_relations: bool = False
    ) -> Optional[InsuranceDetail]:
        query = select(InsuranceDetail).where(InsuranceDetail.id == detail_id)
        if load_relations:
            query = query.options(
                selectinload(InsuranceDetail.patient),
                selectinload(InsuranceDetail.claims),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_patient_insurance_details(
        self, patient_id: int, active_only: bool = True
    ) -> List[InsuranceDetail]:
        """Get all insurance details for a patient, optionally only active (within coverage dates)."""
        patient = await self.db.get(Patient, patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {patient_id} not found")

        query = select(InsuranceDetail).where(InsuranceDetail.patient_id == patient_id)
        if active_only:
            today = date.today()
            query = query.where(
                or_(
                    InsuranceDetail.coverage_end.is_(None),
                    InsuranceDetail.coverage_end >= today,
                ),
                InsuranceDetail.coverage_start <= today,
            )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_insurance_detail(self, data: InsuranceDetailCreate) -> InsuranceDetail:
        """Create a new insurance detail for a patient."""
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")

        # Check for overlapping active policies
        overlapping = await self._check_overlapping_policies(
            patient_id=data.patient_id,
            start_date=data.coverage_start,
            end_date=data.coverage_end,
        )
        if overlapping:
            raise DuplicateInsuranceError("Patient already has active insurance for this period")

        detail = InsuranceDetail(
            patient_id=data.patient_id,
            provider_name=data.provider_name,
            policy_number=data.policy_number,
            group_number=data.group_number,
            coverage_start=data.coverage_start,
            coverage_end=data.coverage_end,
            copay_percent=data.copay_percent,
        )
        self.db.add(detail)
        await self.db.commit()
        await self.db.refresh(detail)
        return detail

    async def update_insurance_detail(
        self, detail_id: int, data: InsuranceDetailUpdate
    ) -> Optional[InsuranceDetail]:
        detail = await self.get_insurance_detail(detail_id)
        if not detail:
            raise InsuranceDetailNotFoundError(f"Insurance detail {detail_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(detail, key, value)

        await self.db.commit()
        await self.db.refresh(detail)
        return detail

    async def delete_insurance_detail(self, detail_id: int) -> bool:
        """Delete insurance detail if no claims associated."""
        detail = await self.get_insurance_detail(detail_id)
        if not detail:
            return False
        if detail.claims:
            raise ValueError("Cannot delete insurance detail with existing claims")
        await self.db.delete(detail)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # InsuranceClaim CRUD + Utilities
    # ------------------------------------------------------------------
    async def get_claim(
        self, claim_id: int, load_relations: bool = False
    ) -> Optional[InsuranceClaim]:
        query = select(InsuranceClaim).where(InsuranceClaim.id == claim_id)
        if load_relations:
            query = query.options(
                selectinload(InsuranceClaim.insurance_detail),
                selectinload(InsuranceClaim.invoice),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_claims(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "submitted_date",
        descending: bool = True,
    ) -> List[InsuranceClaim]:
        query = select(InsuranceClaim)
        if filters:
            if "insurance_detail_id" in filters:
                query = query.where(InsuranceClaim.insurance_detail_id == filters["insurance_detail_id"])
            if "invoice_id" in filters:
                query = query.where(InsuranceClaim.invoice_id == filters["invoice_id"])
            if "status" in filters:
                query = query.where(InsuranceClaim.status == filters["status"])
            if "submitted_date_from" in filters:
                query = query.where(InsuranceClaim.submitted_date >= filters["submitted_date_from"])
            if "submitted_date_to" in filters:
                query = query.where(InsuranceClaim.submitted_date <= filters["submitted_date_to"])

        order_column = getattr(InsuranceClaim, order_by, InsuranceClaim.submitted_date)
        if descending:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_claim(self, data: InsuranceClaimCreate) -> InsuranceClaim:
        """Create a new insurance claim."""
        # Validate insurance detail exists and is active
        detail = await self.get_insurance_detail(data.insurance_detail_id)
        if not detail:
            raise InsuranceDetailNotFoundError(f"Insurance detail {data.insurance_detail_id} not found")
        if not self._is_coverage_active(detail):
            raise InsuranceCoverageExpiredError("Insurance coverage is not active")

        # Validate invoice exists and is not fully paid
        invoice = await self.db.get(Invoice, data.invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {data.invoice_id} not found")
        if invoice.status == "paid":
            raise ValueError("Cannot create claim for already paid invoice")

        # Validate claim amount (must not exceed invoice total)
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
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(claim, key, value)

        await self.db.commit()
        await self.db.refresh(claim)
        return claim

    async def delete_claim(self, claim_id: int) -> bool:
        """Soft delete? We'll just hard delete if no payments linked."""
        claim = await self.get_claim(claim_id)
        if not claim:
            return False
        # Check if claim is already paid or partially paid? Optional.
        await self.db.delete(claim)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Business Utilities
    # ------------------------------------------------------------------
    async def calculate_patient_responsibility(
        self, invoice_id: int, patient_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Given an invoice, determine how much insurance will cover and patient's copay.
        Returns: {
            "invoice_total": Decimal,
            "insurance_covers": Decimal,
            "patient_pays": Decimal,
            "copay_percent_applied": Decimal,
            "insurance_detail_id": int or None
        }
        """
        invoice = await self.db.get(Invoice, invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")

        patient_id = patient_id or invoice.patient_id
        active_details = await self.get_patient_insurance_details(patient_id, active_only=True)
        if not active_details:
            return {
                "invoice_total": invoice.total,
                "insurance_covers": Decimal("0.00"),
                "patient_pays": invoice.total,
                "copay_percent_applied": Decimal("0.00"),
                "insurance_detail_id": None,
            }

        # Use the first active insurance (could prioritize by rules)
        primary_insurance = active_details[0]
        copay_percent = primary_insurance.copay_percent or Decimal("0.00")
        insurance_covers = (invoice.total * copay_percent) / Decimal("100.00")
        patient_pays = invoice.total - insurance_covers

        return {
            "invoice_total": invoice.total,
            "insurance_covers": insurance_covers,
            "patient_pays": patient_pays,
            "copay_percent_applied": copay_percent,
            "insurance_detail_id": primary_insurance.id,
        }

    async def submit_claim_for_invoice(
        self, invoice_id: int, insurance_detail_id: Optional[int] = None
    ) -> InsuranceClaim:
        """
        Automatically create a claim for an invoice using the patient's active insurance.
        """
        invoice = await self.db.get(Invoice, invoice_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")

        if not insurance_detail_id:
            calc = await self.calculate_patient_responsibility(invoice_id)
            insurance_detail_id = calc["insurance_detail_id"]
            if not insurance_detail_id:
                raise ValueError("No active insurance found for this patient")

        claim_data = InsuranceClaimCreate(
            insurance_detail_id=insurance_detail_id,
            invoice_id=invoice_id,
            approved_amount=invoice.total,  # initial claim for full amount, later adjust
            status="submitted",
        )
        return await self.create_claim(claim_data)

    # ------------------------------------------------------------------
    # Internal Helper Methods
    # ------------------------------------------------------------------
    async def _check_overlapping_policies(
        self, patient_id: int, start_date: Optional[date], end_date: Optional[date]
    ) -> bool:
        """Check if there's already an active insurance for the same period."""
        query = select(InsuranceDetail).where(InsuranceDetail.patient_id == patient_id)
        if start_date:
            query = query.where(
                or_(
                    InsuranceDetail.coverage_end.is_(None),
                    InsuranceDetail.coverage_end >= start_date,
                )
            )
        if end_date:
            query = query.where(
                or_(
                    InsuranceDetail.coverage_start.is_(None),
                    InsuranceDetail.coverage_start <= end_date,
                )
            )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def _generate_claim_number(self) -> str:
        """Generate unique claim number, e.g., CLM-20240001"""
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

    @staticmethod
    def _is_coverage_active(detail: InsuranceDetail) -> bool:
        today = date.today()
        if detail.coverage_start and detail.coverage_start > today:
            return False
        if detail.coverage_end and detail.coverage_end < today:
            return False
        return True