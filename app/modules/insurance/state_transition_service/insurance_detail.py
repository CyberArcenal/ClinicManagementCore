from typing import Dict, Any
from sqlalchemy.orm import Session

from app.common.state_transition.base import BaseStateTransition
from app.modules.insurance.models.models import InsuranceDetail

class InsuranceDetailTransition(BaseStateTransition[InsuranceDetail]):

    def on_after_create(self, instance: InsuranceDetail) -> None:
        print(f"[InsuranceDetail] Created policy {instance.policy_number} for patient {instance.patient_id}")

    def on_before_update(self, instance: InsuranceDetail, changes: Dict[str, Any]) -> None:
        # Prevent changing policy number after creation
        if "policy_number" in changes:
            raise ValueError("Cannot change policy number of existing insurance detail")

    def on_before_delete(self, instance: InsuranceDetail) -> None:
        if instance.claims:
            raise ValueError("Cannot delete insurance detail with existing claims")