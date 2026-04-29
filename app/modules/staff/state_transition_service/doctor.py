# app/modules/staff/state_transition_service/doctor.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User

logger = logging.getLogger(__name__)

class DoctorProfileTransition(BaseStateTransition[DoctorProfile]):

    def on_after_create(self, instance: DoctorProfile) -> None:
        logger.info(f"[Doctor] Created profile for user {instance.user_id}")
        self._send_welcome_notification(instance)

    def on_before_update(self, instance: DoctorProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing doctor profile")
        # License uniqueness check would be done in service; here only extra validation

    def on_before_delete(self, instance: DoctorProfile) -> None:
        # Optional: check if doctor has appointments
        if instance.appointments:
            raise ValueError("Cannot delete doctor profile with existing appointments")

    def _send_welcome_notification(self, doctor: DoctorProfile) -> None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == doctor.user_id).first()
            if user:
                context = {
                    "full_name": user.full_name,
                    "specialization": doctor.specialization or "General",
                    "license_number": doctor.license_number
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='staff_welcome_doctor',
                    context=context,
                    subject='Welcome to the Medical Team',
                    message=f"Your doctor profile has been created. Specialization: {doctor.specialization}"
                )
        except Exception as e:
            logger.exception(f"Failed to send welcome notification to doctor {doctor.id}: {e}")
        finally:
            db.close()