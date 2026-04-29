# app/modules/staff/doctor_profile_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.user.models.base import User
from app.modules.user.schemas.base import DoctorProfileCreate, DoctorProfileUpdate


class DoctorProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_doctor(self, doctor_id: int, load_user: bool = False) -> Optional[DoctorProfile]:
        query = select(DoctorProfile).where(DoctorProfile.id == doctor_id)
        if load_user:
            query = query.options(selectinload(DoctorProfile.user))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_doctor_by_user_id(self, user_id: int) -> Optional[DoctorProfile]:
        result = await self.db.execute(
            select(DoctorProfile).where(DoctorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_doctor_by_license(self, license_number: str) -> Optional[DoctorProfile]:
        result = await self.db.execute(
            select(DoctorProfile).where(DoctorProfile.license_number == license_number)
        )
        return result.scalar_one_or_none()

    async def get_doctors(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "id",
        descending: bool = False,
    ) -> PaginatedResponse[DoctorProfile]:
        query = select(DoctorProfile)
        if filters:
            if "specialization" in filters:
                query = query.where(DoctorProfile.specialization == filters["specialization"])
            if "min_experience" in filters:
                query = query.where(DoctorProfile.years_of_experience >= filters["min_experience"])
            if "user__full_name" in filters:
                query = query.join(DoctorProfile.user).where(
                    User.full_name.ilike(f"%{filters['user__full_name']}%")
                )
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        order_col = getattr(DoctorProfile, order_by, DoctorProfile.id)
        if descending:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

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

    async def create_doctor(self, data: DoctorProfileCreate) -> DoctorProfile:
        # Validate user exists
        user = await self.db.get(User, data.user_id)
        if not user:
            raise UserNotFoundError(f"User {data.user_id} not found")
        # Check license uniqueness
        existing = await self.get_doctor_by_license(data.license_number)
        if existing:
            raise DuplicateLicenseError(f"License {data.license_number} already assigned")
        doctor = DoctorProfile(
            user_id=data.user_id,
            specialization=data.specialization,
            license_number=data.license_number,
            years_of_experience=data.years_of_experience,
        )
        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor

    async def update_doctor(
        self, doctor_id: int, data: DoctorProfileUpdate
    ) -> Optional[DoctorProfile]:
        doctor = await self.get_doctor(doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {doctor_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        # Check license uniqueness if changed
        if "license_number" in update_data and update_data["license_number"] != doctor.license_number:
            existing = await self.get_doctor_by_license(update_data["license_number"])
            if existing:
                raise DuplicateLicenseError(f"License {update_data['license_number']} already assigned")
        for key, value in update_data.items():
            setattr(doctor, key, value)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor

    async def delete_doctor(self, doctor_id: int) -> bool:
        doctor = await self.get_doctor(doctor_id)
        if not doctor:
            return False
        await self.db.delete(doctor)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def get_doctors_by_specialization(self, specialization: str) -> List[DoctorProfile]:
        query = select(DoctorProfile).where(DoctorProfile.specialization == specialization)
        result = await self.db.execute(query)
        return result.scalars().all()