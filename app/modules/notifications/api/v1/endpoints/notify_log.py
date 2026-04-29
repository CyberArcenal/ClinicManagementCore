# app/modules/notification/api/v1/endpoints/notify_log.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.get("/", response_model=List[NotifyLogResponse])
async def list_notify_logs(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = Query(None),
    recipient_email: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
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
    logs = await service.get_logs(filters=filters, skip=skip, limit=limit)
    return logs


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