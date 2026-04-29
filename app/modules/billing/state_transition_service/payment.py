import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.core.database import SessionLocal
from app.modules.billing.models.base import Payment
from app.modules.billing.services.invoice import InvoiceService
from app.modules.notifications.services.notification_queue import NotificationQueueService

logger = logging.getLogger(__name__)

class PaymentTransition(BaseStateTransition[Payment]):

    def on_after_create(self, instance: Payment) -> None:
        logger.info(f"[Payment] Received {instance.amount} for invoice {instance.invoice_id}")

        # Recalculate invoice status in a separate session to avoid affecting current transaction
        self._update_invoice_status(instance.invoice_id)

        # Notify patient via in-app
        if instance.invoice and instance.invoice.patient and instance.invoice.patient.user:
            NotificationQueueService.queue_notification(
                channel='inapp',
                recipient=str(instance.invoice.patient.user_id),
                subject='Payment Received',
                message=f'Payment of {instance.amount} received for invoice {instance.invoice.invoice_number}.',
                extra_data={'payment_id': instance.id, 'type': 'payment_received'}
            )

    def _update_invoice_status(self, invoice_id: int) -> None:
        """Use a fresh session to update the invoice status after payment."""
        db = SessionLocal()
        try:
            invoice_service = InvoiceService(db)
            invoice_service.update_invoice_status_from_payments(invoice_id)
            db.commit()
            logger.info(f"Invoice {invoice_id} status updated after payment.")
        except Exception as e:
            logger.exception(f"Failed to update invoice status {invoice_id}: {e}")
            db.rollback()
        finally:
            db.close()