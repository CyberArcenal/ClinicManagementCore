from fastapi import APIRouter
from .endpoints.ehr import router as ehr_router

router = APIRouter()
router.include_router(ehr_router, prefix="/ehr", tags=["Electronic Health Records"])