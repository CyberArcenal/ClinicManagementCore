# app/modules/ehr/service.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.modules.ehr.models.base import EHR
from app.modules.ehr.schemas.base import EHRCreate, EHRUpdate
from app.modules.patients.models.models import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile
from sqlchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload


class EHRService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_ehr(
        self, ehr_id: int, load_relations: bool = False
    ) -> Optional[EHR]:
        """Get single EHR record by ID."""
        query = select(EHR).where(EHR.id == ehr_id)
        if load_relations:
            query = query.options(
                selectinload(EHR.patient),
                selectinload(EHR.doctor),
                selectinload(EHR.prescriptions),
                selectinload(EHR.lab_requests),
                selectinload(EHR.treatments),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_ehr_records(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "visit_date",
        descending: bool = True,
    ) -> List[EHR]:
        """
        List EHR records with filters.
        Filters can include: patient_id, doctor_id, date_from, date_to, diagnosis_contains.
        """
        query = select(EHR)

        if filters:
            if "patient_id" in filters:
                query = query.where(EHR.patient_id == filters["patient_id"])
            if "doctor_id" in filters:
                query = query.where(EHR.doctor_id == filters["doctor_id"])
            if "date_from" in filters:
                query = query.where(EHR.visit_date >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(EHR.visit_date <= filters["date_to"])
            if "diagnosis_contains" in filters:
                query = query.where(EHR.diagnosis.ilike(f"%{filters['diagnosis_contains']}%"))
            if "symptoms_contains" in filters:
                query = query.where(EHR.symptoms.ilike(f"%{filters['symptoms_contains']}%"))

        # Order by
        order_column = getattr(EHR, order_by, EHR.visit_date)
        if descending:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_ehr(self, data: EHRCreate) -> EHR:
        """Create a new EHR record."""
        # Validate patient and doctor exist
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")
        doctor = await self.db.get(DoctorProfile, data.doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {data.doctor_id} not found")

        ehr = EHR(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            visit_date=data.visit_date or datetime.utcnow(),
            diagnosis=data.diagnosis,
            treatment_plan=data.treatment_plan,
            clinical_notes=data.clinical_notes,
            vital_signs=data.vital_signs,
            symptoms=data.symptoms,
        )
        self.db.add(ehr)
        await self.db.commit()
        await self.db.refresh(ehr)
        return ehr

    async def update_ehr(self, ehr_id: int, data: EHRUpdate) -> Optional[EHR]:
        """Update an existing EHR record."""
        ehr = await self.get_ehr(ehr_id)
        if not ehr:
            raise EHRNotFoundError(f"EHR record {ehr_id} not found")

        # If doctor_id is being changed, validate new doctor exists
        if data.doctor_id is not None and data.doctor_id != ehr.doctor_id:
            doctor = await self.db.get(DoctorProfile, data.doctor_id)
            if not doctor:
                raise DoctorNotFoundError(f"Doctor {data.doctor_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ehr, key, value)

        await self.db.commit()
        await self.db.refresh(ehr)
        return ehr

    async def delete_ehr(self, ehr_id: int) -> bool:
        """Hard delete an EHR record."""
        ehr = await self.get_ehr(ehr_id)
        if not ehr:
            return False
        # Optional: check if there are dependent records (prescriptions, lab requests, treatments)
        # If yes, either cascade or prevent deletion.
        if ehr.prescriptions or ehr.lab_requests or ehr.treatments:
            raise ValueError(
                "Cannot delete EHR record with associated prescriptions, lab requests, or treatments. Delete those first."
            )
        await self.db.delete(ehr)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def get_patient_ehr_history(
        self, patient_id: int, limit: int = 20
    ) -> List[EHR]:
        """Get all EHR records for a specific patient, ordered by visit date desc."""
        patient = await self.db.get(Patient, patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {patient_id} not found")

        query = (
            select(EHR)
            .where(EHR.patient_id == patient_id)
            .order_by(EHR.visit_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_ehr_notes(
        self, search_term: str, skip: int = 0, limit: int = 50
    ) -> List[EHR]:
        """
        Search within clinical_notes, diagnosis, treatment_plan, symptoms.
        """
        query = select(EHR).where(
            or_(
                EHR.clinical_notes.ilike(f"%{search_term}%"),
                EHR.diagnosis.ilike(f"%{search_term}%"),
                EHR.treatment_plan.ilike(f"%{search_term}%"),
                EHR.symptoms.ilike(f"%{search_term}%"),
            )
        )
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_ehr_statistics(
        self, doctor_id: Optional[int] = None, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get simple statistics: total records, unique patients, common diagnoses (top 5).
        """
        query = select(EHR)
        if doctor_id:
            query = query.where(EHR.doctor_id == doctor_id)
        if date_from:
            query = query.where(EHR.visit_date >= date_from)
        if date_to:
            query = query.where(EHR.visit_date <= date_to)

        result = await self.db.execute(query)
        records = result.scalars().all()

        total_records = len(records)
        unique_patients = len(set(r.patient_id for r in records))

        # Simple diagnosis frequency
        diagnosis_counts = {}
        for r in records:
            if r.diagnosis:
                diag = r.diagnosis.strip()
                diagnosis_counts[diag] = diagnosis_counts.get(diag, 0) + 1
        top_diagnoses = sorted(diagnosis_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_records": total_records,
            "unique_patients": unique_patients,
            "top_diagnoses": [{"diagnosis": d, "count": c} for d, c in top_diagnoses],
        }