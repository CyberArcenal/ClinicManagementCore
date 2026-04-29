# app/modules/staff/pharmacist_profile_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


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

    async def get_all_pharmacists(self, skip: int = 0, limit: int = 100) -> List[PharmacistProfile]:
        query = select(PharmacistProfile).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

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