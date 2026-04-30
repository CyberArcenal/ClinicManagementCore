from fastapi import APIRouter
from .endpoints.appointment import router as appointment_router

router = APIRouter()
router.include_router(appointment_router, prefix="/appointments", tags=["Appointments"])