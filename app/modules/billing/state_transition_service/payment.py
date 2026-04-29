from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.models.base import Payment

class PaymentTransition(BaseStateTransition[Payment]):

    def on_after_create(self, instance: Payment) -> None:
        print(f"[Payment] Received {instance.amount} for invoice {instance.invoice_id}")
        # Optionally trigger invoice status update – that can be done via a separate service call.