# app/modules/staff/receptionist_profile_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError, ReceptionistNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.receptionist_profile import ReceptionistProfile
from app.modules.user.models.user import User
from app.modules.user.schemas.base import DoctorProfileCreate, DoctorProfileUpdate, ReceptionistProfileCreate, ReceptionistProfileUpdate


class ReceptionistProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_receptionist(self, receptionist_id: int) -> Optional[ReceptionistProfile]:
        result = await self.db.execute(
            select(ReceptionistProfile).where(ReceptionistProfile.id == receptionist_id)
        )
        return result.scalar_one_or_none()

    async def get_receptionist_by_user_id(self, user_id: int) -> Optional[ReceptionistProfile]:
        result = await self.db.execute(
            select(ReceptionistProfile).where(ReceptionistProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_receptionists(
        self,
        page: int = 1,
        page_size: int = 100,
    ) -> PaginatedResponse[ReceptionistProfile]:
        query = select(ReceptionistProfile)
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

    async def create_receptionist(self, data: ReceptionistProfileCreate) -> ReceptionistProfile:
        user = await self.db.get(User, data.user_id)
        if not user:
            raise UserNotFoundError(f"User {data.user_id} not found")
        receptionist = ReceptionistProfile(user_id=data.user_id)
        self.db.add(receptionist)
        await self.db.commit()
        await self.db.refresh(receptionist)
        return receptionist

    async def update_receptionist(
        self, receptionist_id: int, data: ReceptionistProfileUpdate
    ) -> Optional[ReceptionistProfile]:
        receptionist = await self.get_receptionist(receptionist_id)
        if not receptionist:
            raise ReceptionistNotFoundError(f"Receptionist {receptionist_id} not found")
        # No fields to update besides user_id? Usually none. Just return.
        await self.db.commit()
        return receptionist

    async def delete_receptionist(self, receptionist_id: int) -> bool:
        receptionist = await self.get_receptionist(receptionist_id)
        if not receptionist:
            return False
        await self.db.delete(receptionist)
        await self.db.commit()
        return True