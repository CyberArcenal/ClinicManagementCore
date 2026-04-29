# app/modules/schedule/state_transition_service/doctor_schedule.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.schedule.models.schedule import DoctorSchedule
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.staff.models.doctor_profile import DoctorProfile

logger = logging.getLogger(__name__)

class DoctorScheduleTransition(BaseStateTransition[DoctorSchedule]):

    def on_after_create(self, instance: DoctorSchedule) -> None:
        logger.info(f"[DoctorSchedule] Created schedule for doctor {instance.doctor_id} on {instance.day_of_week}")
        self._notify_doctor(instance, action='created')

    def on_before_update(self, instance: DoctorSchedule, changes: Dict[str, Any]) -> None:
        if "doctor_id" in changes:
            raise ValueError("Cannot change doctor_id of existing schedule")
        if "day_of_week" in changes:
            raise ValueError("Cannot change day_of_week of existing schedule")
        if "start_time" in changes or "end_time" in changes:
            start = changes.get("start_time", instance.start_time)
            end = changes.get("end_time", instance.end_time)
            if start >= end:
                raise ValueError("Start time must be before end time")

    def on_after_update(self, instance: DoctorSchedule, changes: Dict[str, Any]) -> None:
        if any(k in changes for k in ("start_time", "end_time", "is_available")):
            logger.info(f"[DoctorSchedule] Updated schedule for doctor {instance.doctor_id} on {instance.day_of_week}")
            self._notify_doctor(instance, action='updated', changes=changes)

    def on_before_delete(self, instance: DoctorSchedule) -> None:
        logger.info(f"[DoctorSchedule] Deleting schedule for doctor {instance.doctor_id} on {instance.day_of_week}")
        self._notify_doctor(instance, action='deleted')

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_doctor(self, schedule: DoctorSchedule, action: str, changes: Dict = None) -> None:
        db = SessionLocal()
        try:
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == schedule.doctor_id).first()
            if doctor and doctor.user_id:
                context = {
                    "doctor_name": doctor.user.full_name if doctor.user else "Doctor",
                    "day": schedule.day_of_week.value.capitalize(),
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time,
                    "is_available": schedule.is_available,
                    "action": action
                }
                if changes:
                    if "start_time" in changes:
                        context["old_start_time"] = changes.get("start_time")
                    if "end_time" in changes:
                        context["old_end_time"] = changes.get("end_time")

                template_name = f"doctor_schedule_{action}"
                subject = f"Schedule {action.capitalize()}"
                message = f"Your schedule for {schedule.day_of_week.value} has been {action}."

                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(doctor.user_id),
                    template_name=template_name,
                    context=context,
                    subject=subject,
                    message=message
                )
        except Exception as e:
            logger.exception(f"Failed to notify doctor about schedule {action}: {e}")
        finally:
            db.close()