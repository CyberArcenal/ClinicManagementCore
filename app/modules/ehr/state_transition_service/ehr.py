# app/modules/ehr/state_transition_service/ehr.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.core.database import SessionLocal
from app.modules.ehr.models.ehr import EHR
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.patients.models.patient import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.user.models import User

logger = logging.getLogger(__name__)

# List of critical diagnosis keywords (can be moved to config)
CRITICAL_KEYWORDS = ['cancer', 'tumor', 'malignant', 'heart attack', 'stroke', 'sepsis', 'acute']

class EHRTransition(BaseStateTransition[EHR]):

    def on_after_create(self, instance: EHR) -> None:
        logger.info(f"[EHR] Created record for patient {instance.patient_id} on {instance.visit_date}")
        self._notify_patient_and_doctor(instance, is_new=True)

    def on_before_update(self, instance: EHR, changes: Dict[str, Any]) -> None:
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of an existing EHR record")
        if "doctor_id" in changes and instance.treatments:
            raise ValueError("Cannot change doctor because treatments are already linked")

    def on_after_update(self, instance: EHR, changes: Dict[str, Any]) -> None:
        if "diagnosis" in changes:
            new_diagnosis = changes.get('diagnosis')
            if new_diagnosis:
                logger.info(f"[EHR] Diagnosis updated for record {instance.id}: {new_diagnosis}")
                if self._is_critical_diagnosis(new_diagnosis):
                    self._send_critical_alert(instance, new_diagnosis)
                # Optionally notify patient/doctor of diagnosis change even if not critical
                self._notify_patient_and_doctor(instance, is_new=False, diagnosis_changed=True)
        if "vital_signs" in changes:
            # Check for abnormal vitals (placeholder)
            pass

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_patient_and_doctor(self, ehr: EHR, is_new: bool, diagnosis_changed: bool = False) -> None:
        """Send notifications using templates."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == ehr.patient_id).first()
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == ehr.doctor_id).first()

            # Prepare context
            context = {
                "patient_id": ehr.patient_id,
                "visit_date": str(ehr.visit_date),
                "diagnosis": ehr.diagnosis or "not specified",
                "doctor_name": doctor.user.full_name if doctor and doctor.user else "Doctor",
                "patient_name": patient.user.full_name if patient and patient.user else "Patient",
                "ehr_id": ehr.id
            }

            if is_new:
                template_patient = "ehr_created"
                template_doctor = "ehr_created_doctor"
                fallback_patient_subj = "New Medical Record"
                fallback_patient_msg = f"A new medical record was created for you on {ehr.visit_date}."
                fallback_doctor_subj = "New EHR Record"
                fallback_doctor_msg = f"New EHR record created for patient {ehr.patient_id}."
            elif diagnosis_changed:
                template_patient = "ehr_diagnosis_updated"
                template_doctor = "ehr_diagnosis_updated_doctor"
                fallback_patient_subj = "Diagnosis Updated"
                fallback_patient_msg = f"Your diagnosis has been updated to: {ehr.diagnosis}."
                fallback_doctor_subj = "EHR Diagnosis Updated"
                fallback_doctor_msg = f"Diagnosis for patient {ehr.patient_id} updated to: {ehr.diagnosis}."
            else:
                # Generic update (e.g., notes or vitals)
                template_patient = "ehr_updated"
                template_doctor = "ehr_updated_doctor"
                fallback_patient_subj = "Medical Record Updated"
                fallback_patient_msg = "Your medical record has been updated."
                fallback_doctor_subj = "EHR Record Updated"
                fallback_doctor_msg = f"EHR record for patient {ehr.patient_id} has been updated."

            # Notify patient
            if patient and patient.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name=template_patient,
                    context=context,
                    subject=fallback_patient_subj,
                    message=fallback_patient_msg
                )

            # Notify doctor
            if doctor and doctor.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(doctor.user_id),
                    template_name=template_doctor,
                    context=context,
                    subject=fallback_doctor_subj,
                    message=fallback_doctor_msg
                )

        except Exception as e:
            logger.exception(f"Failed to send notifications for EHR {ehr.id}: {e}")
        finally:
            db.close()

    def _is_critical_diagnosis(self, diagnosis: str) -> bool:
        diagnosis_lower = diagnosis.lower()
        for keyword in CRITICAL_KEYWORDS:
            if keyword in diagnosis_lower:
                return True
        return False

    def _send_critical_alert(self, ehr: EHR, diagnosis: str) -> None:
        """Send critical diagnosis alert to doctor and patient."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == ehr.patient_id).first()
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == ehr.doctor_id).first()

            context = {
                "patient_name": patient.user.full_name if patient and patient.user else "Patient",
                "doctor_name": doctor.user.full_name if doctor and doctor.user else "Doctor",
                "diagnosis": diagnosis,
                "visit_date": str(ehr.visit_date),
                "patient_id": ehr.patient_id
            }

            if patient and patient.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name="critical_diagnosis_patient",
                    context=context,
                    subject="⚠️ Critical Diagnosis Alert",
                    message=f"Your diagnosis includes: {diagnosis}. Please consult your doctor immediately."
                )

            if doctor and doctor.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(doctor.user_id),
                    template_name="critical_diagnosis_doctor",
                    context=context,
                    subject="CRITICAL: Patient Diagnosis",
                    message=f"Patient {ehr.patient_id} diagnosed with: {diagnosis}."
                )

            logger.warning(f"Critical diagnosis alert sent for EHR {ehr.id}: {diagnosis}")

            # Optionally send email to doctor as well (high priority)
            if doctor and doctor.user and doctor.user.email:
                NotificationQueueService.queue_notification(
                    channel='email',
                    recipient=doctor.user.email,
                    template_name="critical_diagnosis_doctor_email",
                    context=context,
                    subject="URGENT: Critical Diagnosis",
                    message=f"Patient {ehr.patient_id} has been diagnosed with {diagnosis}."
                )

        except Exception as e:
            logger.exception(f"Failed to send critical alert for EHR {ehr.id}: {e}")
        finally:
            db.close()