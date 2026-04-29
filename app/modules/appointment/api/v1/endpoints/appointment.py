# app/modules/appointment/api.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import AppointmentConflictError, DoctorNotFoundError, DoctorUnavailableError, InvalidStatusTransitionError, PatientNotFoundError
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.appointment.schemas.base import AppointmentCreate, AppointmentResponse, AppointmentUpdate


from app.modules.appointment.services.base import AppointmentService
from app.modules.user.models import User

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    """
    Create a new appointment.
    Requires role: receptionist, admin, or doctor (depending on policy).
    """
    service = AppointmentService(db)
    try:
        appointment = await service.create_appointment(
            data, created_by_id=current_user.id
        )
        return appointment
    except (DoctorNotFoundError, PatientNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (AppointmentConflictError, DoctorUnavailableError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List appointments with filters.
    Accessible by all authenticated users (filtered by role in service?).
    """
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if doctor_id:
        filters["doctor_id"] = doctor_id
    if status:
        filters["status"] = status
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    service = AppointmentService(db)
    appointments = await service.get_appointments(
        filters=filters, skip=skip, limit=limit
    )
    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AppointmentService(db)
    appointment = await service.get_appointment(appointment_id, load_relations=True)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    # Optional: check if user has access (patient sees own, doctor sees own, etc.)
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = AppointmentService(db)
    try:
        appointment = await service.update_appointment(appointment_id, data)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appointment
    except (DoctorNotFoundError, PatientNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (AppointmentConflictError, DoctorUnavailableError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = AppointmentService(db)
    deleted = await service.delete_appointment(appointment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return None


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def change_appointment_status(
    appointment_id: int,
    new_status: AppointmentStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = AppointmentService(db)
    try:
        appointment = await service.change_status(appointment_id, new_status)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appointment
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/doctors/{doctor_id}/available-slots")
async def get_available_slots(
    doctor_id: int,
    date: datetime = Query(..., description="Date for which to get slots (e.g., 2025-01-15)"),
    duration_minutes: int = Query(30, ge=15, le=120),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get available time slots for a doctor on a specific date.
    """
    service = AppointmentService(db)
    slots = await service.get_available_slots(
        doctor_id=doctor_id,
        date=date,
        duration_minutes=duration_minutes,
    )
    return {"doctor_id": doctor_id, "date": date.date(), "available_slots": slots}