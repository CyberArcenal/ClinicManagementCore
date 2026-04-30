# app/modules/report_log/state_transition_service/report_log.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.reports.models.report import ReportLog
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User

logger = logging.getLogger(__name__)

class ReportLogTransition(BaseStateTransition[ReportLog]):

    def on_after_create(self, instance: ReportLog) -> None:
        logger.info(f"[ReportLog] Generated report '{instance.report_name}' by user {instance.generated_by_id}")
        
        # Optionally notify the user who generated the report (in-app)
        if instance.generated_by_id:
            self._notify_report_generated(instance)

    def on_before_update(self, instance: ReportLog, changes: Dict[str, Any]) -> None:
        if "report_name" in changes:
            raise ValueError("Cannot change report name of existing log")
        if "generated_by_id" in changes:
            raise ValueError("Cannot change generated_by of existing log")

    def on_before_delete(self, instance: ReportLog) -> None:
        logger.info(f"[ReportLog] Deleting log for report '{instance.report_name}'")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_report_generated(self, report: ReportLog) -> None:
        """Send an in-app notification to the user who generated the report."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == report.generated_by_id).first()
            if user:
                context = {
                    "user_name": user.full_name,
                    "report_name": report.report_name,
                    "generated_at": str(report.generated_at),
                    "parameters": report.parameters or "{}"
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(user.id),
                    template_name='report_generated',
                    context=context,
                    subject='Report Generated',
                    message=f'Your report "{report.report_name}" has been generated.'
                )
        except Exception as e:
            logger.exception(f"Failed to send report generation notification: {e}")
        finally:
            db.close()