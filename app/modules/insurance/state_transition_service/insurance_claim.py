from typing import Dict, Any
from sqlalchemy.orm import Session

from app.common.state_transition.base import BaseStateTransition
from app.modules.insurance.models.models import InsuranceClaim

class InsuranceClaimTransition(BaseStateTransition[InsuranceClaim]):

    def on_after_create(self, instance: InsuranceClaim) -> None:
        print(f"[InsuranceClaim] Created claim {instance.claim_number} for invoice {instance.invoice_id}")

    def on_before_update(self, instance: InsuranceClaim, changes: Dict[str, Any]) -> None:
        # Prevent reducing approved amount if claim is already paid
        if "approved_amount" in changes and instance.status == "paid":
            raise ValueError("Cannot change approved amount of a paid claim")

    def on_status_change(self, instance: InsuranceClaim, old_status: str, new_status: str) -> None:
        print(f"[InsuranceClaim] Status changed from {old_status} to {new_status}")
        if new_status == "approved":
            # TODO: update invoice with approved amount
            pass
        elif new_status == "paid":
            # TODO: mark invoice as paid if claim covers full amount
            pass