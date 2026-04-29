# app/modules/lab/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.lab_result import router as lab_result_router

router = APIRouter()
router.include_router(lab_result_router, prefix="/lab-results", tags=["Lab Results"])