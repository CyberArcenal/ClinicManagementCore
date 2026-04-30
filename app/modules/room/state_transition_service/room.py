# app/modules/room/state_transition_service/room.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.room.models.room import Room
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User  # assuming User model is accessible

logger = logging.getLogger(__name__)

class RoomTransition(BaseStateTransition[Room]):

    def on_after_create(self, instance: Room) -> None:
        logger.info(f"[Room] Created: {instance.room_number} (type: {instance.room_type})")
        # Optionally notify admins about new room (can be omitted if not needed)

    def on_before_update(self, instance: Room, changes: Dict[str, Any]) -> None:
        if "room_number" in changes:
            raise ValueError("Cannot change room number of existing room")

    def on_after_update(self, instance: Room, changes: Dict[str, Any]) -> None:
        if "is_available" in changes:
            status = "available" if instance.is_available else "unavailable"
            logger.info(f"[Room] Room {instance.room_number} is now {status}")
            self._notify_availability_change(instance)

    def on_before_delete(self, instance: Room) -> None:
        if instance.appointments:
            upcoming = [apt for apt in instance.appointments if apt.status in ["scheduled", "confirmed"]]
            if upcoming:
                raise ValueError(f"Cannot delete room with {len(upcoming)} upcoming appointments")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_availability_change(self, room: Room) -> None:
        """Notify receptionists and admins about room availability change."""
        db = SessionLocal()
        try:
            # Fetch all users with role 'receptionist' or 'admin'
            recipients = db.query(User).filter(User.role.in_(['receptionist', 'admin'])).all()
            context = {
                "room_number": room.room_number,
                "room_type": room.room_type or "General",
                "status": "available" if room.is_available else "unavailable",
                "capacity": room.capacity,
                "notes": room.notes or ""
            }
            for user in recipients:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='room_availability_changed',
                    context=context,
                    subject='Room Availability Update',
                    message=f"Room {room.room_number} is now {'available' if room.is_available else 'unavailable'}."
                )
            logger.info(f"Notified {len(recipients)} staff about room {room.room_number} availability change")
        except Exception as e:
            logger.exception(f"Failed to send room availability notification: {e}")
        finally:
            db.close()