from typing import Dict, Any
from sqlalchemy.orm import Session

from app.common.state_transition.base import BaseStateTransition
from app.modules.patient_portal.models.models import PatientPortalAccess

class PatientPortalAccessTransition(BaseStateTransition[PatientPortalAccess]):

    def on_after_create(self, instance: PatientPortalAccess) -> None:
        print(f"[PatientPortalAccess] Login recorded for patient {instance.patient_id} from IP {instance.ip_address}")

    def on_before_update(self, instance: PatientPortalAccess, changes: Dict[str, Any]) -> None:
        # Example: prevent changing patient_id after creation
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing access record")

    def on_after_update(self, instance: PatientPortalAccess, changes: Dict[str, Any]) -> None:
        if "logout_time" in changes and changes["logout_time"] is not None:
            print(f"[PatientPortalAccess] Logout recorded for patient {instance.patient_id}")