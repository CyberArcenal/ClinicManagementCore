from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.appointment.models.base import Appointment

class AppointmentStateTransition(BaseStateTransition[Appointment]):

    def on_after_create(self, instance: Appointment) -> None:
        # Placeholder: send notifications to patient and doctor
        print(f"[AppointmentState] Created appointment {instance.id}")
        # TODO: Implement notification logic
        pass

    def on_before_update(self, instance: Appointment, changes: Dict[str, Any]) -> None:
        # Validation: cannot change doctor if already confirmed
        if "doctor_id" in changes and instance.status == AppointmentStatus.CONFIRMED:
            raise ValueError("Cannot change doctor for confirmed appointment")

    def on_after_update(self, instance: Appointment, changes: Dict[str, Any]) -> None:
        if "appointment_datetime" in changes:
            print(f"[AppointmentState] Rescheduled appointment {instance.id}")
            # TODO: Send reschedule notification

    def on_status_change(self, instance: Appointment, old_status: AppointmentStatus, new_status: AppointmentStatus) -> None:
        print(f"[AppointmentState] Status changed from {old_status} to {new_status}")
        if new_status == AppointmentStatus.COMPLETED:
            # TODO: Trigger billing item creation
            pass
        elif new_status == AppointmentStatus.CANCELLED:
            # TODO: Free up resources
            pass