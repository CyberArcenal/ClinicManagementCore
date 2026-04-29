# app/modules/insurance/state_transition_service/insurance_detail.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.insurance.models.models import InsuranceDetail
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.patients.models.models import Patient

logger = logging.getLogger(__name__)

class InsuranceDetailTransition(BaseStateTransition[InsuranceDetail]):

    def on_after_create(self, instance: InsuranceDetail) -> None:
        logger.info(f"[InsuranceDetail] Created policy {instance.policy_number} for patient {instance.patient_id}")

        # Notify patient
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == instance.patient_id).first()
            if patient and patient.user_id:
                context = {
                    "patient_name": patient.user.full_name if patient.user else "Patient",
                    "provider_name": instance.provider_name,
                    "policy_number": instance.policy_number,
                    "coverage_start": str(instance.coverage_start),
                    "coverage_end": str(instance.coverage_end) if instance.coverage_end else "ongoing"
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name='insurance_detail_created',
                    context=context,
                    subject='Insurance Policy Added',
                    message=f"Your {instance.provider_name} policy has been added."
                )
        except Exception as e:
            logger.exception(f"Failed to send insurance notification: {e}")
        finally:
            db.close()

    def on_before_update(self, instance: InsuranceDetail, changes: Dict[str, Any]) -> None:
        if "policy_number" in changes:
            raise ValueError("Cannot change policy number of existing insurance detail")

    def on_before_delete(self, instance: InsuranceDetail) -> None:
        if instance.claims:
            raise ValueError("Cannot delete insurance detail with existing claims")