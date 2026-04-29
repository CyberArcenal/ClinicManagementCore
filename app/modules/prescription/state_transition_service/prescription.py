from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.prescription.models import Prescription

class PrescriptionTransition(BaseStateTransition[Prescription]):

    def on_after_create(self, instance: Prescription) -> None:
        print(f"[Prescription] Created for patient {instance.patient_id} by doctor {instance.doctor_id}")

    def on_before_update(self, instance: Prescription, changes: Dict[str, Any]) -> None:
        # Prevent changing patient or doctor after creation
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing prescription")
        if "doctor_id" in changes:
            raise ValueError("Cannot change doctor ID of existing prescription")
        # If already dispensed, prevent further changes to most fields
        if instance.is_dispensed and changes:
            raise ValueError("Cannot modify a dispensed prescription")

    def on_status_change(self, instance: Prescription, old_status: bool, new_status: bool) -> None:
        # is_dispensed field
        if new_status is True:
            print(f"[Prescription] Dispensed prescription {instance.id}")
            # TODO: reduce inventory stock for each item