# app/modules/prescription/prescription_item_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.common.exceptions.prescription import PrescriptionItemNotFoundError, PrescriptionNotFoundError
from app.modules.prescription.models import PrescriptionItem
from app.modules.prescription.schemas import (
    PrescriptionItemCreate,
    PrescriptionItemUpdate,
)



class PrescriptionItemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_item(self, item_id: int) -> Optional[PrescriptionItem]:
        result = await self.db.execute(
            select(PrescriptionItem).where(PrescriptionItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_items_by_prescription(
        self, prescription_id: int
    ) -> List[PrescriptionItem]:
        result = await self.db.execute(
            select(PrescriptionItem)
            .where(PrescriptionItem.prescription_id == prescription_id)
            .order_by(PrescriptionItem.id)
        )
        return result.scalars().all()

    async def create_item(self, data: PrescriptionItemCreate) -> PrescriptionItem:
        # Ensure prescription exists
        from app.modules.prescription.models import Prescription
        pres = await self.db.get(Prescription, data.prescription_id)
        if not pres:
            raise PrescriptionNotFoundError(f"Prescription {data.prescription_id} not found")

        item = PrescriptionItem(
            prescription_id=data.prescription_id,
            drug_name=data.drug_name,
            dosage=data.dosage,
            frequency=data.frequency,
            duration_days=data.duration_days,
            instructions=data.instructions,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_item(
        self, item_id: int, data: PrescriptionItemUpdate
    ) -> Optional[PrescriptionItem]:
        item = await self.get_item(item_id)
        if not item:
            raise PrescriptionItemNotFoundError(f"Item {item_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item_id: int) -> bool:
        item = await self.get_item(item_id)
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def delete_all_items_for_prescription(self, prescription_id: int) -> int:
        items = await self.get_items_by_prescription(prescription_id)
        count = len(items)
        for item in items:
            await self.db.delete(item)
        await self.db.commit()
        return count