from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.staff.models import PharmacistProfile

class PharmacistProfileTransition(BaseStateTransition[PharmacistProfile]):

    def on_after_create(self, instance: PharmacistProfile) -> None:
        print(f"[Pharmacist] Created profile for user {instance.user_id}")

    def on_before_update(self, instance: PharmacistProfile, changes: Dict[str, Any]) -> None:
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing pharmacist profile")