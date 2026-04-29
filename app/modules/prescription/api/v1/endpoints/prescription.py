# app/modules/prescription/api/v1/endpoints/prescription.py
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.prescription.prescription_service import PrescriptionService
from app.modules.prescription.schemas import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
)
from app.api.dependencies.auth import get_current_user, require_role
from app.modules.user.models import User
from app.common.exceptions import (
    PatientNotFoundError,
    DoctorNotFoundError,
    EHRNotFoundError,
    PrescriptionNotFoundError,
)

router = APIRouter()


@router.post("/", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    data: PrescriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    """
    Create a new prescription (including its items).
    Requires role: doctor or admin.
    """
    service = PrescriptionService(db)
    try:
        prescription = await service.create_prescription(data)
        return prescription
    except (PatientNotFoundError, DoctorNotFoundError, EHRNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[PrescriptionResponse])
async def list_prescriptions(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    is_dispensed: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    prescriptions = await service.get_prescriptions(filters=filters, skip=skip, limit=limit)

    # Role-based filtering
    if current_user.role == "patient":
        from app.modules.patient.models import Patient
        patient = await service.db.get(Patient, {"user_id": current_user.id})
        if patient:
            prescriptions = [p for p in prescriptions if p.patient_id == patient.id]
        else:
            prescriptions = []
    elif current_user.role == "doctor":
        from app.modules.doctor.models import DoctorProfile
        doctor = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if doctor:
            prescriptions = [p for p in prescriptions if p.doctor_id == doctor.id]
        else:
            prescriptions = []

    return prescriptions


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PrescriptionService(db)
    prescription = await service.get_prescription(prescription_id, load_items=True)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    # Authorization
    if current_user.role == "patient":
        from app.modules.patient.models import Patient
        patient = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient or prescription.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor":
        from app.modules.doctor.models import DoctorProfile
        doctor = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if not doctor or prescription.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return prescription


@router.put("/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: int,
    data: PrescriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = PrescriptionService(db)
    try:
        prescription = await service.update_prescription(prescription_id, data)
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return prescription
    except PrescriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{prescription_id}/dispense", response_model=PrescriptionResponse)
async def dispense_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    service = PrescriptionService(db)
    prescription = await service.mark_as_dispensed(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PrescriptionService(db)
    deleted = await service.delete_prescription(prescription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return None