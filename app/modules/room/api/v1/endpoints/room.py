from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.room import RoomNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.room.schemas.base import RoomCreate, RoomResponse, RoomUpdate
from app.modules.room.services.room import RoomService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[RoomResponse]:
    service = RoomService(db)
    try:
        room = await service.create_room(data)
        return success_response(data=room, message="Room created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_rooms(
    room_type: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    min_capacity: Optional[int] = Query(None),
    room_number_contains: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[RoomResponse]]:
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
    paginated = await service.get_rooms(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return success_response(data=paginated, message="Rooms retrieved")


@router.get("/available")
async def get_available_rooms(
    room_type: Optional[str] = Query(None),
    min_capacity: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[RoomResponse]]:
    service = RoomService(db)
    rooms = await service.get_available_rooms(room_type=room_type, min_capacity=min_capacity)
    return success_response(data=rooms, message="Available rooms retrieved")


@router.get("/{room_id}")
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[RoomResponse]:
    service = RoomService(db)
    room = await service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return success_response(data=room, message="Room retrieved")


@router.put("/{room_id}")
async def update_room(
    room_id: int,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[RoomResponse]:
    service = RoomService(db)
    try:
        room = await service.update_room(room_id, data)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return success_response(data=room, message="Room updated")
    except (RoomNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{room_id}/availability")
async def set_room_availability(
    room_id: int,
    is_available: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[RoomResponse]:
    service = RoomService(db)
    room = await service.set_availability(room_id, is_available)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return success_response(data=room, message=f"Room availability set to {is_available}")


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = RoomService(db)
    deleted = await service.delete_room(room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Room not found")
    return None


@router.get("/{room_id}/check-availability")
async def check_room_availability(
    room_id: int,
    start_datetime: datetime = Query(...),
    end_datetime: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict]:
    service = RoomService(db)
    available = await service.check_room_availability(room_id, start_datetime, end_datetime)
    return success_response(data={"available": available}, message="Room availability checked")