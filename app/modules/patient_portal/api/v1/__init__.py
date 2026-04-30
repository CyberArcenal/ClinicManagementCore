from fastapi import APIRouter
from .endpoints.patient_portal_access import router as portal_router

router = APIRouter()
router.include_router(portal_router, prefix="/patient-portal", tags=["Patient Portal"])