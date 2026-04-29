from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.prescription.models.models import PrescriptionItem

class PrescriptionItemTransition(BaseStateTransition[PrescriptionItem]):

    def on_after_create(self, instance: PrescriptionItem) -> None:
        print(f"[PrescriptionItem] Added {instance.drug_name} to prescription {instance.prescription_id}")

    def on_before_update(self, instance: PrescriptionItem, changes: Dict[str, Any]) -> None:
        # If parent prescription already dispensed, prevent changes
        if instance.prescription and instance.prescription.is_dispensed:
            raise ValueError("Cannot modify items of a dispensed prescription")
        # Prevent changing drug name after creation
        if "drug_name" in changes:
            raise ValueError("Cannot change drug name of existing prescription item")