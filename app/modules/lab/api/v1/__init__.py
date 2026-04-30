from fastapi import APIRouter
from .endpoints.lab_result import router as lab_router

router = APIRouter()
router.include_router(lab_router, prefix="/lab-results", tags=["Lab Results"])