from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import PatientNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.patient_portal.schemas.base import (
    PatientPortalAccessCreate,
    PatientPortalAccessResponse,
    PatientPortalAccessUpdate,
)
from app.modules.patient_portal.services.base import PatientPortalAccessService
from app.modules.patients.models.patient import Patient
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_access_record(
    data: PatientPortalAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[PatientPortalAccessResponse]:
    service = PatientPortalAccessService(db)
    try:
        record = await service.create_access_record(data)
        return success_response(data=record, message="Access record created")
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_access_records(
    patient_id: Optional[int] = Query(None),
    ip_address: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[PaginatedResponse[PatientPortalAccessResponse]]:
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if ip_address:
        filters["ip_address"] = ip_address

    service = PatientPortalAccessService(db)
    paginated = await service.get_access_records(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return success_response(data=paginated, message="Access records retrieved")


@router.get("/{record_id}")
async def get_access_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[PatientPortalAccessResponse]:
    service = PatientPortalAccessService(db)
    record = await service.get_access_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Access record not found")
    return success_response(data=record, message="Access record retrieved")


@router.put("/{record_id}")
async def update_access_record(
    record_id: int,
    data: PatientPortalAccessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[PatientPortalAccessResponse]:
    service = PatientPortalAccessService(db)
    record = await service.update_access_record(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Access record not found")
    return success_response(data=record, message="Access record updated")


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_access_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = PatientPortalAccessService(db)
    deleted = await service.delete_access_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Access record not found")
    return None


# ------------------------------------------------------------------
# Patient‑facing endpoints (for portal functionality)
# ------------------------------------------------------------------
@router.post("/login")
async def portal_login(
    patient_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict]:
    patient_record = await db.get(Patient, patient_id)
    if not patient_record or patient_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    service = PatientPortalAccessService(db)
    record = await service.record_login(patient_id, ip_address or "unknown", user_agent or "unknown")
    return success_response(data={"session_id": record.id}, message="Login recorded")


@router.post("/logout")
async def portal_logout(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[None]:
    patient_record = await db.get(Patient, patient_id)
    if not patient_record or patient_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    service = PatientPortalAccessService(db)
    success = await service.record_logout(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="No active session found")
    return success_response(data=None, message="Logout recorded")


@router.get("/me/history")
async def get_my_access_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[PatientPortalAccessResponse]]:
    patient_record = await db.get(Patient, {"user_id": current_user.id})
    if not patient_record:
        raise HTTPException(status_code=404, detail="Patient record not found")
    service = PatientPortalAccessService(db)
    history = await service.get_patient_access_history(patient_record.id, limit=limit)
    return success_response(data=history, message="Access history retrieved")


@router.get("/me/active-session")
async def get_active_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict]:
    patient_record = await db.get(Patient, {"user_id": current_user.id})
    if not patient_record:
        raise HTTPException(status_code=404, detail="Patient record not found")
    service = PatientPortalAccessService(db)
    active = await service.get_active_session(patient_record.id)
    if not active:
        return success_response(data={"active": False}, message="No active session")
    return success_response(
        data={"active": True, "login_time": active.login_time, "session_id": active.id},
        message="Active session found"
    )