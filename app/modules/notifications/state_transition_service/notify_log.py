from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.notifications.enums.base import NotifyStatus
from app.modules.notifications.models.notify_log import NotifyLog

class NotifyLogTransition(BaseStateTransition[NotifyLog]):

    def on_after_create(self, instance: NotifyLog) -> None:
        print(f"[NotifyLog] Created for {instance.recipient_email} with status {instance.status}")

    def on_status_change(self, instance: NotifyLog, old_status: str, new_status: str) -> None:
        if new_status == NotifyStatus.SENT.value:
            print(f"[NotifyLog] Successfully sent to {instance.recipient_email}")
        elif new_status == NotifyStatus.FAILED.value:
            print(f"[NotifyLog] Failed to send to {instance.recipient_email}: {instance.error_message}")