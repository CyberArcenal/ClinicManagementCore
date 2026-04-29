# app/modules/staff/state_transition_service/nurse.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.staff.models.nurse_profile import NurseProfile
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User

logger = logging.getLogger(__name__)

class NurseProfileTransition(BaseStateTransition[NurseProfile]):

    def on_after_create(self, instance: NurseProfile) -> None:
        logger.info(f"[Nurse] Created profile for user {instance.user_id}")
        self._send_welcome_notification(instance)

    def on_before_update(self, instance: NurseProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing nurse profile")

    def _send_welcome_notification(self, nurse: NurseProfile) -> None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == nurse.user_id).first()
            if user:
                context = {"full_name": user.full_name, "license_number": nurse.license_number}
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='staff_welcome_nurse',
                    context=context,
                    subject='Welcome to the Nursing Team',
                    message="Your nurse profile has been created."
                )
        except Exception as e:
            logger.exception(f"Failed to send welcome notification to nurse {nurse.id}: {e}")
        finally:
            db.close()