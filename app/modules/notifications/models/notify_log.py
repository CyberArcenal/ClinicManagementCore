# app/models/notifications/notify_log.py
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Index
from sqlalchemy.sql import func


from app.common.models.base import BaseModel
from app.modules.notifications.enums.base import NotifyStatus


class NotifyLog(BaseModel):
    __tablename__ = "notify_logs"
    __table_args__ = (
        Index("idx_notify_status", "status"),
        Index("idx_notify_recipient", "recipient_email"),
        Index("idx_notify_status_created", "status", "created_at"),
    )

    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    payload = Column(Text, nullable=True)
    type = Column(String(50), nullable=False, default="custom")  # store TemplateType value
    status = Column(String(20), nullable=False, default=NotifyStatus.QUEUED.value)
    error_message = Column(Text, nullable=True)
    channel = Column(String(50), nullable=False, default="email")
    priority = Column(String(20), nullable=False, default="normal")
    message_id = Column(String(255), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    resend_count = Column(Integer, nullable=False, default=0)
    sent_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Note: BaseModel provides created_at & updated_at (Django uses created_at & updated_at too)

    def __repr__(self):
        return f"<NotifyLog {self.recipient_email} - {self.status}>"