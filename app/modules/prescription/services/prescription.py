# app/modules/prescription/prescription_service.py
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.exceptions.prescription import PrescriptionNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.ehr.models.ehr import EHR
from app.modules.patients.models.patient import Patient
from app.modules.prescription.models.prescription import Prescription
from app.modules.prescription.schemas.base import PrescriptionCreate, PrescriptionUpdate
from app.modules.prescription.services.prescription_item import PrescriptionItemService
from app.modules.staff.models.doctor_profile import DoctorProfile

class PrescriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.item_service = PrescriptionItemService(db)

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_prescription(
        self, prescription_id: int, load_items: bool = False
    ) -> Optional[Prescription]:
        query = select(Prescription).where(Prescription.id == prescription_id)
        if load_items:
            query = query.options(selectinload(Prescription.items))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_prescriptions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "issue_date",
        descending: bool = True,
    ) -> PaginatedResponse[Prescription]:
        query = select(Prescription)
        if filters:
            if "patient_id" in filters:
                query = query.where(Prescription.patient_id == filters["patient_id"])
            if "doctor_id" in filters:
                query = query.where(Prescription.doctor_id == filters["doctor_id"])
            if "ehr_id" in filters:
                query = query.where(Prescription.ehr_id == filters["ehr_id"])
            if "is_dispensed" in filters:
                query = query.where(Prescription.is_dispensed == filters["is_dispensed"])
            if "date_from" in filters:
                query = query.where(Prescription.issue_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(Prescription.issue_date <= filters["date_to"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_col = getattr(Prescription, order_by, Prescription.issue_date)
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

    async def create_prescription(
        self, data: PrescriptionCreate
    ) -> Prescription:
        """Create prescription including its items."""
        # Validate patient
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")
        # Validate doctor
        doctor = await self.db.get(DoctorProfile, data.doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {data.doctor_id} not found")
        # Validate optional EHR
        if data.ehr_id:
            ehr = await self.db.get(EHR, data.ehr_id)
            if not ehr:
                raise EHRNotFoundError(f"EHR record {data.ehr_id} not found")

        prescription = Prescription(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            ehr_id=data.ehr_id,
            issue_date=data.issue_date or date.today(),
            notes=data.notes,
            is_dispensed=data.is_dispensed,
        )
        self.db.add(prescription)
        await self.db.commit()
        await self.db.refresh(prescription)

        # Add items if provided
        if data.items:
            for item_data in data.items:
                # Ensure item_data.prescription_id is set
                item_data.prescription_id = prescription.id
                await self.item_service.create_item(item_data)

        await self.db.refresh(prescription)
        return prescription

    async def update_prescription(
        self, prescription_id: int, data: PrescriptionUpdate
    ) -> Optional[Prescription]:
        prescription = await self.get_prescription(prescription_id)
        if not prescription:
            raise PrescriptionNotFoundError(f"Prescription {prescription_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        # Do not allow updating patient_id, doctor_id, ehr_id via this method? Up to you.
        for key, value in update_data.items():
            setattr(prescription, key, value)

        await self.db.commit()
        await self.db.refresh(prescription)
        return prescription

    async def delete_prescription(self, prescription_id: int) -> bool:
        prescription = await self.get_prescription(prescription_id)
        if not prescription:
            return False
        # Delete all items first (cascade should handle, but explicit for safety)
        for item in prescription.items:
            await self.db.delete(item)
        await self.db.delete(prescription)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def mark_as_dispensed(self, prescription_id: int) -> Optional[Prescription]:
        prescription = await self.get_prescription(prescription_id)
        if not prescription:
            return None
        prescription.is_dispensed = True
        await self.db.commit()
        await self.db.refresh(prescription)
        return prescription

    async def get_patient_prescriptions(
        self, patient_id: int, include_dispensed: bool = True
    ) -> List[Prescription]:
        query = select(Prescription).where(Prescription.patient_id == patient_id)
        if not include_dispensed:
            query = query.where(Prescription.is_dispensed == False)
        query = query.order_by(Prescription.issue_date.desc())
        result = await self.db.execute(query)
        return result.scalars().all()