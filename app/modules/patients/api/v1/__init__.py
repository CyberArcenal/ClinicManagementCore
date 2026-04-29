# app/modules/patients/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.patients import router as patients_router

router = APIRouter()
router.include_router(patients_router, prefix="/patients", tags=["Patients"])