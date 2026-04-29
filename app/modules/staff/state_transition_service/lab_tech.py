# app/modules/staff/state_transition_service/lab_tech.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.staff.models.labtech_profile import LabTechProfile
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User

logger = logging.getLogger(__name__)

class LabTechProfileTransition(BaseStateTransition[LabTechProfile]):

    def on_after_create(self, instance: LabTechProfile) -> None:
        logger.info(f"[LabTech] Created profile for user {instance.user_id}")
        self._send_welcome_notification(instance)

    def on_before_update(self, instance: LabTechProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing lab tech profile")

    def _send_welcome_notification(self, tech: LabTechProfile) -> None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == tech.user_id).first()
            if user:
                context = {"full_name": user.full_name}
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='staff_welcome_labtech',
                    context=context,
                    subject='Welcome to the Laboratory Team',
                    message="Your lab technician profile has been created."
                )
        except Exception as e:
            logger.exception(f"Failed to send welcome notification: {e}")
        finally:
            db.close()