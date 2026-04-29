# app/modules/treatment/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.treatment import router as treatment_router

router = APIRouter()
router.include_router(treatment_router, prefix="/treatments", tags=["Treatments"])