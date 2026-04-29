# app/modules/prescription/api/v1/endpoints/prescription_item.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.user.models import User


router = APIRouter()


@router.post("/", response_model=PrescriptionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription_item(
    data: PrescriptionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = PrescriptionItemService(db)
    try:
        item = await service.create_item(data)
        return item
    except PrescriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prescription/{prescription_id}", response_model=List[PrescriptionItemResponse])
async def get_items_by_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PrescriptionItemService(db)
    items = await service.get_items_by_prescription(prescription_id)
    return items


@router.get("/{item_id}", response_model=PrescriptionItemResponse)
async def get_prescription_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PrescriptionItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Prescription item not found")
    return item


@router.put("/{item_id}", response_model=PrescriptionItemResponse)
async def update_prescription_item(
    item_id: int,
    data: PrescriptionItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = PrescriptionItemService(db)
    try:
        item = await service.update_item(item_id, data)
        if not item:
            raise HTTPException(status_code=404, detail="Prescription item not found")
        return item
    except PrescriptionItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = PrescriptionItemService(db)
    deleted = await service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prescription item not found")
    return None