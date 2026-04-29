# app/modules/insurance/insurance_detail_service.py
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.billing import InvoiceNotFoundError
from app.common.exceptions.insurance import ClaimAmountExceedsInvoiceError, DuplicateInsuranceError, InsuranceCoverageExpiredError, InsuranceDetailNotFoundError
from app.modules.billing.models.base import Invoice
from app.modules.insurance.models.models import InsuranceClaim, InsuranceDetail
from app.modules.insurance.schemas.base import InsuranceClaimCreate, InsuranceClaimUpdate, InsuranceDetailCreate, InsuranceDetailUpdate
from app.modules.patients.models.models import Patient

class InsuranceDetailService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_insurance_detail(self, detail_id: int) -> Optional[InsuranceDetail]:
        result = await self.db.execute(
            select(InsuranceDetail).where(InsuranceDetail.id == detail_id)
        )
        return result.scalar_one_or_none()

    async def get_insurance_details_by_patient(
        self, patient_id: int, active_only: bool = True
    ) -> List[InsuranceDetail]:
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

    async def get_all_insurance_details(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[InsuranceDetail]:
        query = select(InsuranceDetail)
        if filters:
            if "provider_name" in filters:
                query = query.where(InsuranceDetail.provider_name.ilike(f"%{filters['provider_name']}%"))
            if "policy_number" in filters:
                query = query.where(InsuranceDetail.policy_number == filters["policy_number"])
            if "patient_id" in filters:
                query = query.where(InsuranceDetail.patient_id == filters["patient_id"])
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_insurance_detail(self, data: InsuranceDetailCreate) -> InsuranceDetail:
        # Validate patient exists
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
        detail = await self.get_insurance_detail(detail_id)
        if not detail:
            return False
        if detail.claims:
            raise ValueError("Cannot delete insurance detail with existing claims")
        await self.db.delete(detail)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def _check_overlapping_policies(
        self, patient_id: int, start_date: Optional[date], end_date: Optional[date]
    ) -> bool:
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

    @staticmethod
    def is_coverage_active(detail: InsuranceDetail) -> bool:
        today = date.today()
        if detail.coverage_start and detail.coverage_start > today:
            return False
        if detail.coverage_end and detail.coverage_end < today:
            return False
        return True