# app/modules/staff/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.doctor_profile import router as doctor_router
from .endpoints.nurse_profile import router as nurse_router
from .endpoints.receptionist_profile import router as receptionist_router
from .endpoints.labtech_profile import router as labtech_router
from .endpoints.pharmacist_profile import router as pharmacist_router

router = APIRouter()
router.include_router(doctor_router, prefix="/doctors", tags=["Doctor Profiles"])
router.include_router(nurse_router, prefix="/nurses", tags=["Nurse Profiles"])
router.include_router(receptionist_router, prefix="/receptionists", tags=["Receptionist Profiles"])
router.include_router(labtech_router, prefix="/lab-techs", tags=["Lab Technician Profiles"])
router.include_router(pharmacist_router, prefix="/pharmacists", tags=["Pharmacist Profiles"])