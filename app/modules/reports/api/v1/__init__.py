# app/modules/report_log/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.report_log import router as report_log_router

router = APIRouter()
router.include_router(report_log_router, prefix="/report-logs", tags=["Report Logs"])