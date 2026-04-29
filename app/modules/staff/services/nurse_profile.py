# app/modules/staff/nurse_profile_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.user.models import User


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

    async def get_nurses(self, skip: int = 0, limit: int = 100) -> List[NurseProfile]:
        query = select(NurseProfile).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_nurse(self, data: NurseProfileCreate) -> NurseProfile:
        user = await self.db.get(User, data.user_id)
        if not user:
            raise UserNotFoundError(f"User {data.user_id} not found")
        existing = await self.get_nurse_by_license(data.license_number)
        if existing:
            raise DuplicateLicenseError(f"License {data.license_number} already assigned")
        nurse = NurseProfile(
            user_id=data.user_id,
            license_number=data.license_number,
        )
        self.db.add(nurse)
        await self.db.commit()
        await self.db.refresh(nurse)
        return nurse

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