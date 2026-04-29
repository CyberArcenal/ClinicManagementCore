from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.billing.models import Invoice, BillingItem, Payment
from app.modules.billing.enums.base import InvoiceStatus

class BillingInvoiceTransition(BaseStateTransition[Invoice]):

    def on_after_create(self, instance: Invoice) -> None:
        print(f"[BillingInvoice] Created invoice {instance.invoice_number}")

    def on_before_update(self, instance: Invoice, changes: Dict[str, Any]) -> None:
        # Prevent reducing total if already partially paid
        if "total" in changes and instance.status in [InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID]:
            raise ValueError("Cannot change total of a paid or partially paid invoice")
        # Prevent changing status to PAID if total paid is less than total
        # (Actual check would need to know total paid so far – could be done in after_update or service)

    def on_after_update(self, instance: Invoice, changes: Dict[str, Any]) -> None:
        if "status" in changes:
            print(f"[BillingInvoice] Invoice {instance.invoice_number} status changed to {instance.status}")

    def on_status_change(self, instance: Invoice, old_status: InvoiceStatus, new_status: InvoiceStatus) -> None:
        if new_status == InvoiceStatus.PAID:
            # TODO: trigger receipt generation, mark appointments as confirmed, etc.
            pass


class BillingItemTransition(BaseStateTransition[BillingItem]):

    def on_after_create(self, instance: BillingItem) -> None:
        print(f"[BillingItem] Added item {instance.description} to invoice {instance.invoice_id}")

    def on_before_delete(self, instance: BillingItem) -> None:
        # Prevent deletion if invoice is already paid
        if instance.invoice and instance.invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot delete item from a paid invoice")


class BillingPaymentTransition(BaseStateTransition[Payment]):

    def on_after_create(self, instance: Payment) -> None:
        print(f"[BillingPayment] Received payment {instance.amount} for invoice {instance.invoice_id}")
        # TODO: update invoice status via helper