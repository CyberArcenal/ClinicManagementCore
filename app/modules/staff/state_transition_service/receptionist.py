# app/modules/staff/state_transition_service/receptionist.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.staff.models.receptionist_profile import ReceptionistProfile
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User

logger = logging.getLogger(__name__)

class ReceptionistProfileTransition(BaseStateTransition[ReceptionistProfile]):

    def on_after_create(self, instance: ReceptionistProfile) -> None:
        logger.info(f"[Receptionist] Created profile for user {instance.user_id}")
        self._send_welcome_notification(instance)

    def on_before_update(self, instance: ReceptionistProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing receptionist profile")

    def _send_welcome_notification(self, rec: ReceptionistProfile) -> None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == rec.user_id).first()
            if user:
                context = {"full_name": user.full_name}
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='staff_welcome_receptionist',
                    context=context,
                    subject='Welcome to the Front Desk Team',
                    message="Your receptionist profile has been created."
                )
        except Exception as e:
            logger.exception(f"Failed to send welcome notification: {e}")
        finally:
            db.close()