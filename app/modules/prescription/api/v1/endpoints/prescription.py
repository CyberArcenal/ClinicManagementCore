from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.exceptions.prescription import PrescriptionNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.patients.models.patient import Patient
from app.modules.prescription.schemas.base import (
    PrescriptionCreate,
    PrescriptionResponse,
    PrescriptionUpdate,
)
from app.modules.prescription.services.prescription import PrescriptionService
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.user.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_prescription(
    data: PrescriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> SuccessResponse[PrescriptionResponse]:
    service = PrescriptionService(db)
    try:
        prescription = await service.create_prescription(data)
        return success_response(data=prescription, message="Prescription created")
    except (PatientNotFoundError, DoctorNotFoundError, EHRNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_prescriptions(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    is_dispensed: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[PrescriptionResponse]]:
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if doctor_id:
        filters["doctor_id"] = doctor_id
    if is_dispensed is not None:
        filters["is_dispensed"] = is_dispensed
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    service = PrescriptionService(db)
    paginated = await service.get_prescriptions(
        filters=filters,
        page=page,
        page_size=page_size
    )

    # Role-based filtering (applied to items list)
    items = paginated.items
    if current_user.role == "patient":
        patient = await service.db.get(Patient, {"user_id": current_user.id})
        if patient:
            items = [p for p in items if p.patient_id == patient.id]
        else:
            items = []
    elif current_user.role == "doctor":
        doctor = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if doctor:
            items = [p for p in items if p.doctor_id == doctor.id]
        else:
            items = []

    paginated.items = items
    paginated.total = len(items)
    paginated.pages = (paginated.total + page_size - 1) // page_size if paginated.total > 0 else 0
    return success_response(data=paginated, message="Prescriptions retrieved")


@router.get("/{prescription_id}")
async def get_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PrescriptionResponse]:
    service = PrescriptionService(db)
    prescription = await service.get_prescription(prescription_id, load_items=True)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    # Authorization
    if current_user.role == "patient":
        patient = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient or prescription.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor":
        doctor = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if not doctor or prescription.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return success_response(data=prescription, message="Prescription retrieved")


@router.put("/{prescription_id}")
async def update_prescription(
    prescription_id: int,
    data: PrescriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> SuccessResponse[PrescriptionResponse]:
    service = PrescriptionService(db)
    try:
        prescription = await service.update_prescription(prescription_id, data)
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return success_response(data=prescription, message="Prescription updated")
    except PrescriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{prescription_id}/dispense")
async def dispense_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
) -> SuccessResponse[PrescriptionResponse]:
    service = PrescriptionService(db)
    prescription = await service.mark_as_dispensed(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return success_response(data=prescription, message="Prescription dispensed")


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = PrescriptionService(db)
    deleted = await service.delete_prescription(prescription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return None