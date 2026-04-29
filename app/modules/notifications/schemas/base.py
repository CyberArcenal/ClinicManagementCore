# app/schemas/notification.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.common.schema.base import BaseSchema, TimestampSchema
from app.modules.notifications.enums.base import TemplateType, NotifyStatus

# EmailTemplate
class EmailTemplateBase(BaseSchema):
    name: str
    subject: str
    content: str

class EmailTemplateCreate(EmailTemplateBase):
    pass

class EmailTemplateUpdate(BaseSchema):
    subject: Optional[str] = None
    content: Optional[str] = None

class EmailTemplateResponse(TimestampSchema, EmailTemplateBase):
    pass

# InAppNotification (social_notifications)
class NotificationBase(BaseSchema):
    user_id: int
    actor_id: int
    notification_type: str   # e.g., "appointment_reminder"
    message: str
    is_read: bool = False
    related_id: Optional[int] = None
    related_model: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseSchema):
    is_read: Optional[bool] = None

class NotificationResponse(TimestampSchema, NotificationBase):
    pass

# NotifyLog
class NotifyLogBase(BaseSchema):
    recipient_email: str
    subject: Optional[str] = None
    payload: Optional[str] = None
    type: str = "custom"
    status: str = NotifyStatus.QUEUED.value
    error_message: Optional[str] = None
    channel: str = "email"
    priority: str = "normal"
    message_id: Optional[str] = None
    duration_ms: Optional[int] = None
    retry_count: int = 0
    resend_count: int = 0
    sent_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None

class NotifyLogCreate(NotifyLogBase):
    pass

class NotifyLogUpdate(BaseSchema):
    status: Optional[str] = None
    error_message: Optional[str] = None
    message_id: Optional[str] = None
    duration_ms: Optional[int] = None
    retry_count: Optional[int] = None
    resend_count: Optional[int] = None
    sent_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None

class NotifyLogResponse(TimestampSchema, NotifyLogBase):
    pass