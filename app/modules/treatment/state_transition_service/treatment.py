from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.treatment.models import Treatment

class TreatmentTransition(BaseStateTransition[Treatment]):

    def on_after_create(self, instance: Treatment) -> None:
        print(f"[Treatment] Created treatment for patient {instance.patient_id}: {instance.procedure_name}")

    def on_before_update(self, instance: Treatment, changes: Dict[str, Any]) -> None:
        # Prevent changing patient_id or doctor_id after creation
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing treatment")
        if "doctor_id" in changes:
            raise ValueError("Cannot change doctor ID of existing treatment")

    def on_before_delete(self, instance: Treatment) -> None:
        # Check if linked to a billing item
        if instance.billing_item:
            raise ValueError(f"Cannot delete treatment {instance.id} because it has an associated billing item")