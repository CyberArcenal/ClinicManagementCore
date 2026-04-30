import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.models.billing_item import BillingItem

logger = logging.getLogger(__name__)

class BillingItemTransition(BaseStateTransition[BillingItem]):

    def on_after_create(self, instance: BillingItem) -> None:
        logger.info(f"[BillingItem] Added to invoice {instance.invoice_id}")

    def on_before_delete(self, instance: BillingItem) -> None:
        if instance.invoice and instance.invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot delete item from a paid invoice")