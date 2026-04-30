from fastapi import APIRouter
from .endpoints.insurance_detail import router as detail_router
from .endpoints.insurance_claim import router as claim_router

router = APIRouter()
router.include_router(detail_router, prefix="/insurance-details", tags=["Insurance Details"])
router.include_router(claim_router, prefix="/insurance-claims", tags=["Insurance Claims"])