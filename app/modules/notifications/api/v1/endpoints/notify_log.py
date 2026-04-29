# app/modules/notification/api/v1/endpoints/notify_log.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import require_role
from app.common.schema.base import PaginatedResponse
from app.modules.notifications.schemas.base import NotifyLogCreate, NotifyLogResponse
from app.modules.notifications.services.notify_log_service import NotifyLogService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=NotifyLogResponse, status_code=status.HTTP_201_CREATED)
async def create_notify_log(
    data: NotifyLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NotifyLogService(db)
    log = await service.create_log(data)
    return log


@router.get("/", response_model=PaginatedResponse[NotifyLogResponse])
async def list_notify_logs(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = Query(None),
    recipient_email: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if channel:
        filters["channel"] = channel
    if recipient_email:
        filters["recipient_email"] = recipient_email
    service = NotifyLogService(db)
    paginated = await service.get_logs(filters=filters, page=page, page_size=page_size)
    return paginated


@router.get("/{log_id}", response_model=NotifyLogResponse)
async def get_notify_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NotifyLogService(db)
    log = await service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Notify log not found")
    return log


@router.post("/{log_id}/retry", response_model=NotifyLogResponse)
async def retry_notification(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NotifyLogService(db)
    log = await service.retry_failed_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Notify log not found")
    return log


@router.get("/stats/summary", response_model=dict)
async def get_notify_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NotifyLogService(db)
    # Convert strings to datetime if needed, or pass None
    stats = await service.get_statistics()
    return stats


@router.delete("/cleanup", response_model=dict)
async def cleanup_old_logs(
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = NotifyLogService(db)
    deleted_count = await service.cleanup_old_logs(days)
    return {"deleted_logs": deleted_count}