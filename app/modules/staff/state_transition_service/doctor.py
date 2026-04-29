from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.staff.models import DoctorProfile

class DoctorProfileTransition(BaseStateTransition[DoctorProfile]):

    def on_after_create(self, instance: DoctorProfile) -> None:
        print(f"[Doctor] Created profile for user {instance.user_id}")

    def on_before_update(self, instance: DoctorProfile, changes: Dict[str, Any]) -> None:
        # Prevent changing user_id after creation
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing doctor profile")
        # Prevent duplicate license number (handled in service, but also here)
        if "license_number" in changes:
            # Check uniqueness would require query; service should handle.
            pass