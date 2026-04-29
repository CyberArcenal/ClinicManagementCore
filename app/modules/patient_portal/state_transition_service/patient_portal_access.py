# app/modules/patient_portal/state_transition_service/patient_portal_access.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.patient_portal.models.models import PatientPortalAccess
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.patients.models.models import Patient

logger = logging.getLogger(__name__)

class PatientPortalAccessTransition(BaseStateTransition[PatientPortalAccess]):

    def on_after_create(self, instance: PatientPortalAccess) -> None:
        logger.info(f"[PatientPortalAccess] Login recorded for patient {instance.patient_id} from IP {instance.ip_address}")
        
        # Send login alert notification to patient
        self._send_login_alert(instance)

    def on_before_update(self, instance: PatientPortalAccess, changes: Dict[str, Any]) -> None:
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing access record")

    def on_after_update(self, instance: PatientPortalAccess, changes: Dict[str, Any]) -> None:
        if "logout_time" in changes and changes["logout_time"] is not None:
            logger.info(f"[PatientPortalAccess] Logout recorded for patient {instance.patient_id}")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _send_login_alert(self, access: PatientPortalAccess) -> None:
        """Send a security alert for portal login."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == access.patient_id).first()
            if patient and patient.user_id:
                context = {
                    "patient_name": patient.user.full_name if patient.user else "Patient",
                    "ip_address": access.ip_address or "unknown",
                    "user_agent": access.user_agent or "unknown",
                    "login_time": str(access.login_time)
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name='portal_login_alert',
                    context=context,
                    subject='🔐 Portal Login Alert',
                    message=f"New login to your patient portal from IP {access.ip_address} at {access.login_time}."
                )
                # Optionally, also send email for high security
                if patient.user.email:
                    NotificationQueueService.queue_notification(
                        channel='email',
                        recipient=patient.user.email,
                        template_name='portal_login_alert_email',
                        context=context,
                        subject='Security Alert: Portal Login',
                        message=f"Your patient portal was accessed from {access.ip_address}."
                    )
        except Exception as e:
            logger.exception(f"Failed to send login alert for patient {access.patient_id}: {e}")
        finally:
            db.close()