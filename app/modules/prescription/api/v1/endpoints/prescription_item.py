from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.prescription import PrescriptionItemNotFoundError, PrescriptionNotFoundError
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.prescription.schemas.base import (
    PrescriptionItemCreate,
    PrescriptionItemResponse,
    PrescriptionItemUpdate,
)
from app.modules.prescription.services.prescription_item import PrescriptionItemService
from app.modules.user.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_prescription_item(
    data: PrescriptionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> SuccessResponse[PrescriptionItemResponse]:
    service = PrescriptionItemService(db)
    try:
        item = await service.create_item(data)
        return success_response(data=item, message="Prescription item created")
    except PrescriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prescription/{prescription_id}")
async def get_items_by_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[List[PrescriptionItemResponse]]:
    service = PrescriptionItemService(db)
    items = await service.get_items_by_prescription(prescription_id)
    return success_response(data=items, message="Prescription items retrieved")


@router.get("/{item_id}")
async def get_prescription_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PrescriptionItemResponse]:
    service = PrescriptionItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Prescription item not found")
    return success_response(data=item, message="Prescription item retrieved")


@router.put("/{item_id}")
async def update_prescription_item(
    item_id: int,
    data: PrescriptionItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> SuccessResponse[PrescriptionItemResponse]:
    service = PrescriptionItemService(db)
    try:
        item = await service.update_item(item_id, data)
        if not item:
            raise HTTPException(status_code=404, detail="Prescription item not found")
        return success_response(data=item, message="Prescription item updated")
    except PrescriptionItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> None:
    service = PrescriptionItemService(db)
    deleted = await service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prescription item not found")
    return None