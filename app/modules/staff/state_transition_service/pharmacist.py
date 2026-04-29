# app/modules/staff/state_transition_service/pharmacist.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.staff.models.pharmacist_profile import PharmacistProfile
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User

logger = logging.getLogger(__name__)

class PharmacistProfileTransition(BaseStateTransition[PharmacistProfile]):

    def on_after_create(self, instance: PharmacistProfile) -> None:
        logger.info(f"[Pharmacist] Created profile for user {instance.user_id}")
        self._send_welcome_notification(instance)

    def on_before_update(self, instance: PharmacistProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing pharmacist profile")

    def _send_welcome_notification(self, pharm: PharmacistProfile) -> None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == pharm.user_id).first()
            if user:
                context = {"full_name": user.full_name}
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='staff_welcome_pharmacist',
                    context=context,
                    subject='Welcome to the Pharmacy Team',
                    message="Your pharmacist profile has been created."
                )
        except Exception as e:
            logger.exception(f"Failed to send welcome notification: {e}")
        finally:
            db.close()