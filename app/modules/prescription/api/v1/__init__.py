# app/modules/prescription/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.prescription import router as prescription_router
from .endpoints.prescription_item import router as prescription_item_router

router = APIRouter()
router.include_router(prescription_router, prefix="/prescriptions", tags=["Prescriptions"])
router.include_router(prescription_item_router, prefix="/prescription-items", tags=["Prescription Items"])