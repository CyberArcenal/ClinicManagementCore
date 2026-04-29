# app/modules/lab/api/v1/endpoints/lab_result.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.post("/", response_model=LabResultResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_request(
    data: LabResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    """
    Create a new lab request (status = PENDING).
    Requires role: doctor (or admin).
    """
    service = LabService(db)
    try:
        lab = await service.create_lab_request(data)
        return lab
    except (PatientNotFoundError, DoctorNotFoundError, EHRNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[LabResultResponse])
async def list_lab_results(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status_filter: Optional[LabStatus] = Query(None, alias="status"),
    test_name_contains: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
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
    if status_filter:
        filters["status"] = status_filter
    if test_name_contains:
        filters["test_name_contains"] = test_name_contains
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    service = LabService(db)
    results = await service.get_lab_results(filters=filters, skip=skip, limit=limit)

    # Role-based filtering
    if current_user.role == "patient":
        # Patient sees only their own records
        from app.modules.patient.models import Patient
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if patient_record:
            results = [r for r in results if r.patient_id == patient_record.id]
        else:
            results = []
    elif current_user.role == "doctor":
        from app.modules.doctor.models import DoctorProfile
        doctor_profile = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if doctor_profile:
            results = [r for r in results if r.requested_by_id == doctor_profile.id]
        else:
            results = []
    # Lab tech sees all? Could add filter for performed_by, but let's keep simple

    return results


@router.get("/{lab_id}", response_model=LabResultResponse)
async def get_lab_result(
    lab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LabService(db)
    lab = await service.get_lab_result(lab_id, load_relations=True)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab result not found")
    # Authorization check
    if current_user.role == "patient":
        from app.modules.patient.models import Patient
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient_record or lab.patient_id != patient_record.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor":
        from app.modules.doctor.models import DoctorProfile
        doctor_profile = await service.db.get(DoctorProfile, {"user_id": current_user.id})
        if not doctor_profile or lab.requested_by_id != doctor_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return lab


@router.put("/{lab_id}", response_model=LabResultResponse)
async def update_lab_result(
    lab_id: int,
    data: LabResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("lab_tech")),
):
    """
    Update lab result (mainly for lab technicians to add results, normal range, etc.)
    """
    service = LabService(db)
    try:
        lab = await service.update_lab_result(lab_id, data)
        if not lab:
            raise HTTPException(status_code=404, detail="Lab result not found")
        return lab
    except LabResultNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab_result(
    lab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = LabService(db)
    try:
        deleted = await service.delete_lab_result(lab_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Lab result not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{lab_id}/start", response_model=LabResultResponse)
async def start_lab_processing(
    lab_id: int,
    performed_by_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("lab_tech")),
):
    service = LabService(db)
    try:
        lab = await service.start_lab_processing(lab_id, performed_by_id)
        if not lab:
            raise HTTPException(status_code=404, detail="Lab result not found")
        return lab
    except (InvalidLabStatusTransitionError, LabTechNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{lab_id}/complete", response_model=LabResultResponse)
async def complete_lab_result(
    lab_id: int,
    result_data: str = Query(..., description="Test results in JSON or text"),
    remarks: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("lab_tech")),
):
    service = LabService(db)
    try:
        lab = await service.complete_lab_result(lab_id, result_data, remarks)
        if not lab:
            raise HTTPException(status_code=404, detail="Lab result not found")
        return lab
    except InvalidLabStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{lab_id}/cancel", response_model=LabResultResponse)
async def cancel_lab_request(
    lab_id: int,
    reason: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    service = LabService(db)
    try:
        lab = await service.cancel_lab_request(lab_id, reason)
        if not lab:
            raise HTTPException(status_code=404, detail="Lab result not found")
        return lab
    except InvalidLabStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}/history", response_model=List[LabResultResponse])
async def get_patient_lab_history(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LabService(db)
    # Authorization: patient sees own, doctor sees any, admin sees any
    if current_user.role == "patient":
        from app.modules.patient.models import Patient
        patient_record = await service.db.get(Patient, {"user_id": current_user.id})
        if not patient_record or patient_record.id != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")
    history = await service.get_patient_lab_history(patient_id, limit=limit)
    return history


@router.get("/pending", response_model=List[LabResultResponse])
async def get_pending_lab_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("lab_tech")),
):
    service = LabService(db)
    pending = await service.get_pending_lab_requests()
    return pending