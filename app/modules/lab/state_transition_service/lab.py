from typing import Dict, Any
from sqlalchemy.orm import Session

from app.common.state_transition.base import BaseStateTransition
from app.modules.lab.models.models import LabResult, LabStatus

class LabResultTransition(BaseStateTransition[LabResult]):

    def on_after_create(self, instance: LabResult) -> None:
        print(f"[LabResult] Created request for patient {instance.patient_id}: {instance.test_name}")

    def on_before_update(self, instance: LabResult, changes: Dict[str, Any]) -> None:
        # Prevent changing patient or test name after creation
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing lab request")
        if "test_name" in changes:
            raise ValueError("Cannot change test name of existing lab request")

    def on_status_change(self, instance: LabResult, old_status: LabStatus, new_status: LabStatus) -> None:
        print(f"[LabResult] Status changed from {old_status} to {new_status}")
        if new_status == LabStatus.COMPLETED:
            # TODO: notify requesting doctor that results are ready
            pass
        elif new_status == LabStatus.CANCELLED:
            # TODO: free up lab resources
            pass