# app/modules/appointment/state_transition_service/appointment.py
import logging
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import insert
from app.common.state_transition.base import BaseStateTransition
from app.core.database import SessionLocal
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.appointment.models.base import Appointment
from app.modules.billing.models.base import BillingItem
from app.modules.notifications.services.notification_queue import NotificationQueueService

logger = logging.getLogger(__name__)

class AppointmentStateTransition(BaseStateTransition[Appointment]):

    def on_after_create(self, instance: Appointment) -> None:
        logger.info(f"[AppointmentState] Created appointment {instance.id}")

        # Prepare context for notifications
        context = {
            "patient_name": instance.patient.user.full_name if instance.patient and instance.patient.user else "Patient",
            "doctor_name": instance.doctor.user.full_name if instance.doctor and instance.doctor.user else "Doctor",
            "appointment_datetime": str(instance.appointment_datetime),
            "appointment_id": instance.id
        }

        # Notify patient (in-app and optionally email)
        if instance.patient and instance.patient.user:
            # In-app notification (uses template to generate message)
            NotificationQueueService.queue_notification(
                channel='inapp',
                recipient=str(instance.patient.user_id),
                template_name='appointment_created',
                context=context,
                subject='New Appointment',      # fallback if template missing
                message='Your appointment has been scheduled.'
            )
            # Optionally also email using same template (channel='email')
            # NotificationQueueService.queue_notification(
            #     channel='email',
            #     recipient=instance.patient.user.email,
            #     template_name='appointment_created',
            #     context=context
            # )

        # Notify doctor (in-app)
        if instance.doctor and instance.doctor.user:
            NotificationQueueService.queue_notification(
                channel='inapp',
                recipient=str(instance.doctor.user_id),
                template_name='appointment_created_doctor',
                context=context,
                subject='New Appointment',
                message=f'New appointment with patient {instance.patient_id}.'
            )

    def on_before_update(self, instance: Appointment, changes: Dict[str, Any]) -> None:
        if "doctor_id" in changes and instance.status == AppointmentStatus.CONFIRMED:
            raise ValueError("Cannot change doctor for confirmed appointment")

    def on_after_update(self, instance: Appointment, changes: Dict[str, Any]) -> None:
        if "appointment_datetime" in changes:
            logger.info(f"[AppointmentState] Rescheduled appointment {instance.id}")

            context = {
                "patient_name": instance.patient.user.full_name if instance.patient and instance.patient.user else "Patient",
                "doctor_name": instance.doctor.user.full_name if instance.doctor and instance.doctor.user else "Doctor",
                "old_datetime": str(changes.get("old_appointment_datetime", "unknown")),  # may need to store old value
                "new_datetime": str(instance.appointment_datetime),
                "appointment_id": instance.id
            }

            if instance.patient and instance.patient.user:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(instance.patient.user_id),
                    template_name='appointment_rescheduled',
                    context=context,
                    subject='Appointment Rescheduled',
                    message=f'Your appointment moved to {instance.appointment_datetime}.'
                )
            if instance.doctor and instance.doctor.user:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(instance.doctor.user_id),
                    template_name='appointment_rescheduled_doctor',
                    context=context,
                    subject='Appointment Rescheduled',
                    message=f'Appointment with patient {instance.patient_id} moved.'
                )

    def on_status_change(self, instance: Appointment, old_status: AppointmentStatus, new_status: AppointmentStatus) -> None:
        logger.info(f"[AppointmentState] Status changed from {old_status} to {new_status}")

        context = {
            "patient_name": instance.patient.user.full_name if instance.patient and instance.patient.user else "Patient",
            "doctor_name": instance.doctor.user.full_name if instance.doctor and instance.doctor.user else "Doctor",
            "appointment_datetime": str(instance.appointment_datetime),
            "appointment_id": instance.id
        }

        if new_status == AppointmentStatus.COMPLETED:
            self._create_billing_item_sync(instance)

        elif new_status == AppointmentStatus.CANCELLED:
            if instance.patient and instance.patient.user:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(instance.patient.user_id),
                    template_name='appointment_cancelled',
                    context=context,
                    subject='Appointment Cancelled',
                    message=f'Your appointment on {instance.appointment_datetime} cancelled.'
                )
            if instance.doctor and instance.doctor.user:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(instance.doctor.user_id),
                    template_name='appointment_cancelled_doctor',
                    context=context,
                    subject='Appointment Cancelled',
                    message=f'Appointment with patient {instance.patient_id} cancelled.'
                )

    # ------------------------------------------------------------------
    # Helper: synchronous billing item creation (using raw insert or sync ORM)
    # ------------------------------------------------------------------
    def _create_billing_item_sync(self, appointment: Appointment) -> None:
        """
        Create a billing item for the completed appointment using a separate sync session.
        """
        db = SessionLocal()
        try:
            # Option 1: Use SQLAlchemy Core insert (bypasses async service)
            stmt = insert(BillingItem).values(
                invoice_id=None,
                description=f"Appointment fee - Dr. {appointment.doctor_id} on {appointment.appointment_datetime}",
                quantity=1,
                unit_price=Decimal('50.00'),
                total=Decimal('50.00'),
                appointment_id=appointment.id,
                treatment_id=None
            )
            db.execute(stmt)
            db.commit()
            logger.info(f"Billing item created for appointment {appointment.id}")
        except Exception as e:
            logger.exception(f"Failed to create billing item for appointment {appointment.id}: {e}")
            db.rollback()
        finally:
            db.close()