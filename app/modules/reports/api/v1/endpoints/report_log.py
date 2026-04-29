# app/modules/report_log/api/v1/endpoints/report_log.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=ReportLogResponse, status_code=status.HTTP_201_CREATED)
async def create_report_log(
    data: ReportLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Create a log entry for a generated report.
    Usually called automatically when a report is generated.
    """
    service = ReportLogService(db)
    try:
        log = await service.create_report_log(data)
        return log
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[ReportLogResponse])
async def list_report_logs(
    report_name: Optional[str] = Query(None),
    generated_by_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    filters = {}
    if report_name:
        filters["report_name"] = report_name
    if generated_by_id:
        filters["generated_by_id"] = generated_by_id
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    service = ReportLogService(db)
    logs = await service.get_report_logs(filters=filters, skip=skip, limit=limit)
    return logs


@router.get("/{log_id}", response_model=ReportLogResponse)
async def get_report_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReportLogService(db)
    log = await service.get_report_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Report log not found")
    return log


@router.put("/{log_id}", response_model=ReportLogResponse)
async def update_report_log(
    log_id: int,
    data: ReportLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReportLogService(db)
    try:
        log = await service.update_report_log(log_id, data)
        if not log:
            raise HTTPException(status_code=404, detail="Report log not found")
        return log
    except ReportLogNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReportLogService(db)
    deleted = await service.delete_report_log(log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report log not found")
    return None


@router.get("/user/{user_id}", response_model=List[ReportLogResponse])
async def get_reports_by_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReportLogService(db)
    logs = await service.get_reports_by_user(user_id, skip=skip, limit=limit)
    return logs


@router.get("/summary/stats", response_model=dict)
async def get_report_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReportLogService(db)
    stats = await service.get_report_statistics(start_date=start_date, end_date=end_date)
    return stats


@router.delete("/cleanup/old", response_model=dict)
async def cleanup_old_logs(
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ReportLogService(db)
    deleted_count = await service.cleanup_old_logs(days)
    return {"deleted_logs": deleted_count}