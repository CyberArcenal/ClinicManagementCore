from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import require_role
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.notifications.schemas.base import NotifyLogCreate, NotifyLogResponse
from app.modules.notifications.services.notify_log_service import NotifyLogService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_notify_log(
    data: NotifyLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[NotifyLogResponse]:
    service = NotifyLogService(db)
    log = await service.create_log(data)
    return success_response(data=log, message="Notify log created")


@router.get("/")
async def list_notify_logs(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = Query(None),
    recipient_email: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[PaginatedResponse[NotifyLogResponse]]:
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if channel:
        filters["channel"] = channel
    if recipient_email:
        filters["recipient_email"] = recipient_email

    service = NotifyLogService(db)
    paginated = await service.get_logs(filters=filters, page=page, page_size=page_size)
    return success_response(data=paginated, message="Notify logs retrieved")


@router.get("/{log_id}")
async def get_notify_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[NotifyLogResponse]:
    service = NotifyLogService(db)
    log = await service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Notify log not found")
    return success_response(data=log, message="Notify log retrieved")


@router.post("/{log_id}/retry")
async def retry_notification(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[NotifyLogResponse]:
    service = NotifyLogService(db)
    log = await service.retry_failed_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Notify log not found")
    return success_response(data=log, message="Notification retry queued")


@router.get("/stats/summary")
async def get_notify_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    service = NotifyLogService(db)
    stats = await service.get_statistics()
    return success_response(data=stats, message="Notify statistics retrieved")


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    service = NotifyLogService(db)
    deleted_count = await service.cleanup_old_logs(days)
    return success_response(data={"deleted_logs": deleted_count}, message="Old logs cleaned up")