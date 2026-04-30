import asyncio
from datetime import datetime
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition

from app.core.database import SessionLocal
from app.modules.notifications.channels.email import EmailService
from app.modules.notifications.channels.push import PushService
from app.modules.notifications.channels.sms import SMSService
from app.modules.notifications.enums.base import NotifyStatus
from app.modules.notifications.models.notify_log import NotifyLog
from app.modules.notifications.services.email_template_service import EmailTemplateService
logger = logging.getLogger(__name__)


class NotifyLogTransition(BaseStateTransition[NotifyLog]):

    def on_after_create(self, instance: NotifyLog) -> None:
        start = datetime.utcnow()
        success = False
        error_msg = None
        rendered_subject = instance.subject
        rendered_body = instance.payload

        try:
            # If template name is given (not 'custom'), render using EmailTemplate
            if instance.notification_type and instance.notification_type != 'custom':
                db = SessionLocal()
                try:
                    template_svc = EmailTemplateService(db)
                    template = template_svc.get_template_by_name_sync(instance.notification_type)
                    if template:
                        context = instance.extra_data or {}
                        rendered_subject, rendered_body = template_svc.render_template(template, context)
                    else:
                        error_msg = f"Template '{instance.notification_type}' not found"
                        raise ValueError(error_msg)
                finally:
                    db.close()
            else:
                # Use stored subject/payload as is
                rendered_subject = instance.subject or ''
                rendered_body = instance.payload or ''

            # Send via appropriate channel
            if instance.channel == 'email':
                success = asyncio.run(EmailService.send_email(
                    to_email=instance.recipient_email,
                    subject=rendered_subject,
                    body=rendered_body
                ))
            elif instance.channel == 'sms':
                success = asyncio.run(SMSService.send_sms(
                    to_number=instance.recipient_email,
                    message=rendered_body or rendered_subject
                ))
            elif instance.channel == 'push':
                success = asyncio.run(PushService.send_push(
                    device_token=instance.recipient_email,
                    title=rendered_subject,
                    message=rendered_body
                ))
            else:
                error_msg = f"Unknown channel: {instance.channel}"
                logger.warning(error_msg)
        except Exception as e:
            logger.exception(f"Notification send failed for log {instance.id}")
            success = False
            error_msg = str(e)

        # Update log entry
        end = datetime.utcnow()
        instance.duration_ms = int((end - start).total_seconds() * 1000)
        if success:
            instance.status = 'sent'
            instance.sent_at = end
            instance.subject = rendered_subject
            instance.payload = rendered_body
        else:
            instance.status = 'failed'
            instance.error_message = error_msg
            instance.last_error_at = end

        self._update_log(instance)

    def _update_log(self, instance: NotifyLog):
        db = SessionLocal()
        try:
            log = db.query(NotifyLog).get(instance.id)
            if log:
                log.status = instance.status
                log.sent_at = instance.sent_at
                log.error_message = instance.error_message
                log.last_error_at = instance.last_error_at
                log.duration_ms = instance.duration_ms
                log.subject = instance.subject
                log.payload = instance.payload
                db.commit()
        except Exception as e:
            logger.exception(f"Failed to update NotifyLog {instance.id}: {e}")
        finally:
            db.close()