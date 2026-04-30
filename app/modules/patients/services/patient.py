# app/modules/patient/service.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.patients.models.patient import Patient
from app.modules.patients.schemas.base import PatientCreate, PatientUpdate
from app.modules.user.models import User


class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_patient(
        self, patient_id: int, load_user: bool = False
    ) -> Optional[Patient]:
        """Get patient by ID. Optionally load user relationship."""
        query = select(Patient).where(Patient.id == patient_id)
        if load_user:
            query = query.options(joinedload(Patient.user))
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_patient_by_user_id(
        self, user_id: int, load_user: bool = False
    ) -> Optional[Patient]:
        """Get patient record by linked user ID."""
        query = select(Patient).where(Patient.user_id == user_id)
        if load_user:
            query = query.options(joinedload(Patient.user))
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_patients(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "id",
        descending: bool = False,
    ) -> PaginatedResponse[Patient]:
        """
        List patients with pagination and optional filters.
        """
        query = select(Patient)

        if filters:
            if "gender" in filters:
                query = query.where(Patient.gender == filters["gender"])
            if "blood_type" in filters:
                query = query.where(Patient.blood_type == filters["blood_type"])
            if "date_of_birth_from" in filters:
                query = query.where(Patient.date_of_birth >= filters["date_of_birth_from"])
            if "date_of_birth_to" in filters:
                query = query.where(Patient.date_of_birth <= filters["date_of_birth_to"])
            if "user__full_name" in filters:
                query = query.join(Patient.user).where(
                    User.full_name.ilike(f"%{filters['user__full_name']}%")
                )
            if "user__email" in filters:
                query = query.join(Patient.user).where(
                    User.email.ilike(f"%{filters['user__email']}%")
                )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        if order_by.startswith("user__"):
            user_field = order_by.split("__")[1]
            query = query.join(Patient.user)
            order_column = getattr(User, user_field, User.id)
        else:
            order_column = getattr(Patient, order_by, Patient.id)
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

    async def create_patient(self, data: PatientCreate) -> Patient:
        """Create a new patient record. user_id must reference an existing User."""
        # Check if user exists
        if data.user_id:
            user = await self.db.get(User, data.user_id)
            if not user:
                raise EHRNotFoundError(f"User {data.user_id} not found")
            # Ensure user role is PATIENT? Could be set by auth service
        else:
            # If no user_id, we could optionally auto-create a User account? Not here.
            raise ValueError("user_id is required for patient creation")

        patient = Patient(
            user_id=data.user_id,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_type=data.blood_type,
            address=data.address,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            allergies=data.allergies,
            medical_history=data.medical_history,
        )
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def update_patient(
        self, patient_id: int, data: PatientUpdate
    ) -> Optional[Patient]:
        patient = await self.get_patient(patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {patient_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        # Prevent updating user_id accidentally (should not change user link)
        update_data.pop("user_id", None)
        for key, value in update_data.items():
            setattr(patient, key, value)

        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def delete_patient(self, patient_id: int, hard_delete: bool = False) -> bool:
        """
        Delete patient record.
        If hard_delete=True, permanently remove; else soft delete? 
        Our model doesn't have is_active; we'll just hard delete but check dependencies.
        """
        patient = await self.get_patient(patient_id, load_user=False)
        if not patient:
            return False

        # Optional: check for dependent records (appointments, prescriptions, etc.)
        # If any exist, raise error or set a flag. For now, allow deletion with cascade if DB configured.
        await self.db.delete(patient)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def search_patients(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Patient]:
        """
        Search patients by user's full_name, email, or patient's emergency contact.
        """
        query = (
            select(Patient)
            .join(Patient.user)
            .where(
                or_(
                    User.full_name.ilike(f"%{search_term}%"),
                    User.email.ilike(f"%{search_term}%"),
                    Patient.emergency_contact_name.ilike(f"%{search_term}%"),
                    Patient.emergency_contact_phone.ilike(f"%{search_term}%"),
                )
            )
        )
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_patient_summary(self, patient_id: int) -> Dict[str, Any]:
        """Return summary counts of related data: appointments, prescriptions, ehrs, lab results, invoices."""
        patient = await self.get_patient(patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {patient_id} not found")

        # Count appointments
        appt_count = await self.db.scalar(
            select(func.count()).select_from(patient.appointments)
        )
        # Count prescriptions
        presc_count = await self.db.scalar(
            select(func.count()).select_from(patient.prescriptions)
        )
        # Count EHR records
        ehr_count = await self.db.scalar(
            select(func.count()).select_from(patient.ehr_records)
        )
        # Count lab results
        lab_count = await self.db.scalar(
            select(func.count()).select_from(patient.lab_results)
        )
        # Count invoices
        invoice_count = await self.db.scalar(
            select(func.count()).select_from(patient.invoices)
        )
        # Count payments
        payment_count = await self.db.scalar(
            select(func.count()).select_from(patient.payments)
        )

        return {
            "patient_id": patient_id,
            "appointment_count": appt_count or 0,
            "prescription_count": presc_count or 0,
            "ehr_record_count": ehr_count or 0,
            "lab_result_count": lab_count or 0,
            "invoice_count": invoice_count or 0,
            "payment_count": payment_count or 0,
        }

    async def get_patients_birthday_today(self) -> List[Patient]:
        """Get list of patients whose birthday is today (month and day match)."""
        today = datetime.utcnow().date()
        query = select(Patient).where(
            func.extract("month", Patient.date_of_birth) == today.month,
            func.extract("day", Patient.date_of_birth) == today.day,
        )
        result = await self.db.execute(query)
        return result.scalars().all()