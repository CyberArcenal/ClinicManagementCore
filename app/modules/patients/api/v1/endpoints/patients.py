# app/modules/patients/api/v1/endpoints/patients.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.patients.schemas.base import PatientCreate, PatientResponse, PatientUpdate
from app.modules.patients.services.patient import PatientService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    """
    Create a new patient record. Requires an existing user account.
    """
    service = PatientService(db)
    try:
        patient = await service.create_patient(data)
        return patient
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedResponse[PatientResponse])
async def list_patients(
    gender: Optional[str] = Query(None),
    blood_type: Optional[str] = Query(None),
    name: Optional[str] = Query(None, description="Search by user full name"),
    email: Optional[str] = Query(None, description="Search by user email"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    filters = {}
    if gender:
        filters["gender"] = gender
    if blood_type:
        filters["blood_type"] = blood_type
    if name:
        filters["user__full_name"] = name
    if email:
        filters["user__email"] = email

    service = PatientService(db)
    paginated = await service.get_patients(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return paginated


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PatientService(db)
    patient = await service.get_patient(patient_id, load_user=True)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Authorization: patient can see own record, staff/admin can see any
    if current_user.role == "patient":
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PatientService(db)
    # Check authorization first
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        updated = await service.update_patient(patient_id, data)
        return updated
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PatientService(db)
    deleted = await service.delete_patient(patient_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Patient not found")
    return None


@router.get("/search/{search_term}", response_model=List[PatientResponse])
async def search_patients(
    search_term: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = PatientService(db)
    patients = await service.search_patients(search_term, skip=skip, limit=limit)
    return patients


@router.get("/{patient_id}/summary", response_model=dict)
async def get_patient_summary(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PatientService(db)
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    summary = await service.get_patient_summary(patient_id)
    return summary


@router.get("/birthdays/today", response_model=List[PatientResponse])
async def get_birthdays_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = PatientService(db)
    patients = await service.get_patients_birthday_today()
    return patients