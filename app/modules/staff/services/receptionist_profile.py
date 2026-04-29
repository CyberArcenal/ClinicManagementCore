# app/modules/staff/receptionist_profile_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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

    async def get_all_receptionists(self, skip: int = 0, limit: int = 100) -> List[ReceptionistProfile]:
        query = select(ReceptionistProfile).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

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