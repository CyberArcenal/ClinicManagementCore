from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.schedule import ScheduleConflictError, ScheduleNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.schedule.enums.base import WeekDay
from app.modules.schedule.schema.schedule import (
    DoctorScheduleCreate,
    DoctorScheduleResponse,
    DoctorScheduleUpdate,
)
from app.modules.schedule.services.schedule import ScheduleService
from app.modules.user.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: DoctorScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[DoctorScheduleResponse]:
    service = ScheduleService(db)
    try:
        schedule = await service.create_schedule(data)
        return success_response(data=schedule, message="Doctor schedule created")
    except (DoctorNotFoundError, ScheduleConflictError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/weekly")
async def create_weekly_schedule(
    doctor_id: int,
    weekly_slots: dict,
    is_available: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[list[DoctorScheduleResponse]]:
    """
    Bulk create schedules for a doctor for multiple weekdays.
    Example format:
    {
        "monday": ["09:00", "17:00"],
        "tuesday": ["09:00", "17:00"],
        "wednesday": ["09:00", "17:00"],
        "thursday": ["09:00", "17:00"],
        "friday": ["09:00", "17:00"]
    }
    """
    from app.modules.schedule.models import WeekDay
    service = ScheduleService(db)
    try:
        converted = {}
        for day_str, times in weekly_slots.items():
            day_enum = WeekDay[day_str.upper()]
            converted[day_enum] = (times[0], times[1])
        schedules = await service.bulk_create_weekly_schedule(
            doctor_id, converted, is_available
        )
        return success_response(data=schedules, message="Weekly schedules created")
    except DoctorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_schedules(
    doctor_id: Optional[int] = Query(None),
    day_of_week: Optional[WeekDay] = Query(None),
    is_available: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[DoctorScheduleResponse]]:
    filters = {}
    if doctor_id:
        filters["doctor_id"] = doctor_id
    if day_of_week:
        filters["day_of_week"] = day_of_week
    if is_available is not None:
        filters["is_available"] = is_available

    service = ScheduleService(db)
    paginated = await service.get_schedules(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return success_response(data=paginated, message="Schedules retrieved")


@router.get("/doctor/{doctor_id}")
async def get_doctor_schedules(
    doctor_id: int,
    only_available: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[DoctorScheduleResponse]]:
    service = ScheduleService(db)
    schedules = await service.get_schedules_by_doctor(doctor_id, only_available=only_available)
    return success_response(data=schedules, message="Doctor schedules retrieved")


@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[DoctorScheduleResponse]:
    service = ScheduleService(db)
    schedule = await service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return success_response(data=schedule, message="Schedule retrieved")


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    data: DoctorScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[DoctorScheduleResponse]:
    service = ScheduleService(db)
    try:
        schedule = await service.update_schedule(schedule_id, data)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return success_response(data=schedule, message="Schedule updated")
    except ScheduleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{schedule_id}/availability")
async def set_schedule_availability(
    schedule_id: int,
    is_available: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
) -> SuccessResponse[DoctorScheduleResponse]:
    service = ScheduleService(db)
    schedule = await service.set_availability(schedule_id, is_available)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return success_response(data=schedule, message=f"Availability set to {is_available}")


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = ScheduleService(db)
    deleted = await service.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return None


@router.delete("/doctor/{doctor_id}")
async def delete_all_schedules_for_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    service = ScheduleService(db)
    deleted = await service.delete_all_schedules_for_doctor(doctor_id)
    return success_response(
        data={"deleted_count": deleted},
        message=f"Deleted {deleted} schedule(s) for doctor {doctor_id}"
    )