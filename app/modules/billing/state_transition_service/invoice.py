import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.models.base import Invoice
from app.modules.notifications.services.notification_queue import NotificationQueueService

logger = logging.getLogger(__name__)

class InvoiceTransition(BaseStateTransition[Invoice]):

    def on_after_create(self, instance: Invoice) -> None:
        logger.info(f"[Invoice] Created: {instance.invoice_number}")

        # Notify patient via in-app
        if instance.patient and instance.patient.user:
            NotificationQueueService.queue_notification(
                channel='inapp',
                recipient=str(instance.patient.user_id),
                subject='New Invoice',
                message=f'Invoice {instance.invoice_number} for {instance.total} has been created.',
                extra_data={'invoice_id': instance.id, 'type': 'invoice_created'}
            )
        # Could also send email if needed via channel='email'

    def on_before_update(self, instance: Invoice, changes: Dict[str, Any]) -> None:
        if "total" in changes and instance.status in [InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID]:
            raise ValueError("Cannot change total of a paid or partially paid invoice")

    def on_after_update(self, instance: Invoice, changes: Dict[str, Any]) -> None:
        if "status" in changes:
            logger.info(f"[Invoice] Status changed to {instance.status}")
            # Notify patient when status changes to PAID
            if instance.status == InvoiceStatus.PAID and instance.patient and instance.patient.user:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(instance.patient.user_id),
                    subject='Invoice Paid',
                    message=f'Invoice {instance.invoice_number} has been fully paid.',
                    extra_data={'invoice_id': instance.id, 'type': 'invoice_paid'}
                )