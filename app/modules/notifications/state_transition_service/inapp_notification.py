from typing import Dict, Any
from sqlalchemy.orm import Session

from app.common.state_transition.base import BaseStateTransition
from app.modules.notifications.models.inapp_notification import Notification

class NotificationTransition(BaseStateTransition[Notification]):

    def on_after_create(self, instance: Notification) -> None:
        print(f"[Notification] Created for user {instance.user_id}: {instance.notification_type}")

    def on_status_change(self, instance: Notification, old_status: bool, new_status: bool) -> None:
        # is_read status change
        if new_status is True:
            print(f"[Notification] Marked as read for user {instance.user_id}")