from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.room.models import Room

class RoomTransition(BaseStateTransition[Room]):

    def on_after_create(self, instance: Room) -> None:
        print(f"[Room] Created: {instance.room_number} (type: {instance.room_type})")

    def on_before_update(self, instance: Room, changes: Dict[str, Any]) -> None:
        # Prevent changing room_number after creation
        if "room_number" in changes:
            raise ValueError("Cannot change room number of existing room")

    def on_after_update(self, instance: Room, changes: Dict[str, Any]) -> None:
        if "is_available" in changes:
            status = "available" if instance.is_available else "unavailable"
            print(f"[Room] Room {instance.room_number} is now {status}")
            # TODO: notify booking system about availability change

    def on_before_delete(self, instance: Room) -> None:
        # Check if room has upcoming appointments before deletion
        if instance.appointments:
            # Assuming room has appointments relationship
            upcoming = [apt for apt in instance.appointments if apt.status in ["scheduled", "confirmed"]]
            if upcoming:
                raise ValueError(f"Cannot delete room with {len(upcoming)} upcoming appointments")