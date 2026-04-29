# app/modules/treatment/treatment_service.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.exceptions.staff import NurseNotFoundError
from app.common.exceptions.treatment import TreatmentNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.ehr.models.base import EHR
from app.modules.patients.models.models import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.nurse_profile import NurseProfile
from app.modules.treatment.models.models import Treatment
from app.modules.treatment.schemas.treatment import TreatmentCreate, TreatmentUpdate



class TreatmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_treatment(self, treatment_id: int, load_relations: bool = False) -> Optional[Treatment]:
        query = select(Treatment).where(Treatment.id == treatment_id)
        if load_relations:
            query = query.options(
                selectinload(Treatment.patient),
                selectinload(Treatment.doctor),
                selectinload(Treatment.nurse),
                selectinload(Treatment.ehr_visit),
                selectinload(Treatment.billing_item),
            )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_treatments(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "performed_date",
        descending: bool = True,
    ) -> PaginatedResponse[Treatment]:
        query = select(Treatment)
        if filters:
            if "patient_id" in filters:
                query = query.where(Treatment.patient_id == filters["patient_id"])
            if "doctor_id" in filters:
                query = query.where(Treatment.doctor_id == filters["doctor_id"])
            if "nurse_id" in filters:
                query = query.where(Treatment.nurse_id == filters["nurse_id"])
            if "ehr_id" in filters:
                query = query.where(Treatment.ehr_id == filters["ehr_id"])
            if "treatment_type" in filters:
                query = query.where(Treatment.treatment_type == filters["treatment_type"])
            if "date_from" in filters:
                query = query.where(Treatment.performed_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(Treatment.performed_date <= filters["date_to"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_col = getattr(Treatment, order_by, Treatment.performed_date)
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

    async def create_treatment(self, data: TreatmentCreate) -> Treatment:
        # Validate patient
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")
        # Validate doctor
        doctor = await self.db.get(DoctorProfile, data.doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {data.doctor_id} not found")
        # Validate optional nurse
        if data.nurse_id:
            nurse = await self.db.get(NurseProfile, data.nurse_id)
            if not nurse:
                raise NurseNotFoundError(f"Nurse {data.nurse_id} not found")
        # Validate optional EHR
        if data.ehr_id:
            ehr = await self.db.get(EHR, data.ehr_id)
            if not ehr:
                raise EHRNotFoundError(f"EHR {data.ehr_id} not found")

        treatment = Treatment(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            ehr_id=data.ehr_id,
            nurse_id=data.nurse_id,
            treatment_type=data.treatment_type,
            procedure_name=data.procedure_name,
            performed_date=data.performed_date or datetime.utcnow(),
            notes=data.notes,
        )
        self.db.add(treatment)
        await self.db.commit()
        await self.db.refresh(treatment)
        return treatment

    async def update_treatment(
        self, treatment_id: int, data: TreatmentUpdate
    ) -> Optional[Treatment]:
        treatment = await self.get_treatment(treatment_id)
        if not treatment:
            raise TreatmentNotFoundError(f"Treatment {treatment_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        # Validate nurse_id if being changed
        if "nurse_id" in update_data and update_data["nurse_id"]:
            nurse = await self.db.get(NurseProfile, update_data["nurse_id"])
            if not nurse:
                raise NurseNotFoundError(f"Nurse {update_data['nurse_id']} not found")

        for key, value in update_data.items():
            setattr(treatment, key, value)

        await self.db.commit()
        await self.db.refresh(treatment)
        return treatment

    async def delete_treatment(self, treatment_id: int) -> bool:
        treatment = await self.get_treatment(treatment_id)
        if not treatment:
            return False
        # Optional: check if linked to billing item (should cascade or warn)
        if treatment.billing_item:
            raise ValueError("Cannot delete treatment that has an associated billing item")
        await self.db.delete(treatment)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def get_treatments_by_patient(
        self, patient_id: int, limit: int = 50
    ) -> List[Treatment]:
        query = (
            select(Treatment)
            .where(Treatment.patient_id == patient_id)
            .order_by(Treatment.performed_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_treatments_by_doctor(
        self, doctor_id: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None
    ) -> List[Treatment]:
        query = select(Treatment).where(Treatment.doctor_id == doctor_id)
        if from_date:
            query = query.where(Treatment.performed_date >= from_date)
        if to_date:
            query = query.where(Treatment.performed_date <= to_date)
        query = query.order_by(Treatment.performed_date.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_treatments_by_type(
        self, treatment_type: str, from_date: Optional[datetime] = None
    ) -> List[Treatment]:
        query = select(Treatment).where(Treatment.treatment_type == treatment_type)
        if from_date:
            query = query.where(Treatment.performed_date >= from_date)
        query = query.order_by(Treatment.performed_date.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_treatment_statistics(
        self,
        doctor_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        query = select(Treatment)
        if doctor_id:
            query = query.where(Treatment.doctor_id == doctor_id)
        if from_date:
            query = query.where(Treatment.performed_date >= from_date)
        if to_date:
            query = query.where(Treatment.performed_date <= to_date)

        result = await self.db.execute(query)
        treatments = result.scalars().all()

        total = len(treatments)
        by_type = {}
        for t in treatments:
            if t.treatment_type:
                by_type[t.treatment_type] = by_type.get(t.treatment_type, 0) + 1

        return {
            "total_treatments": total,
            "unique_patients": len(set(t.patient_id for t in treatments)),
            "treatments_by_type": by_type,
        }