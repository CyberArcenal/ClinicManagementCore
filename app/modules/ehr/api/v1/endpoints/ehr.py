from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.ehr.schemas.base import EHRCreate, EHRResponse, EHRUpdate
from app.modules.ehr.services.base import EHRService
from app.modules.patients.models.patient import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.user.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ehr_record(
    data: EHRCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> SuccessResponse[EHRResponse]:
    service = EHRService(db)
    try:
        ehr = await service.create_ehr(data)
        return success_response(data=ehr, message="EHR record created")
    except (PatientNotFoundError, DoctorNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_ehr_records(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    diagnosis_contains: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[EHRResponse]]:
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
        filters=filters, page=page, page_size=page_size
    )

    # Role-based filtering
    items = paginated.items
    if current_user.role == "patient":
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if patient_record:
            items = [e for e in items if e.patient_id == patient_record.id]
        else:
            items = []
    elif current_user.role == "doctor":
        doctor_profile = await service.db.get(
            DoctorProfile, {"user_id": current_user.id}
        )
        if doctor_profile:
            items = [e for e in items if e.doctor_id == doctor_profile.id]
        else:
            items = []

    paginated.items = items
    paginated.total = len(items)
    paginated.pages = (
        (paginated.total + page_size - 1) // page_size if paginated.total > 0 else 0
    )

    return success_response(data=paginated, message="EHR records retrieved")


@router.get("/{ehr_id}")
async def get_ehr_record(
    ehr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[EHRResponse]:
    service = EHRService(db)
    ehr = await service.get_ehr(ehr_id, load_relations=True)
    if not ehr:
        raise HTTPException(status_code=404, detail="EHR record not found")

    # Authorization
    if current_user.role == "patient":
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient_record or ehr.patient_id != patient_record.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor":
        doctor_profile = await service.db.get(
            DoctorProfile, {"user_id": current_user.id}
        )
        if not doctor_profile or ehr.doctor_id != doctor_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return success_response(data=ehr, message="EHR record retrieved")


@router.put("/{ehr_id}")
async def update_ehr_record(
    ehr_id: int,
    data: EHRUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> SuccessResponse[EHRResponse]:
    service = EHRService(db)
    try:
        ehr = await service.update_ehr(ehr_id, data)
        if not ehr:
            raise HTTPException(status_code=404, detail="EHR record not found")
        return success_response(data=ehr, message="EHR record updated")
    except (DoctorNotFoundError, EHRNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{ehr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ehr_record(
    ehr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = EHRService(db)
    try:
        deleted = await service.delete_ehr(ehr_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="EHR record not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}/history")
async def get_patient_ehr_history(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[EHRResponse]]:
    service = EHRService(db)
    patient = await service.db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == "patient":
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient_record or patient_record.id != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")
    # doctor role is allowed to view

    ehrs = await service.get_patient_ehr_history(patient_id, limit=limit)
    return success_response(data=ehrs, message="Patient EHR history retrieved")


@router.get("/search/notes")
async def search_ehr_notes(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
) -> SuccessResponse[list[EHRResponse]]:
    service = EHRService(db)
    results = await service.search_ehr_notes(q, skip=skip, limit=limit)
    return success_response(data=results, message="Search results")


@router.get("/stats/summary")
async def get_ehr_statistics(
    doctor_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    service = EHRService(db)
    stats = await service.get_ehr_statistics(
        doctor_id=doctor_id, date_from=date_from, date_to=date_to
    )
    return success_response(data=stats, message="EHR statistics")