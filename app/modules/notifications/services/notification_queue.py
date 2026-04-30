import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.notifications.models.notify_log import NotifyLog
from app.modules.notifications.schemas.base import NotificationCreate, NotifyLogCreate
from app.modules.notifications.services.inapp_notification_service import InAppNotificationService
from app.modules.notifications.services.notify_log_service import NotifyLogService

logger = logging.getLogger(__name__)

class NotificationQueueService:
    @staticmethod
    def queue_notification(
        channel: str,
        recipient: str,
        template_name: str = None,
        context: dict = None,
        subject: str = None,     # fallback if no template
        message: str = None,     # fallback if no template
        extra_data: dict = None
    ) -> None:
        db = SessionLocal()
        try:
            if channel == 'inapp':
                # For in-app, you could also render a template to get the message.
                # Here we use the provided message or fallback.
                final_message = message or subject or 'Notification'
                data = NotificationCreate(
                    user_id=int(recipient),
                    actor_id=None,  # system
                    notification_type=template_name or 'generic',
                    message=final_message,
                    is_read=False,
                    related_id=extra_data.get('entity_id') if extra_data else None,
                    related_model=extra_data.get('entity_type') if extra_data else None
                )
                service = InAppNotificationService(db)
                service.create_notification(data)
                db.commit()
                logger.info(f"In-app notification queued for user {recipient} (type={template_name})")
            else:
                # For email/sms/push: store template name and context
                # The NotifyLog will later render the template
                notify_data = NotifyLogCreate(
                    recipient_email=recipient,
                    subject=subject,
                    payload=message,
                    notification_type=template_name or 'custom',
                    status='queued',
                    channel=channel,
                    priority='normal',
                    extra_data=context or {}
                )
                svc = NotifyLogService(db)
                svc.create_log(notify_data)
                db.commit()
                logger.info(f"Queued {channel} notification for {recipient} with template {template_name}")
        finally:
            db.close()