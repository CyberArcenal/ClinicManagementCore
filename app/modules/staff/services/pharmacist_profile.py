# app/modules/staff/pharmacist_profile_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError, PharmacistNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.pharmacist_profile import PharmacistProfile
from app.modules.user.models.user import User
from app.modules.user.schemas.base import DoctorProfileCreate, DoctorProfileUpdate, PharmacistProfileCreate, PharmacistProfileUpdate



class PharmacistProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pharmacist(self, pharmacist_id: int) -> Optional[PharmacistProfile]:
        result = await self.db.execute(
            select(PharmacistProfile).where(PharmacistProfile.id == pharmacist_id)
        )
        return result.scalar_one_or_none()

    async def get_pharmacist_by_user_id(self, user_id: int) -> Optional[PharmacistProfile]:
        result = await self.db.execute(
            select(PharmacistProfile).where(PharmacistProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_pharmacists(
        self,
        page: int = 1,
        page_size: int = 100,
    ) -> PaginatedResponse[PharmacistProfile]:
        query = select(PharmacistProfile)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
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

    async def create_pharmacist(self, data: PharmacistProfileCreate) -> PharmacistProfile:
        user = await self.db.get(User, data.user_id)
        if not user:
            raise UserNotFoundError(f"User {data.user_id} not found")
        pharmacist = PharmacistProfile(user_id=data.user_id)
        self.db.add(pharmacist)
        await self.db.commit()
        await self.db.refresh(pharmacist)
        return pharmacist

    async def update_pharmacist(
        self, pharmacist_id: int, data: PharmacistProfileUpdate
    ) -> Optional[PharmacistProfile]:
        pharmacist = await self.get_pharmacist(pharmacist_id)
        if not pharmacist:
            raise PharmacistNotFoundError(f"Pharmacist {pharmacist_id} not found")
        await self.db.commit()
        return pharmacist

    async def delete_pharmacist(self, pharmacist_id: int) -> bool:
        pharmacist = await self.get_pharmacist(pharmacist_id)
        if not pharmacist:
            return False
        await self.db.delete(pharmacist)
        await self.db.commit()
        return True