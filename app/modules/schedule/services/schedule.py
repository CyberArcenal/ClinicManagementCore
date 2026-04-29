# app/modules/schedule/schedule_service.py
from datetime import datetime, time, timedelta, date
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from app.modules.schedule.models import DoctorSchedule, WeekDay
from app.modules.schedule.schemas import (
    DoctorScheduleCreate,
    DoctorScheduleUpdate,
    WeekDayEnum,
)
from app.modules.doctor.models import DoctorProfile
from app.common.exceptions import (
    DoctorNotFoundError,
    ScheduleNotFoundError,
    ScheduleConflictError,
)


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD for DoctorSchedule
    # ------------------------------------------------------------------
    async def get_schedule(self, schedule_id: int) -> Optional[DoctorSchedule]:
        result = await self.db.execute(
            select(DoctorSchedule).where(DoctorSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_schedules_by_doctor(
        self, doctor_id: int, only_available: bool = True
    ) -> List[DoctorSchedule]:
        query = select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
        if only_available:
            query = query.where(DoctorSchedule.is_available == True)
        query = query.order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_schedules(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DoctorSchedule]:
        query = select(DoctorSchedule)
        if filters:
            if "doctor_id" in filters:
                query = query.where(DoctorSchedule.doctor_id == filters["doctor_id"])
            if "day_of_week" in filters:
                query = query.where(DoctorSchedule.day_of_week == filters["day_of_week"])
            if "is_available" in filters:
                query = query.where(DoctorSchedule.is_available == filters["is_available"])
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_schedule(self, data: DoctorScheduleCreate) -> DoctorSchedule:
        # Check if doctor exists
        doctor = await self.db.get(DoctorProfile, data.doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {data.doctor_id} not found")

        # Check for overlapping schedule on same day (a doctor should have only one schedule per day)
        existing = await self.db.execute(
            select(DoctorSchedule).where(
                DoctorSchedule.doctor_id == data.doctor_id,
                DoctorSchedule.day_of_week == data.day_of_week
            )
        )
        if existing.scalar_one_or_none():
            raise ScheduleConflictError(
                f"Doctor {data.doctor_id} already has a schedule on {data.day_of_week.value}"
            )

        schedule = DoctorSchedule(
            doctor_id=data.doctor_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            is_available=data.is_available,
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def update_schedule(
        self, schedule_id: int, data: DoctorScheduleUpdate
    ) -> Optional[DoctorSchedule]:
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(schedule, key, value)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: int) -> bool:
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            return False
        await self.db.delete(schedule)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def set_availability(self, schedule_id: int, is_available: bool) -> Optional[DoctorSchedule]:
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            return None
        schedule.is_available = is_available
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def bulk_create_weekly_schedule(
        self,
        doctor_id: int,
        weekly_slots: Dict[WeekDay, tuple[str, str]],  # {Monday: ("09:00","17:00"), ...}
        is_available: bool = True,
    ) -> List[DoctorSchedule]:
        """Create schedules for multiple days at once."""
        doctor = await self.db.get(DoctorProfile, doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {doctor_id} not found")

        created = []
        for day, (start, end) in weekly_slots.items():
            # check if already exists
            existing = await self.db.execute(
                select(DoctorSchedule).where(
                    DoctorSchedule.doctor_id == doctor_id,
                    DoctorSchedule.day_of_week == day
                )
            )
            if existing.scalar_one_or_none():
                continue  # skip or raise? we skip to avoid conflict
            schedule = DoctorSchedule(
                doctor_id=doctor_id,
                day_of_week=day,
                start_time=start,
                end_time=end,
                is_available=is_available,
            )
            self.db.add(schedule)
            created.append(schedule)
        await self.db.commit()
        for s in created:
            await self.db.refresh(s)
        return created

    async def delete_all_schedules_for_doctor(self, doctor_id: int) -> int:
        result = await self.db.execute(
            delete(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
        )
        await self.db.commit()
        return result.rowcount

    # ------------------------------------------------------------------
    # Availability checking
    # ------------------------------------------------------------------
    async def is_doctor_available_at(
        self, doctor_id: int, appointment_datetime: datetime, duration_minutes: int = 30
    ) -> bool:
        """
        Check if doctor is available for an appointment at given time.
        Checks:
        1. Day of week matches schedule and within working hours
        2. No overlapping appointments (may delegate to appointment service)
        """
        # Get weekday as enum value
        weekday_map = {
            0: WeekDay.MON, 1: WeekDay.TUE, 2: WeekDay.WED,
            3: WeekDay.THU, 4: WeekDay.FRI, 5: WeekDay.SAT, 6: WeekDay.SUN
        }
        day_of_week = weekday_map[appointment_datetime.weekday()]
        # Get schedule for that day
        schedule = await self.db.execute(
            select(DoctorSchedule).where(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.day_of_week == day_of_week,
                DoctorSchedule.is_available == True,
            )
        )
        schedule = schedule.scalar_one_or_none()
        if not schedule:
            return False

        # Parse time strings into time objects for comparison
        start_time = datetime.strptime(schedule.start_time, "%H:%M").time()
        end_time = datetime.strptime(schedule.end_time, "%H:%M").time()
        appointment_time = appointment_datetime.time()
        appointment_end = (appointment_datetime + timedelta(minutes=duration_minutes)).time()

        if appointment_time < start_time or appointment_end > end_time:
            return False

        # To check overlapping appointments, we need AppointmentService, but we avoid circular import.
        # We'll leave that to a higher-level service or pass appointment service instance.
        # Return True for now assuming no conflict; actual conflict check should be done by appointment service.
        return True

    async def get_available_time_slots(
        self,
        doctor_id: int,
        target_date: date,
        duration_minutes: int = 30,
        slot_interval_minutes: int = 30,
        existing_appointments: List[tuple[datetime, datetime]] = None,
    ) -> List[datetime]:
        """
        Get list of available start times for a given date.
        `existing_appointments` should be list of (start, end) datetime pairs from appointment service.
        """
        # Get doctor schedule for that weekday
        weekday_map = {0: WeekDay.MON, 1: WeekDay.TUE, 2: WeekDay.WED,
                       3: WeekDay.THU, 4: WeekDay.FRI, 5: WeekDay.SAT, 6: WeekDay.SUN}
        day_of_week = weekday_map[target_date.weekday()]
        schedule = await self.db.execute(
            select(DoctorSchedule).where(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.day_of_week == day_of_week,
                DoctorSchedule.is_available == True,
            )
        )
        schedule = schedule.scalar_one_or_none()
        if not schedule:
            return []

        start_dt = datetime.combine(target_date, datetime.strptime(schedule.start_time, "%H:%M").time())
        end_dt = datetime.combine(target_date, datetime.strptime(schedule.end_time, "%H:%M").time())

        slots = []
        current = start_dt
        while current + timedelta(minutes=duration_minutes) <= end_dt:
            slot_end = current + timedelta(minutes=duration_minutes)
            # Check if slot overlaps with any existing appointment
            conflict = False
            if existing_appointments:
                for apt_start, apt_end in existing_appointments:
                    if max(current, apt_start) < min(slot_end, apt_end):
                        conflict = True
                        break
            if not conflict:
                slots.append(current)
            current += timedelta(minutes=slot_interval_minutes)
        return slots