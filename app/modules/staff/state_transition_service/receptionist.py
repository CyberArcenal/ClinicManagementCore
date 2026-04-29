from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.staff.models.receptionist_profile import ReceptionistProfile

class ReceptionistProfileTransition(BaseStateTransition[ReceptionistProfile]):

    def on_after_create(self, instance: ReceptionistProfile) -> None:
        print(f"[Receptionist] Created profile for user {instance.user_id}")

    def on_before_update(self, instance: ReceptionistProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing receptionist profile")