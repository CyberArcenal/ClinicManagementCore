# app/modules/lab/state_transition_service/lab.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.lab.models.lab import LabResult, LabStatus
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.patients.models.patient import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile

logger = logging.getLogger(__name__)

# Keywords that indicate critical lab results (can be moved to config)
CRITICAL_RESULT_KEYWORDS = ['positive', 'abnormal', 'critical', 'high', 'low', 'malignant', 'cancer']

class LabResultTransition(BaseStateTransition[LabResult]):

    def on_after_create(self, instance: LabResult) -> None:
        logger.info(f"[LabResult] Created request for patient {instance.patient_id}: {instance.test_name}")
        self._notify_doctor_and_patient(instance, event='created')

    def on_before_update(self, instance: LabResult, changes: Dict[str, Any]) -> None:
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing lab request")
        if "test_name" in changes:
            raise ValueError("Cannot change test name of existing lab request")

    def on_status_change(self, instance: LabResult, old_status: LabStatus, new_status: LabStatus) -> None:
        logger.info(f"[LabResult] Status changed from {old_status} to {new_status}")
        
        if new_status == LabStatus.COMPLETED:
            # Notify that results are ready
            self._notify_doctor_and_patient(instance, event='completed')
            # Check if results contain critical values
            if instance.result_data and self._is_critical_result(instance.result_data):
                self._send_critical_alert(instance)
                
        elif new_status == LabStatus.CANCELLED:
            self._notify_doctor_and_patient(instance, event='cancelled')
            # Optionally free lab resources (placeholder)
            
    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_doctor_and_patient(self, lab: LabResult, event: str) -> None:
        """Send appropriate notifications based on event type."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == lab.patient_id).first()
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == lab.requested_by_id).first()
            
            context = {
                "patient_name": patient.user.full_name if patient and patient.user else "Patient",
                "doctor_name": doctor.user.full_name if doctor and doctor.user else "Doctor",
                "test_name": lab.test_name,
                "lab_id": lab.id,
                "status": lab.status.value,
                "requested_date": str(lab.requested_date),
                "completed_date": str(lab.completed_date) if lab.completed_date else "pending"
            }
            
            if event == 'created':
                template_patient = "lab_request_created"
                template_doctor = "lab_request_created_doctor"
                patient_subj = "Lab Test Requested"
                doctor_subj = "Lab Request Created"
            elif event == 'completed':
                template_patient = "lab_result_ready"
                template_doctor = "lab_result_ready_doctor"
                patient_subj = "Lab Results Ready"
                doctor_subj = "Lab Results Completed"
            elif event == 'cancelled':
                template_patient = "lab_request_cancelled"
                template_doctor = "lab_request_cancelled_doctor"
                patient_subj = "Lab Test Cancelled"
                doctor_subj = "Lab Request Cancelled"
            else:
                return
                
            # Notify patient
            if patient and patient.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name=template_patient,
                    context=context,
                    subject=patient_subj,
                    message=f"{lab.test_name} results are ready." if event == 'completed' else f"Your lab request has been {event}."
                )
                
            # Notify doctor
            if doctor and doctor.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(doctor.user_id),
                    template_name=template_doctor,
                    context=context,
                    subject=doctor_subj,
                    message=f"Lab {lab.test_name} for patient {lab.patient_id} is {event}."
                )
        except Exception as e:
            logger.exception(f"Failed to send lab notification for event {event}: {e}")
        finally:
            db.close()
            
    def _is_critical_result(self, result_data: str) -> bool:
        """Heuristic to detect critical lab results."""
        result_lower = result_data.lower()
        for keyword in CRITICAL_RESULT_KEYWORDS:
            if keyword in result_lower:
                return True
        return False
        
    def _send_critical_alert(self, lab: LabResult) -> None:
        """Send urgent alert for critical lab results."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == lab.patient_id).first()
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == lab.requested_by_id).first()
            
            context = {
                "patient_name": patient.user.full_name if patient and patient.user else "Patient",
                "doctor_name": doctor.user.full_name if doctor and doctor.user else "Doctor",
                "test_name": lab.test_name,
                "result_data": lab.result_data,
                "normal_range": lab.normal_range or "not specified",
                "lab_id": lab.id,
                "completed_date": str(lab.completed_date)
            }
            
            # Send critical alert to doctor (in-app and email)
            if doctor and doctor.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(doctor.user_id),
                    template_name='critical_lab_result_doctor',
                    context=context,
                    subject='URGENT: Critical Lab Result',
                    message=f"Critical result for {lab.test_name} on patient {lab.patient_id}."
                )
                # Optionally email doctor as well
                if doctor.user.email:
                    NotificationQueueService.queue_notification(
                        channel='email',
                        recipient=doctor.user.email,
                        template_name='critical_lab_result_doctor_email',
                        context=context,
                        subject='URGENT: Critical Lab Result',
                        message=f"Patient {lab.patient_id} has critical {lab.test_name} results."
                    )
            # Also notify patient? Usually doctor handles, but maybe not.
            logger.warning(f"Critical lab result alert sent for lab {lab.id}: {lab.result_data[:100]}")
        except Exception as e:
            logger.exception(f"Failed to send critical lab alert: {e}")
        finally:
            db.close()