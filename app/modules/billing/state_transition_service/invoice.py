from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.models.base import Invoice

class InvoiceTransition(BaseStateTransition[Invoice]):

    def on_after_create(self, instance: Invoice) -> None:
        print(f"[Invoice] Created: {instance.invoice_number}")

    def on_before_update(self, instance: Invoice, changes: Dict[str, Any]) -> None:
        if "total" in changes and instance.status in [InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID]:
            raise ValueError("Cannot change total of a paid or partially paid invoice")

    def on_after_update(self, instance: Invoice, changes: Dict[str, Any]) -> None:
        if "status" in changes:
            print(f"[Invoice] Status changed to {instance.status}")

    def on_status_change(self, instance: Invoice, old_status: InvoiceStatus, new_status: InvoiceStatus) -> None:
        if new_status == InvoiceStatus.PAID:
            # TODO: generate receipt, update related appointments
            pass