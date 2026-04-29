# app/models/notifications/social_notification.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.common.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "social_notifications"   # renamed to avoid clash with clinic's Notification
    __table_args__ = (
        Index("idx_social_notif_user_read", "user_id", "is_read"),
        Index("idx_social_notif_created", "created_at"),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(20), nullable=False)  # use Enum in app logic
    message = Column(String(255), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    related_id = Column(Integer, nullable=True)
    related_model = Column(String(50), nullable=True)

    # relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="received_notifications")
    actor = relationship("User", foreign_keys=[actor_id], back_populates="sent_notifications")

    def __repr__(self):
        return f"<Notification {self.notification_type} for user {self.user_id}>"