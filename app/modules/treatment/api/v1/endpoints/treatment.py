# app/modules/treatment/api/v1/endpoints/treatment.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.exceptions.staff import NurseNotFoundError
from app.common.exceptions.treatment import TreatmentNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.patients.models.models import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.treatment.schemas.treatment import TreatmentCreate, TreatmentResponse, TreatmentUpdate
from app.modules.treatment.services.treatment import TreatmentService
from app.modules.user.models import User


router = APIRouter()


@router.post("/", response_model=TreatmentResponse, status_code=status.HTTP_201_CREATED)
async def create_treatment(
    data: TreatmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    """
    Create a new treatment record.
    Requires role: doctor or admin.
    """
    service = TreatmentService(db)
    try:
        treatment = await service.create_treatment(data)
        return treatment
    except (PatientNotFoundError, DoctorNotFoundError, NurseNotFoundError, EHRNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=PaginatedResponse[TreatmentResponse])
async def list_treatments(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    nurse_id: Optional[int] = Query(None),
    treatment_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if doctor_id:
        filters["doctor_id"] = doctor_id
    if nurse_id:
        filters["nurse_id"] = nurse_id
    if treatment_type:
        filters["treatment_type"] = treatment_type
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    service = TreatmentService(db)
    paginated = await service.get_treatments(
        filters=filters,
        page=page,
        page_size=page_size
    )

    # Role-based filtering (applied to items list)
    items = paginated.items
    if current_user.role == "patient":
        patient = await service.db.get(Patient, {"user_id": current_user.id})
        if patient:
            items = [t for t in items if t.patient_id == patient.id]
        else:
            items = []
    elif current_user.role == "doctor":
        doctor = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if doctor:
            items = [t for t in items if t.doctor_id == doctor.id]
        else:
            items = []

    paginated.items = items
    paginated.total = len(items)
    paginated.pages = (paginated.total + page_size - 1) // page_size if paginated.total > 0 else 0
    return paginated


@router.get("/{treatment_id}", response_model=TreatmentResponse)
async def get_treatment(
    treatment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TreatmentService(db)
    treatment = await service.get_treatment(treatment_id, load_relations=True)
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    # Authorization
    if current_user.role == "patient":
        patient = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient or treatment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor":
        doctor = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if not doctor or treatment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return treatment


@router.put("/{treatment_id}", response_model=TreatmentResponse)
async def update_treatment(
    treatment_id: int,
    data: TreatmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = TreatmentService(db)
    try:
        treatment = await service.update_treatment(treatment_id, data)
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment not found")
        return treatment
    except (TreatmentNotFoundError, NurseNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{treatment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_treatment(
    treatment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = TreatmentService(db)
    try:
        deleted = await service.delete_treatment(treatment_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Treatment not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}/history", response_model=List[TreatmentResponse])
async def get_patient_treatments(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TreatmentService(db)
    # Authorization: patients see own, doctors see any, admin see any
    if current_user.role == "patient":
        patient = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")
    treatments = await service.get_treatments_by_patient(patient_id, limit=limit)
    return treatments


@router.get("/doctor/{doctor_id}/treatments", response_model=List[TreatmentResponse])
async def get_doctor_treatments(
    doctor_id: int,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = TreatmentService(db)
    treatments = await service.get_treatments_by_doctor(doctor_id, from_date, to_date)
    return treatments


@router.get("/stats/summary", response_model=dict)
async def get_treatment_statistics(
    doctor_id: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = TreatmentService(db)
    stats = await service.get_treatment_statistics(doctor_id, from_date, to_date)
    return stats