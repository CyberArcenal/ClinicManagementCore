from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.patients.schemas.base import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from app.modules.patients.services.patient import PatientService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[PatientResponse]:
    service = PatientService(db)
    try:
        patient = await service.create_patient(data)
        return success_response(data=patient, message="Patient created")
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_patients(
    gender: Optional[str] = Query(None),
    blood_type: Optional[str] = Query(None),
    name: Optional[str] = Query(None, description="Search by user full name"),
    email: Optional[str] = Query(None, description="Search by user email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[PaginatedResponse[PatientResponse]]:
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
    return success_response(data=paginated, message="Patients retrieved")


@router.get("/{patient_id}")
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PatientResponse]:
    service = PatientService(db)
    patient = await service.get_patient(patient_id, load_user=True)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Authorization: patient can see own record, staff/admin can see any
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return success_response(data=patient, message="Patient retrieved")


@router.put("/{patient_id}")
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PatientResponse]:
    service = PatientService(db)
    # Check authorization first
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        updated = await service.update_patient(patient_id, data)
        return success_response(data=updated, message="Patient updated")
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = PatientService(db)
    deleted = await service.delete_patient(patient_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Patient not found")
    return None


@router.get("/search/{search_term}")
async def search_patients(
    search_term: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[list[PatientResponse]]:
    service = PatientService(db)
    patients = await service.search_patients(search_term, skip=skip, limit=limit)
    return success_response(data=patients, message="Patients found")


@router.get("/{patient_id}/summary")
async def get_patient_summary(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict]:
    service = PatientService(db)
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    summary = await service.get_patient_summary(patient_id)
    return success_response(data=summary, message="Patient summary retrieved")


@router.get("/birthdays/today")
async def get_birthdays_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[list[PatientResponse]]:
    service = PatientService(db)
    patients = await service.get_patients_birthday_today()
    return success_response(data=patients, message="Today's birthdays retrieved")