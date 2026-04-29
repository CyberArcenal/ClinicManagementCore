from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.staff.models.labtech_profile import LabTechProfile

class LabTechProfileTransition(BaseStateTransition[LabTechProfile]):

    def on_after_create(self, instance: LabTechProfile) -> None:
        print(f"[LabTech] Created profile for user {instance.user_id}")

    def on_before_update(self, instance: LabTechProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing lab tech profile")