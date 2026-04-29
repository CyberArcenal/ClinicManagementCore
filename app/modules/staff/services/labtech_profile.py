# app/modules/staff/labtech_profile_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.lab import LabTechNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.labtech_profile import LabTechProfile
from app.modules.user.models.base import User
from app.modules.user.schemas.base import (
    DoctorProfileCreate,
    DoctorProfileUpdate,
    LabTechProfileUpdate,
)


class LabTechProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lab_tech(self, tech_id: int) -> Optional[LabTechProfile]:
        result = await self.db.execute(
            select(LabTechProfile).where(LabTechProfile.id == tech_id)
        )
        return result.scalar_one_or_none()

    async def get_lab_tech_by_user_id(self, user_id: int) -> Optional[LabTechProfile]:
        result = await self.db.execute(
            select(LabTechProfile).where(LabTechProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_lab_techs(
        self,
        page: int = 1,
        page_size: int = 100,
    ) -> PaginatedResponse[LabTechProfile]:
        query = select(LabTechProfile)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()
        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(
            items=items, total=total, page=page, size=page_size, pages=pages
        )

    async def update_lab_tech(
        self, tech_id: int, data: LabTechProfileUpdate
    ) -> Optional[LabTechProfile]:
        tech = await self.get_lab_tech(tech_id)
        if not tech:
            raise LabTechNotFoundError(f"LabTech {tech_id} not found")
        # No updatable fields
        await self.db.commit()
        return tech

    async def delete_lab_tech(self, tech_id: int) -> bool:
        tech = await self.get_lab_tech(tech_id)
        if not tech:
            return False
        await self.db.delete(tech)
        await self.db.commit()
        return True
