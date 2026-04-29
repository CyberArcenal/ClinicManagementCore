from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.schedule.models.schedule import DoctorSchedule

class DoctorScheduleTransition(BaseStateTransition[DoctorSchedule]):

    def on_after_create(self, instance: DoctorSchedule) -> None:
        print(f"[DoctorSchedule] Created schedule for doctor {instance.doctor_id} on {instance.day_of_week}")

    def on_before_update(self, instance: DoctorSchedule, changes: Dict[str, Any]) -> None:
        # Prevent changing doctor_id after creation
        if "doctor_id" in changes:
            raise ValueError("Cannot change doctor_id of existing schedule")
        # Prevent changing day_of_week after creation
        if "day_of_week" in changes:
            raise ValueError("Cannot change day_of_week of existing schedule")
        # Validate time range if start_time or end_time changed
        if "start_time" in changes or "end_time" in changes:
            start = changes.get("start_time", instance.start_time)
            end = changes.get("end_time", instance.end_time)
            if start >= end:
                raise ValueError("Start time must be before end time")

    def on_after_update(self, instance: DoctorSchedule, changes: Dict[str, Any]) -> None:
        if "is_available" in changes:
            status = "available" if instance.is_available else "unavailable"
            print(f"[DoctorSchedule] Doctor {instance.doctor_id} is now {status} on {instance.day_of_week}")

    def on_before_delete(self, instance: DoctorSchedule) -> None:
        # Optional: check if there are appointments booked during this schedule?
        print(f"[DoctorSchedule] Deleting schedule for doctor {instance.doctor_id} on {instance.day_of_week}")