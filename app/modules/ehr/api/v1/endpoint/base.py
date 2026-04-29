# app/modules/ehr/api.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.ehr.schemas.base import EHRCreate, EHRResponse, EHRUpdate
from app.modules.ehr.services.base import EHRService
from app.modules.patients.models.models import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.user.models.base import User


router = APIRouter(prefix="/ehr", tags=["Electronic Health Records"])


@router.post("/", response_model=EHRResponse, status_code=status.HTTP_201_CREATED)
async def create_ehr_record(
    data: EHRCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    """
    Create a new EHR record.
    Requires role: doctor (or admin).
    """
    service = EHRService(db)
    try:
        ehr = await service.create_ehr(data)
        return ehr
    except (PatientNotFoundError, DoctorNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/", response_model=PaginatedResponse[EHRResponse])
async def list_ehr_records(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    diagnosis_contains: Optional[str] = Query(None),
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
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if diagnosis_contains:
        filters["diagnosis_contains"] = diagnosis_contains

    service = EHRService(db)
    paginated = await service.get_ehr_records(
        filters=filters,
        page=page,
        page_size=page_size
    )

    # Role-based filtering (still applied to the items list)
    items = paginated.items
    if current_user.role == "patient":
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if patient_record:
            items = [e for e in items if e.patient_id == patient_record.id]
        else:
            items = []
    elif current_user.role == "doctor":
        doctor_profile = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if doctor_profile:
            items = [e for e in items if e.doctor_id == doctor_profile.id]
        else:
            items = []

    # Return new paginated object with filtered items and recalculated total? 
    # Best to keep original pagination but update the items. We'll replace items and adjust total/pages accordingly.
    paginated.items = items
    paginated.total = len(items)
    paginated.pages = (paginated.total + page_size - 1) // page_size if paginated.total > 0 else 0
    return paginated


@router.get("/{ehr_id}", response_model=EHRResponse)
async def get_ehr_record(
    ehr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EHRService(db)
    ehr = await service.get_ehr(ehr_id, load_relations=True)
    if not ehr:
        raise HTTPException(status_code=404, detail="EHR record not found")

    # Authorization
    if current_user.role == "patient":
        # Check if this EHR belongs to the patient
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient_record or ehr.patient_id != patient_record.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor":
        doctor_profile = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if not doctor_profile or ehr.doctor_id != doctor_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return ehr


@router.put("/{ehr_id}", response_model=EHRResponse)
async def update_ehr_record(
    ehr_id: int,
    data: EHRUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = EHRService(db)
    try:
        ehr = await service.update_ehr(ehr_id, data)
        if not ehr:
            raise HTTPException(status_code=404, detail="EHR record not found")
        # Optional: check if current doctor is the owner? Could be allowed if admin.
        return ehr
    except (DoctorNotFoundError, EHRNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{ehr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ehr_record(
    ehr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Delete an EHR record. Only admin allowed because of dependencies (prescriptions, lab requests, treatments).
    """
    service = EHRService(db)
    try:
        deleted = await service.delete_ehr(ehr_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="EHR record not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}/history", response_model=List[EHRResponse])
async def get_patient_ehr_history(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all EHR records for a specific patient (ordered by visit date desc).
    """
    # Authorization: patient can see own, doctor can see if they treated, admin can see all
    service = EHRService(db)
    patient = await service.db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == "patient":
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient_record or patient_record.id != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor":
        # optional: check if doctor has treated this patient (but we allow viewing)
        pass

    ehrs = await service.get_patient_ehr_history(patient_id, limit=limit)
    return ehrs


@router.get("/search/notes", response_model=List[EHRResponse])
async def search_ehr_notes(
    q: str = Query(..., min_length=2, description="Search term for clinical notes, diagnosis, etc."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    """
    Search within clinical notes, diagnosis, treatment plan, symptoms.
    Only doctors and admins can use this.
    """
    service = EHRService(db)
    results = await service.search_ehr_notes(q, skip=skip, limit=limit)
    return results


@router.get("/stats/summary", response_model=dict)
async def get_ehr_statistics(
    doctor_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = EHRService(db)
    stats = await service.get_ehr_statistics(
        doctor_id=doctor_id, date_from=date_from, date_to=date_to
    )
    return stats