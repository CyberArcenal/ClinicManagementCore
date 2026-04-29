# app/modules/notifications/notify_log_service.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, update
from app.common.schema.base import PaginatedResponse
from app.modules.notifications.enums.base import NotifyStatus
from app.modules.notifications.models.notify_log import NotifyLog
from app.modules.notifications.schemas.base import NotifyLogCreate, NotifyLogUpdate


class NotifyLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def get_log(self, log_id: int) -> Optional[NotifyLog]:
        result = await self.db.execute(
            select(NotifyLog).where(NotifyLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> PaginatedResponse[NotifyLog]:
        query = select(NotifyLog)
        if filters:
            if "status" in filters:
                query = query.where(NotifyLog.status == filters["status"])
            if "channel" in filters:
                query = query.where(NotifyLog.channel == filters["channel"])
            if "recipient_email" in filters:
                query = query.where(NotifyLog.recipient_email == filters["recipient_email"])
            if "type" in filters:
                query = query.where(NotifyLog.type == filters["type"])
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        # Ordering
        order_col = getattr(NotifyLog, order_by, NotifyLog.created_at)
        if descending:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()
        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=page_size, pages=pages)

    async def create_log(self, data: NotifyLogCreate) -> NotifyLog:
        log = NotifyLog(
            recipient_email=data.recipient_email,
            subject=data.subject,
            payload=data.payload,
            type=data.type,
            status=data.status,
            error_message=data.error_message,
            channel=data.channel,
            priority=data.priority,
            message_id=data.message_id,
            duration_ms=data.duration_ms,
            retry_count=data.retry_count,
            resend_count=data.resend_count,
            sent_at=data.sent_at,
            last_error_at=data.last_error_at,
            extra_data=data.extra_data,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def update_log(self, log_id: int, data: NotifyLogUpdate) -> Optional[NotifyLog]:
        log = await self.get_log(log_id)
        if not log:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(log, key, value)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def delete_log(self, log_id: int) -> bool:
        log = await self.get_log(log_id)
        if not log:
            return False
        await self.db.delete(log)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities: retry, statistics, cleanup
    # ------------------------------------------------------------------
    async def retry_failed_log(self, log_id: int) -> Optional[NotifyLog]:
        """
        Increment retry_count and reset status to QUEUED.
        (Actual sending should be done by a separate worker.)
        """
        log = await self.get_log(log_id)
        if not log:
            return None
        log.retry_count += 1
        log.status = NotifyStatus.QUEUED.value
        log.error_message = None
        log.last_error_at = None
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def mark_as_sent(self, log_id: int, message_id: str, duration_ms: int) -> bool:
        log = await self.get_log(log_id)
        if not log:
            return False
        log.status = NotifyStatus.SENT.value
        log.message_id = message_id
        log.duration_ms = duration_ms
        log.sent_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def mark_as_failed(self, log_id: int, error_message: str) -> bool:
        log = await self.get_log(log_id)
        if not log:
            return False
        log.status = NotifyStatus.FAILED.value
        log.error_message = error_message
        log.last_error_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def get_statistics(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get counts of logs by status and channel."""
        query = select(NotifyLog)
        if start_date:
            query = query.where(NotifyLog.created_at >= start_date)
        if end_date:
            query = query.where(NotifyLog.created_at <= end_date)
        result = await self.db.execute(query)
        logs = result.scalars().all()
        total = len(logs)
        by_status = {}
        by_channel = {}
        for log in logs:
            by_status[log.status] = by_status.get(log.status, 0) + 1
            by_channel[log.channel] = by_channel.get(log.channel, 0) + 1
        return {
            "total": total,
            "by_status": by_status,
            "by_channel": by_channel,
        }

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Delete logs older than specified days (based on created_at)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(NotifyLog).where(NotifyLog.created_at < cutoff)
        )
        old_logs = result.scalars().all()
        count = len(old_logs)
        for log in old_logs:
            await self.db.delete(log)
        await self.db.commit()
        return count