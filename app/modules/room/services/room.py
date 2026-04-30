# app/modules/room/room_service.py
import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.common.exceptions.room import RoomNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.room.models.room import Room
from app.modules.room.schemas.base import RoomCreate, RoomUpdate

class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_room(self, room_id: int) -> Optional[Room]:
        result = await self.db.execute(
            select(Room).where(Room.id == room_id)
        )
        return result.scalar_one_or_none()

    async def get_room_by_number(self, room_number: str) -> Optional[Room]:
        result = await self.db.execute(
            select(Room).where(Room.room_number == room_number)
        )
        return result.scalar_one_or_none()

    async def get_rooms(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "room_number",
        descending: bool = False,
    ) -> PaginatedResponse[Room]:
        query = select(Room)
        if filters:
            if "room_type" in filters:
                query = query.where(Room.room_type == filters["room_type"])
            if "is_available" in filters:
                query = query.where(Room.is_available == filters["is_available"])
            if "min_capacity" in filters:
                query = query.where(Room.capacity >= filters["min_capacity"])
            if "room_number_contains" in filters:
                query = query.where(Room.room_number.ilike(f"%{filters['room_number_contains']}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_col = getattr(Room, order_by, Room.room_number)
        if descending:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=page_size,
            pages=pages
        )

    async def create_room(self, data: RoomCreate) -> Room:
        # Check if room_number already exists
        existing = await self.get_room_by_number(data.room_number)
        if existing:
            raise ValueError(f"Room with number {data.room_number} already exists")

        room = Room(
            room_number=data.room_number,
            room_type=data.room_type,
            capacity=data.capacity,
            is_available=data.is_available,
            notes=data.notes,
        )
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def update_room(self, room_id: int, data: RoomUpdate) -> Optional[Room]:
        room = await self.get_room(room_id)
        if not room:
            raise RoomNotFoundError(f"Room {room_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        # If room_number is being changed, check uniqueness
        if "room_number" in update_data and update_data["room_number"] != room.room_number:
            existing = await self.get_room_by_number(update_data["room_number"])
            if existing:
                raise ValueError(f"Room number {update_data['room_number']} already exists")
        for key, value in update_data.items():
            setattr(room, key, value)

        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def delete_room(self, room_id: int) -> bool:
        room = await self.get_room(room_id)
        if not room:
            return False
        # Check if room has any appointments? If yes, might want to prevent deletion or just set is_available=False
        # For now, hard delete if no appointments (soft delete via is_available preferred)
        # We'll hard delete but you could change to soft delete by setting is_available=False
        await self.db.delete(room)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def set_availability(self, room_id: int, is_available: bool) -> Optional[Room]:
        room = await self.get_room(room_id)
        if not room:
            return None
        room.is_available = is_available
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def get_available_rooms(
        self, room_type: Optional[str] = None, min_capacity: int = 1
    ) -> List[Room]:
        query = select(Room).where(
            Room.is_available == True,
            Room.capacity >= min_capacity,
        )
        if room_type:
            query = query.where(Room.room_type == room_type)
        query = query.order_by(Room.room_number)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def check_room_availability(
        self, room_id: int, start_datetime: datetime, end_datetime: datetime
    ) -> bool:
        """
        Check if room is available during a time window.
        Assumes Appointment has a room_id field and times.
        """
        from app.modules.appointment.models.appointment import Appointment
        # Query overlapping appointments for this room
        overlapping = await self.db.execute(
            select(Appointment)
            .where(
                Appointment.room_id == room_id,
                Appointment.status.in_(["scheduled", "confirmed"]),
                Appointment.appointment_datetime < end_datetime,
                Appointment.appointment_datetime + func.make_interval(minutes=Appointment.duration_minutes) > start_datetime,
            )
        )
        return overlapping.first() is None