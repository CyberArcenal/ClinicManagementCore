# app/modules/schedule/api/v1/endpoints/schedule.py
from typing import List, Optional
from datetime import time, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.user.models import User


router = APIRouter()


@router.post("/", response_model=DoctorScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: DoctorScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Create a schedule for a doctor (working hours on a specific day of week).
    """
    service = ScheduleService(db)
    try:
        schedule = await service.create_schedule(data)
        return schedule
    except (DoctorNotFoundError, ScheduleConflictError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/weekly", response_model=List[DoctorScheduleResponse])
async def create_weekly_schedule(
    doctor_id: int,
    weekly_slots: dict,  # Expecting {"monday": ["09:00","17:00"], "tuesday": [...], ...}
    is_available: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
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
        # Convert dict keys to WeekDay enum values
        converted = {}
        for day_str, times in weekly_slots.items():
            # Expect day_str like "monday" -> WeekDay.MON
            day_enum = WeekDay[day_str.upper()]
            converted[day_enum] = (times[0], times[1])
        schedules = await service.bulk_create_weekly_schedule(
            doctor_id, converted, is_available
        )
        return schedules
    except DoctorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[DoctorScheduleResponse])
async def list_schedules(
    doctor_id: Optional[int] = Query(None),
    day_of_week: Optional[WeekDayEnum] = Query(None),
    is_available: Optional[bool] = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {}
    if doctor_id:
        filters["doctor_id"] = doctor_id
    if day_of_week:
        filters["day_of_week"] = day_of_week
    if is_available is not None:
        filters["is_available"] = is_available

    service = ScheduleService(db)
    schedules = await service.get_schedules(filters=filters, skip=skip, limit=limit)
    return schedules


@router.get("/doctor/{doctor_id}", response_model=List[DoctorScheduleResponse])
async def get_doctor_schedules(
    doctor_id: int,
    only_available: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScheduleService(db)
    schedules = await service.get_schedules_by_doctor(doctor_id, only_available=only_available)
    return schedules


@router.get("/{schedule_id}", response_model=DoctorScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScheduleService(db)
    schedule = await service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/{schedule_id}", response_model=DoctorScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: DoctorScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ScheduleService(db)
    try:
        schedule = await service.update_schedule(schedule_id, data)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule
    except ScheduleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{schedule_id}/availability", response_model=DoctorScheduleResponse)
async def set_schedule_availability(
    schedule_id: int,
    is_available: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("receptionist")),
):
    service = ScheduleService(db)
    schedule = await service.set_availability(schedule_id, is_available)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ScheduleService(db)
    deleted = await service.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return None


@router.delete("/doctor/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_schedules_for_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = ScheduleService(db)
    deleted = await service.delete_all_schedules_for_doctor(doctor_id)
    return {"message": f"Deleted {deleted} schedule(s) for doctor {doctor_id}"}