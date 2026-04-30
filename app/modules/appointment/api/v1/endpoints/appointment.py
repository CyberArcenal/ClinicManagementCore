from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import (
    AppointmentConflictError,
    DoctorNotFoundError,
    DoctorUnavailableError,
    InvalidStatusTransitionError,
    PatientNotFoundError,
)
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.appointment.schemas.base import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.modules.appointment.services.base import AppointmentService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[AppointmentResponse]:
    service = AppointmentService(db)
    try:
        appointment = await service.create_appointment(data, created_by_id=current_user.id)
        return success_response(data=appointment, message="Appointment created successfully")
    except (DoctorNotFoundError, PatientNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (AppointmentConflictError, DoctorUnavailableError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/")
async def list_appointments(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[AppointmentResponse]]:
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
    paginated = await service.get_appointments(
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return success_response(data=paginated, message="Appointments retrieved")


@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[AppointmentResponse]:
    service = AppointmentService(db)
    appointment = await service.get_appointment(appointment_id, load_relations=True)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return success_response(data=appointment, message="Appointment retrieved")


@router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[AppointmentResponse]:
    service = AppointmentService(db)
    try:
        appointment = await service.update_appointment(appointment_id, data)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return success_response(data=appointment, message="Appointment updated")
    except (DoctorNotFoundError, PatientNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (AppointmentConflictError, DoctorUnavailableError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = AppointmentService(db)
    deleted = await service.delete_appointment(appointment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return None


@router.patch("/{appointment_id}/status")
async def change_appointment_status(
    appointment_id: int,
    new_status: AppointmentStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[AppointmentResponse]:
    service = AppointmentService(db)
    try:
        appointment = await service.change_status(appointment_id, new_status)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return success_response(data=appointment, message=f"Status changed to {new_status.value}")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/doctors/{doctor_id}/available-slots")
async def get_available_slots(
    doctor_id: int,
    date: datetime = Query(...),
    duration_minutes: int = Query(30, ge=15, le=120),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict]:
    service = AppointmentService(db)
    slots = await service.get_available_slots(
        doctor_id=doctor_id,
        date=date,
        duration_minutes=duration_minutes,
    )
    return success_response(
        data={"doctor_id": doctor_id, "date": date.date(), "available_slots": slots},
        message="Available slots retrieved",
    )