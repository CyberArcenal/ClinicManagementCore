# app/schemas/room.py
from typing import Optional
from pydantic import BaseModel
from app.common.schema.base import BaseSchema, TimestampSchema
class RoomBase(BaseSchema):
    room_number: str
    room_type: Optional[str] = None
    capacity: int = 1
    is_available: bool = True
    notes: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseSchema):
    room_type: Optional[str] = None
    capacity: Optional[int] = None
    is_available: Optional[bool] = None
    notes: Optional[str] = None

class RoomResponse(TimestampSchema, RoomBase):
    pass