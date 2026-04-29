# app/modules/room/api/v1/endpoints/room.py
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Create a new room (consultation, treatment, exam, ward).
    """
    service = RoomService(db)
    try:
        room = await service.create_room(data)
        return room
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[RoomResponse])
async def list_rooms(
    room_type: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    min_capacity: Optional[int] = Query(None),
    room_number_contains: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if room_type:
        filters["room_type"] = room_type
    if is_available is not None:
        filters["is_available"] = is_available
    if min_capacity:
        filters["min_capacity"] = min_capacity
    if room_number_contains:
        filters["room_number_contains"] = room_number_contains

    service = RoomService(db)
    rooms = await service.get_rooms(filters=filters, skip=skip, limit=limit)
    return rooms


@router.get("/available", response_model=List[RoomResponse])
async def get_available_rooms(
    room_type: Optional[str] = Query(None),
    min_capacity: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(db)
    rooms = await service.get_available_rooms(room_type=room_type, min_capacity=min_capacity)
    return rooms


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(db)
    room = await service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = RoomService(db)
    try:
        room = await service.update_room(room_id, data)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return room
    except (RoomNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{room_id}/availability", response_model=RoomResponse)
async def set_room_availability(
    room_id: int,
    is_available: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = RoomService(db)
    room = await service.set_availability(room_id, is_available)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = RoomService(db)
    deleted = await service.delete_room(room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Room not found")
    return None


@router.get("/{room_id}/check-availability")
async def check_room_availability(
    room_id: int,
    start_datetime: datetime = Query(..., description="Start of appointment"),
    end_datetime: datetime = Query(..., description="End of appointment"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(db)
    available = await service.check_room_availability(room_id, start_datetime, end_datetime)
    return {"available": available}