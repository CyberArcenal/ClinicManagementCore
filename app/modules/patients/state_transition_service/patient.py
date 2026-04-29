from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.patients.models.models import Patient

class PatientTransition(BaseStateTransition[Patient]):

    def on_after_create(self, instance: Patient) -> None:
        print(f"[Patient] Created record for user {instance.user_id}")

    def on_before_update(self, instance: Patient, changes: Dict[str, Any]) -> None:
        # Prevent changing user_id after creation
        if "user_id" in changes:
            raise ValueError("Cannot change user_id of existing patient record")

    def on_before_delete(self, instance: Patient) -> None:
        # Check for dependent records
        if instance.appointments:
            raise ValueError(f"Cannot delete patient with {len(instance.appointments)} existing appointments")
        if instance.prescriptions:
            raise ValueError(f"Cannot delete patient with {len(instance.prescriptions)} existing prescriptions")
        if instance.ehr_records:
            raise ValueError(f"Cannot delete patient with {len(instance.ehr_records)} existing EHR records")
        if instance.lab_results:
            raise ValueError(f"Cannot delete patient with {len(instance.lab_results)} existing lab results")
        if instance.invoices:
            raise ValueError(f"Cannot delete patient with {len(instance.invoices)} existing invoices")
        if instance.payments:
            raise ValueError(f"Cannot delete patient with {len(instance.payments)} existing payments")
        if instance.treatments:
            raise ValueError(f"Cannot delete patient with {len(instance.treatments)} existing treatments")
        if instance.insurance_details:
            raise ValueError(f"Cannot delete patient with {len(instance.insurance_details)} existing insurance details")

    def on_after_delete(self, instance: Patient) -> None:
        print(f"[Patient] Deleted patient record {instance.id}")