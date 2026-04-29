from typing import Dict, Any
from sqlalchemy.orm import Session

from app.common.state_transition.base import BaseStateTransition
from app.modules.notifications.models.email_template import EmailTemplate

class EmailTemplateTransition(BaseStateTransition[EmailTemplate]):

    def on_after_create(self, instance: EmailTemplate) -> None:
        print(f"[EmailTemplate] Created: {instance.name}")

    def on_before_update(self, instance: EmailTemplate, changes: Dict[str, Any]) -> None:
        # Prevent changing name after creation
        if "name" in changes:
            raise ValueError("Cannot change template name after creation")