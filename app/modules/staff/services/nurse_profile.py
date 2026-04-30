# app/modules/staff/nurse_profile_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError, NurseNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.nurse_profile import NurseProfile
from app.modules.user.models.user import User
from app.modules.user.schemas.base import DoctorProfileCreate, DoctorProfileUpdate, NurseProfileUpdate



class NurseProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_nurse(self, nurse_id: int) -> Optional[NurseProfile]:
        result = await self.db.execute(
            select(NurseProfile).where(NurseProfile.id == nurse_id)
        )
        return result.scalar_one_or_none()

    async def get_nurse_by_user_id(self, user_id: int) -> Optional[NurseProfile]:
        result = await self.db.execute(
            select(NurseProfile).where(NurseProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_nurse_by_license(self, license_number: str) -> Optional[NurseProfile]:
        result = await self.db.execute(
            select(NurseProfile).where(NurseProfile.license_number == license_number)
        )
        return result.scalar_one_or_none()

    async def get_nurses(
        self,
        page: int = 1,
        page_size: int = 100,
    ) -> PaginatedResponse[NurseProfile]:
        query = select(NurseProfile)
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

    async def update_nurse(
        self, nurse_id: int, data: NurseProfileUpdate
    ) -> Optional[NurseProfile]:
        nurse = await self.get_nurse(nurse_id)
        if not nurse:
            raise NurseNotFoundError(f"Nurse {nurse_id} not found")
        if data.license_number is not None and data.license_number != nurse.license_number:
            existing = await self.get_nurse_by_license(data.license_number)
            if existing:
                raise DuplicateLicenseError(f"License {data.license_number} already assigned")
            nurse.license_number = data.license_number
        await self.db.commit()
        await self.db.refresh(nurse)
        return nurse

    async def delete_nurse(self, nurse_id: int) -> bool:
        nurse = await self.get_nurse(nurse_id)
        if not nurse:
            return False
        await self.db.delete(nurse)
        await self.db.commit()
        return True