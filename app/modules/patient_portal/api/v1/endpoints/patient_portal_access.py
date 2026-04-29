# app/modules/patient_portal/api/v1/endpoints/patient_portal_access.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=PatientPortalAccessResponse, status_code=status.HTTP_201_CREATED)
async def create_access_record(
    data: PatientPortalAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    """
    Create an access record manually (e.g., when a patient logs in via portal).
    Usually this is called automatically, but provided for admin use.
    """
    service = PatientPortalAccessService(db)
    try:
        record = await service.create_access_record(data)
        return record
    except PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[PatientPortalAccessResponse])
async def list_access_records(
    patient_id: Optional[int] = Query(None),
    ip_address: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    List all portal access records (admin only).
    """
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if ip_address:
        filters["ip_address"] = ip_address
    service = PatientPortalAccessService(db)
    records = await service.get_access_records(filters=filters, skip=skip, limit=limit)
    return records


@router.get("/{record_id}", response_model=PatientPortalAccessResponse)
async def get_access_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PatientPortalAccessService(db)
    record = await service.get_access_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Access record not found")
    return record


@router.put("/{record_id}", response_model=PatientPortalAccessResponse)
async def update_access_record(
    record_id: int,
    data: PatientPortalAccessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PatientPortalAccessService(db)
    record = await service.update_access_record(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Access record not found")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_access_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = PatientPortalAccessService(db)
    deleted = await service.delete_access_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Access record not found")
    return None


# ------------------------------------------------------------------
# Patient-facing endpoints (for portal functionality)
# ------------------------------------------------------------------
@router.post("/login")
async def portal_login(
    patient_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record patient login to portal.
    """
    # Authorization: patient can only record their own login
    from app.modules.patient.models import Patient
    patient_record = await db.get(Patient, patient_id)
    if not patient_record or patient_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    service = PatientPortalAccessService(db)
    record = await service.record_login(patient_id, ip_address or "unknown", user_agent or "unknown")
    return {"message": "Login recorded", "session_id": record.id}


@router.post("/logout")
async def portal_logout(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record patient logout from portal.
    """
    from app.modules.patient.models import Patient
    patient_record = await db.get(Patient, patient_id)
    if not patient_record or patient_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    service = PatientPortalAccessService(db)
    success = await service.record_logout(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="No active session found")
    return {"message": "Logout recorded"}


@router.get("/me/history", response_model=List[PatientPortalAccessResponse])
async def get_my_access_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current patient's own access history.
    """
    from app.modules.patient.models import Patient
    patient_record = await db.get(Patient, {"user_id": current_user.id})
    if not patient_record:
        raise HTTPException(status_code=404, detail="Patient record not found")
    service = PatientPortalAccessService(db)
    history = await service.get_patient_access_history(patient_record.id, limit=limit)
    return history


@router.get("/me/active-session")
async def get_active_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if current patient has an active portal session.
    """
    from app.modules.patient.models import Patient
    patient_record = await db.get(Patient, {"user_id": current_user.id})
    if not patient_record:
        raise HTTPException(status_code=404, detail="Patient record not found")
    service = PatientPortalAccessService(db)
    active = await service.get_active_session(patient_record.id)
    if not active:
        return {"active": False}
    return {"active": True, "login_time": active.login_time, "session_id": active.id}