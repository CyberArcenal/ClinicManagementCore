# app/modules/reports/report_log_service.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.common.exceptions.report_log import ReportLogNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.reports.models.report import ReportLog
from app.modules.reports.schemas.base import ReportLogCreate, ReportLogUpdate
from app.modules.user.models import User


class ReportLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_report_log(self, log_id: int) -> Optional[ReportLog]:
        result = await self.db.execute(
            select(ReportLog).where(ReportLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_report_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "generated_at",
        descending: bool = True,
    ) -> PaginatedResponse[ReportLog]:
        query = select(ReportLog)
        if filters:
            if "report_name" in filters:
                query = query.where(ReportLog.report_name.ilike(f"%{filters['report_name']}%"))
            if "generated_by_id" in filters:
                query = query.where(ReportLog.generated_by_id == filters["generated_by_id"])
            if "date_from" in filters:
                query = query.where(ReportLog.generated_at >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(ReportLog.generated_at <= filters["date_to"])
            if "file_path_contains" in filters:
                query = query.where(ReportLog.file_path.ilike(f"%{filters['file_path_contains']}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_col = getattr(ReportLog, order_by, ReportLog.generated_at)
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
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=page_size,
            pages=pages
        )

    async def create_report_log(self, data: ReportLogCreate) -> ReportLog:
        # Validate user exists if generated_by_id provided
        if data.generated_by_id:
            user = await self.db.get(User, data.generated_by_id)
            if not user:
                raise UserNotFoundError(f"User {data.generated_by_id} not found")

        log = ReportLog(
            report_name=data.report_name,
            generated_by_id=data.generated_by_id,
            parameters=data.parameters,
            file_path=data.file_path,
            generated_at=data.generated_at or datetime.utcnow(),
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def update_report_log(
        self, log_id: int, data: ReportLogUpdate
    ) -> Optional[ReportLog]:
        log = await self.get_report_log(log_id)
        if not log:
            raise ReportLogNotFoundError(f"Report log {log_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(log, key, value)

        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def delete_report_log(self, log_id: int) -> bool:
        log = await self.get_report_log(log_id)
        if not log:
            return False
        await self.db.delete(log)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def get_reports_by_user(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> List[ReportLog]:
        query = (
            select(ReportLog)
            .where(ReportLog.generated_by_id == user_id)
            .order_by(ReportLog.generated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_reports_by_name(
        self, report_name: str, skip: int = 0, limit: int = 50
    ) -> List[ReportLog]:
        query = (
            select(ReportLog)
            .where(ReportLog.report_name.ilike(f"%{report_name}%"))
            .order_by(ReportLog.generated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_report_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get statistics about report generation: total reports, most frequent report names, etc."""
        query = select(ReportLog)
        if start_date:
            query = query.where(ReportLog.generated_at >= start_date)
        if end_date:
            query = query.where(ReportLog.generated_at <= end_date)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        total_reports = len(logs)
        unique_users = len(set(l.generated_by_id for l in logs if l.generated_by_id))

        # Most generated report names
        name_counts = {}
        for log in logs:
            name_counts[log.report_name] = name_counts.get(log.report_name, 0) + 1
        top_reports = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_reports_generated": total_reports,
            "unique_users_generated": unique_users,
            "top_report_names": [{"name": name, "count": count} for name, count in top_reports],
        }

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Delete report logs older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(ReportLog).where(ReportLog.generated_at < cutoff)
        )
        old_logs = result.scalars().all()
        count = len(old_logs)
        for log in old_logs:
            await self.db.delete(log)
        await self.db.commit()
        return count