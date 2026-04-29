# app/modules/treatment/state_transition_service/treatment.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.treatment.models.models import Treatment
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.patients.models.models import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile

logger = logging.getLogger(__name__)

class TreatmentTransition(BaseStateTransition[Treatment]):

    def on_after_create(self, instance: Treatment) -> None:
        logger.info(f"[Treatment] Created treatment for patient {instance.patient_id}: {instance.procedure_name or instance.treatment_type}")
        self._notify_patient_and_doctor(instance)

    def on_before_update(self, instance: Treatment, changes: Dict[str, Any]) -> None:
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing treatment")
        if "doctor_id" in changes:
            raise ValueError("Cannot change doctor ID of existing treatment")

    def on_before_delete(self, instance: Treatment) -> None:
        if instance.billing_item:
            raise ValueError(f"Cannot delete treatment {instance.id} because it has an associated billing item")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_patient_and_doctor(self, treatment: Treatment) -> None:
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == treatment.patient_id).first()
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == treatment.doctor_id).first()
            context = {
                "patient_name": patient.user.full_name if patient and patient.user else "Patient",
                "doctor_name": doctor.user.full_name if doctor and doctor.user else "Doctor",
                "treatment_type": treatment.treatment_type or "",
                "procedure_name": treatment.procedure_name or treatment.treatment_type,
                "treatment_id": treatment.id,
                "performed_date": str(treatment.performed_date) if treatment.performed_date else "to be scheduled",
                "notes": treatment.notes or ""
            }
            if patient and patient.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name='treatment_created_patient',
                    context=context,
                    subject='Treatment Scheduled',
                    message=f"Your {context['procedure_name']} has been scheduled."
                )
            if doctor and doctor.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(doctor.user_id),
                    template_name='treatment_created_doctor',
                    context=context,
                    subject='Treatment Created',
                    message=f"Treatment {context['procedure_name']} for patient {treatment.patient_id} created."
                )
        except Exception as e:
            logger.exception(f"Failed to send treatment notification: {e}")
        finally:
            db.close()