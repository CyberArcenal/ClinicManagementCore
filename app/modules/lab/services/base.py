# app/modules/lab/service.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.exceptions.lab import InvalidLabStatusTransitionError, LabTechNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.ehr.models.ehr import EHR
from app.modules.lab.models.lab import LabResult, LabStatus
from app.modules.lab.schemas.base import LabResultCreate, LabResultUpdate
from app.modules.patients.models.patient import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.labtech_profile import LabTechProfile

class LabService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_lab_result(
        self, lab_id: int, load_relations: bool = False
    ) -> Optional[LabResult]:
        query = select(LabResult).where(LabResult.id == lab_id)
        if load_relations:
            query = query.options(
                selectinload(LabResult.patient),
                selectinload(LabResult.requested_by),
                selectinload(LabResult.performed_by),
                selectinload(LabResult.ehr_visit),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_lab_results(
        self,
        filters: Dict[str, Any] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "requested_date",
        descending: bool = True,
    ) -> PaginatedResponse[LabResult]:
        """
        List lab results with pagination (page/page_size) and optional filters.
        """
        query = select(LabResult)
        if filters:
            if "patient_id" in filters:
                query = query.where(LabResult.patient_id == filters["patient_id"])
            if "doctor_id" in filters:
                query = query.where(LabResult.requested_by_id == filters["doctor_id"])
            if "status" in filters:
                query = query.where(LabResult.status == filters["status"])
            if "test_name_contains" in filters:
                query = query.where(LabResult.test_name.ilike(f"%{filters['test_name_contains']}%"))
            if "date_from" in filters:
                query = query.where(LabResult.requested_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(LabResult.requested_date <= filters["date_to"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_column = getattr(LabResult, order_by, LabResult.requested_date)
        if descending:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

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

    async def create_lab_request(self, data: LabResultCreate) -> LabResult:
        """Create a new lab request (status = PENDING)."""
        # Validate patient
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")
        # Validate requesting doctor
        doctor = await self.db.get(DoctorProfile, data.requested_by_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {data.requested_by_id} not found")
        # Validate optional EHR link
        if data.ehr_id:
            ehr = await self.db.get(EHR, data.ehr_id)
            if not ehr:
                raise EHRNotFoundError(f"EHR record {data.ehr_id} not found")

        lab = LabResult(
            patient_id=data.patient_id,
            ehr_id=data.ehr_id,
            test_name=data.test_name,
            requested_by_id=data.requested_by_id,
            performed_by_id=data.performed_by_id,
            requested_date=data.requested_date or datetime.utcnow(),
            completed_date=data.completed_date,
            status=LabStatus.PENDING,
            result_data=data.result_data,
            normal_range=data.normal_range,
            remarks=data.remarks,
        )
        self.db.add(lab)
        await self.db.commit()
        await self.db.refresh(lab)
        return lab

    async def update_lab_result(
        self, lab_id: int, data: LabResultUpdate
    ) -> Optional[LabResult]:
        lab = await self.get_lab_result(lab_id)
        if not lab:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(lab, key, value)

        await self.db.commit()
        await self.db.refresh(lab)
        return lab

    async def delete_lab_result(self, lab_id: int) -> bool:
        lab = await self.get_lab_result(lab_id)
        if not lab:
            return False
        # Optionally prevent deletion if status is in_progress or completed
        if lab.status in [LabStatus.IN_PROGRESS, LabStatus.COMPLETED]:
            raise ValueError("Cannot delete lab result that is in progress or completed")
        await self.db.delete(lab)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Status Workflow
    # ------------------------------------------------------------------
    async def start_lab_processing(
        self, lab_id: int, performed_by_id: int
    ) -> Optional[LabResult]:
        """Change status from PENDING to IN_PROGRESS."""
        lab = await self.get_lab_result(lab_id)
        if not lab:
            return None
        if lab.status != LabStatus.PENDING:
            raise InvalidLabStatusTransitionError(
                f"Cannot start processing: current status is {lab.status.value}"
            )
        # Validate lab tech exists
        lab_tech = await self.db.get(LabTechProfile, performed_by_id)
        if not lab_tech:
            raise LabTechNotFoundError(f"Lab tech {performed_by_id} not found")

        lab.status = LabStatus.IN_PROGRESS
        lab.performed_by_id = performed_by_id
        await self.db.commit()
        await self.db.refresh(lab)
        return lab

    async def complete_lab_result(
        self, lab_id: int, result_data: str, remarks: Optional[str] = None
    ) -> Optional[LabResult]:
        """Change status to COMPLETED and record results."""
        lab = await self.get_lab_result(lab_id)
        if not lab:
            return None
        if lab.status != LabStatus.IN_PROGRESS:
            raise InvalidLabStatusTransitionError(
                f"Cannot complete: current status is {lab.status.value} (expected IN_PROGRESS)"
            )

        lab.status = LabStatus.COMPLETED
        lab.result_data = result_data
        if remarks:
            lab.remarks = remarks
        lab.completed_date = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lab)
        return lab

    async def cancel_lab_request(self, lab_id: int, reason: str) -> Optional[LabResult]:
        """Cancel a lab request (can be done from PENDING or IN_PROGRESS)."""
        lab = await self.get_lab_result(lab_id)
        if not lab:
            return None
        if lab.status not in [LabStatus.PENDING, LabStatus.IN_PROGRESS]:
            raise InvalidLabStatusTransitionError(
                f"Cannot cancel: current status is {lab.status.value}"
            )

        lab.status = LabStatus.CANCELLED
        lab.remarks = f"CANCELLED: {reason}" if lab.remarks else f"CANCELLED: {reason}"
        await self.db.commit()
        await self.db.refresh(lab)
        return lab

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def get_patient_lab_history(
        self, patient_id: int, limit: int = 20
    ) -> List[LabResult]:
        patient = await self.db.get(Patient, patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {patient_id} not found")
        query = (
            select(LabResult)
            .where(LabResult.patient_id == patient_id)
            .order_by(LabResult.requested_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_pending_lab_requests(self) -> List[LabResult]:
        """Get all lab requests with status PENDING."""
        query = select(LabResult).where(LabResult.status == LabStatus.PENDING)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_lab_results_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[LabResult]:
        query = select(LabResult).where(
            LabResult.requested_date >= start_date,
            LabResult.requested_date <= end_date,
        )
        result = await self.db.execute(query)
        return result.scalars().all()