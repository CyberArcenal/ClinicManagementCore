# app/modules/staff/labtech_profile_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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

    async def get_all_lab_techs(self, skip: int = 0, limit: int = 100) -> List[LabTechProfile]:
        query = select(LabTechProfile).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_lab_tech(self, data: LabTechProfileCreate) -> LabTechProfile:
        user = await self.db.get(User, data.user_id)
        if not user:
            raise UserNotFoundError(f"User {data.user_id} not found")
        tech = LabTechProfile(user_id=data.user_id)
        self.db.add(tech)
        await self.db.commit()
        await self.db.refresh(tech)
        return tech

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