from typing import Dict, Any
from sqlalchemy.orm import Session

from app.common.state_transition.base import BaseStateTransition
from app.modules.ehr.models.base import EHR

class EHRTransition(BaseStateTransition[EHR]):

    def on_after_create(self, instance: EHR) -> None:
        print(f"[EHR] Created record for patient {instance.patient_id} on {instance.visit_date}")

    def on_before_update(self, instance: EHR, changes: Dict[str, Any]) -> None:
        # Example: prevent changing patient_id after creation
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of an existing EHR record")
        # Example: prevent changing doctor_id if already has treatments
        if "doctor_id" in changes and instance.treatments:
            raise ValueError("Cannot change doctor because treatments are already linked")

    def on_after_update(self, instance: EHR, changes: Dict[str, Any]) -> None:
        if "diagnosis" in changes:
            print(f"[EHR] Diagnosis updated for record {instance.id}")
            # TODO: trigger notification if diagnosis is life-threatening