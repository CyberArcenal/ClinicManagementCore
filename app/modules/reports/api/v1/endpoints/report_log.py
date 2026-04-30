from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import require_role
from app.common.exceptions.report_log import ReportLogNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.reports.schemas.base import (
    ReportLogCreate,
    ReportLogResponse,
    ReportLogUpdate,
)
from app.modules.reports.services.base import ReportLogService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_report_log(
    data: ReportLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[ReportLogResponse]:
    service = ReportLogService(db)
    try:
        log = await service.create_report_log(data)
        return success_response(data=log, message="Report log created")
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_report_logs(
    report_name: Optional[str] = Query(None),
    generated_by_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[PaginatedResponse[ReportLogResponse]]:
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
    paginated = await service.get_report_logs(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return success_response(data=paginated, message="Report logs retrieved")


@router.get("/{log_id}")
async def get_report_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[ReportLogResponse]:
    service = ReportLogService(db)
    log = await service.get_report_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Report log not found")
    return success_response(data=log, message="Report log retrieved")


@router.put("/{log_id}")
async def update_report_log(
    log_id: int,
    data: ReportLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[ReportLogResponse]:
    service = ReportLogService(db)
    try:
        log = await service.update_report_log(log_id, data)
        if not log:
            raise HTTPException(status_code=404, detail="Report log not found")
        return success_response(data=log, message="Report log updated")
    except ReportLogNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = ReportLogService(db)
    deleted = await service.delete_report_log(log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report log not found")
    return None


@router.get("/user/{user_id}")
async def get_reports_by_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[list[ReportLogResponse]]:
    service = ReportLogService(db)
    logs = await service.get_reports_by_user(user_id, skip=skip, limit=limit)
    return success_response(data=logs, message="Reports by user retrieved")


@router.get("/summary/stats")
async def get_report_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    service = ReportLogService(db)
    stats = await service.get_report_statistics(start_date=start_date, end_date=end_date)
    return success_response(data=stats, message="Report statistics retrieved")


@router.delete("/cleanup/old")
async def cleanup_old_logs(
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    service = ReportLogService(db)
    deleted_count = await service.cleanup_old_logs(days)
    return success_response(data={"deleted_logs": deleted_count}, message="Old logs cleaned up")