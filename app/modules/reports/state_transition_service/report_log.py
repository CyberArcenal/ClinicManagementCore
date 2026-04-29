from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.reports.models.models import ReportLog

class ReportLogTransition(BaseStateTransition[ReportLog]):

    def on_after_create(self, instance: ReportLog) -> None:
        print(f"[ReportLog] Generated report '{instance.report_name}' by user {instance.generated_by_id}")

    def on_before_update(self, instance: ReportLog, changes: Dict[str, Any]) -> None:
        # Prevent changing report_name or generated_by after creation
        if "report_name" in changes:
            raise ValueError("Cannot change report name of existing log")
        if "generated_by_id" in changes:
            raise ValueError("Cannot change generated_by of existing log")

    def on_before_delete(self, instance: ReportLog) -> None:
        print(f"[ReportLog] Deleting log for report '{instance.report_name}'")