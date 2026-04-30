# app/modules/patient/state_transition_service/patient.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.patients.models.patient import Patient
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User

logger = logging.getLogger(__name__)

class PatientTransition(BaseStateTransition[Patient]):

    def on_after_create(self, instance: Patient) -> None:
        logger.info(f"[Patient] Created record for user {instance.user_id}")
        self._send_welcome_notification(instance)

    def on_before_update(self, instance: Patient, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing patient record")

    def on_after_update(self, instance: Patient, changes: Dict[str, Any]) -> None:
        # Notify patient if allergy or emergency contact changed
        important_fields = ["allergies", "emergency_contact_name", "emergency_contact_phone", "blood_type"]
        changed_important = any(field in changes for field in important_fields)
        if changed_important:
            self._send_profile_update_notification(instance, changes)

    def on_before_delete(self, instance: Patient) -> None:
        if instance.appointments:
            raise ValueError(f"Cannot delete patient with {len(instance.appointments)} existing appointments")
        if instance.prescriptions:
            raise ValueError(f"Cannot delete patient with {len(instance.prescriptions)} existing prescriptions")
        if instance.ehr_records:
            raise ValueError(f"Cannot delete patient with {len(instance.ehr_records)} existing EHR records")
        if instance.lab_results:
            raise ValueError(f"Cannot delete patient with {len(instance.lab_results)} existing lab results")
        if instance.invoices:
            raise ValueError(f"Cannot delete patient with {len(instance.invoices)} existing invoices")
        if instance.payments:
            raise ValueError(f"Cannot delete patient with {len(instance.payments)} existing payments")
        if instance.treatments:
            raise ValueError(f"Cannot delete patient with {len(instance.treatments)} existing treatments")
        if instance.insurance_details:
            raise ValueError(f"Cannot delete patient with {len(instance.insurance_details)} existing insurance details")

    def on_after_delete(self, instance: Patient) -> None:
        logger.info(f"[Patient] Deleted patient record {instance.id}")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _send_welcome_notification(self, patient: Patient) -> None:
        """Send welcome notification to the patient's user."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == patient.user_id).first()
            if user:
                context = {
                    "patient_name": user.full_name,
                    "patient_id": patient.id,
                    "email": user.email
                }
                # In-app notification
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='patient_welcome',
                    context=context,
                    subject='Welcome to Our Clinic',
                    message='Thank you for registering as a patient.'
                )
                # Email notification
                if user.email:
                    NotificationQueueService.queue_notification(
                        channel='email',
                        recipient=user.email,
                        template_name='patient_welcome_email',
                        context=context,
                        subject='Welcome to [Clinic Name]',
                        message='Your patient account has been created.'
                    )
                logger.info(f"Welcome notification sent to patient {patient.id}")
        except Exception as e:
            logger.exception(f"Failed to send welcome notification for patient {patient.id}: {e}")
        finally:
            db.close()

    def _send_profile_update_notification(self, patient: Patient, changes: Dict[str, Any]) -> None:
        """Notify patient when important profile fields change."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == patient.user_id).first()
            if user:
                changed_fields = ", ".join(changes.keys())
                context = {
                    "patient_name": user.full_name,
                    "changed_fields": changed_fields
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='patient_profile_updated',
                    context=context,
                    subject='Profile Updated',
                    message=f'Your patient profile has been updated: {changed_fields}.'
                )
        except Exception as e:
            logger.exception(f"Failed to send profile update notification: {e}")
        finally:
            db.close()