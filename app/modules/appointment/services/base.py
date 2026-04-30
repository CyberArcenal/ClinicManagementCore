# app/modules/appointment/service.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, or_, update, delete
from sqlalchemy.orm import selectinload

from app.common.exceptions.base import AppointmentConflictError, DoctorNotFoundError, DoctorUnavailableError, InvalidStatusTransitionError, PatientNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.appointment.models.appointment import Appointment
from app.modules.appointment.schemas.base import AppointmentCreate, AppointmentUpdate
from app.modules.patients.models.patient import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_appointment(
        self, appointment_id: int, load_relations: bool = False
    ) -> Optional[Appointment]:
        """Get single appointment by ID."""
        query = select(Appointment).where(Appointment.id == appointment_id)
        if load_relations:
            query = query.options(
                selectinload(Appointment.patient),
                selectinload(Appointment.doctor),
                selectinload(Appointment.created_by),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_appointments(
    self,
    filters: Dict[str, Any] = None,
    page: int = 1,
    page_size: int = 100,
    order_by: str = "appointment_datetime",
    descending: bool = False,
) -> PaginatedResponse[Appointment]:
        """
        List appointments with optional filters, paginated by page/page_size.
        """
        # Base query
        query = select(Appointment)

        # Apply filters (same as before)
        if filters:
            if "patient_id" in filters:
                query = query.where(Appointment.patient_id == filters["patient_id"])
            if "doctor_id" in filters:
                query = query.where(Appointment.doctor_id == filters["doctor_id"])
            if "status" in filters:
                query = query.where(Appointment.status == filters["status"])
            if "date_from" in filters:
                query = query.where(Appointment.appointment_datetime >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(Appointment.appointment_datetime <= filters["date_to"])

        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply ordering
        order_column = getattr(Appointment, order_by, Appointment.appointment_datetime)
        if descending:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        # Calculate total pages
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=page_size,
            pages=pages
        )

    async def create_appointment(
        self, data: AppointmentCreate, created_by_id: Optional[int] = None
    ) -> Appointment:
        """Create a new appointment with validation."""
        # 1. Validate patient and doctor exist
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")
        doctor = await self.db.get(DoctorProfile, data.doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor {data.doctor_id} not found")

        # 2. Check doctor availability (working hours, not overlapping)
        await self._validate_doctor_availability(
            doctor_id=data.doctor_id,
            start_time=data.appointment_datetime,
            duration=data.duration_minutes,
            exclude_appointment_id=None,
        )

        # 3. Create appointment
        appointment = Appointment(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            appointment_datetime=data.appointment_datetime,
            duration_minutes=data.duration_minutes,
            status=data.status,
            reason=data.reason,
            notes=data.notes,
            created_by_id=created_by_id,
        )
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def update_appointment(
        self, appointment_id: int, data: AppointmentUpdate, updated_by_id: Optional[int] = None
    ) -> Optional[Appointment]:
        """Update an existing appointment."""
        appointment = await self.get_appointment(appointment_id)
        if not appointment:
            return None

        # If changing datetime or doctor, validate availability
        new_datetime = data.appointment_datetime or appointment.appointment_datetime
        new_doctor_id = data.doctor_id or appointment.doctor_id
        new_duration = data.duration_minutes or appointment.duration_minutes

        if (data.appointment_datetime is not None and data.appointment_datetime != appointment.appointment_datetime) or \
           (data.doctor_id is not None and data.doctor_id != appointment.doctor_id) or \
           (data.duration_minutes is not None and data.duration_minutes != appointment.duration_minutes):

            await self._validate_doctor_availability(
                doctor_id=new_doctor_id,
                start_time=new_datetime,
                duration=new_duration,
                exclude_appointment_id=appointment_id,
            )

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(appointment, key, value)

        # Optionally log who updated (if you have an updated_by field, add it)
        # appointment.updated_by_id = updated_by_id

        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def delete_appointment(self, appointment_id: int) -> bool:
        """Hard delete an appointment."""
        appointment = await self.get_appointment(appointment_id)
        if not appointment:
            return False
        await self.db.delete(appointment)
        await self.db.commit()
        return True

    async def change_status(
        self, appointment_id: int, new_status: AppointmentStatus, user_role: str = None
    ) -> Optional[Appointment]:
        """Change appointment status with allowed transitions validation."""
        appointment = await self.get_appointment(appointment_id)
        if not appointment:
            return None

        # Define allowed transitions (simplified)
        allowed = {
            AppointmentStatus.SCHEDULED: [AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED],
            AppointmentStatus.CONFIRMED: [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED],
            AppointmentStatus.COMPLETED: [],  # terminal
            AppointmentStatus.CANCELLED: [],  # terminal
            AppointmentStatus.NO_SHOW: [AppointmentStatus.CANCELLED],
        }
        if new_status not in allowed.get(appointment.status, []):
            raise InvalidStatusTransitionError(
                f"Cannot change from {appointment.status.value} to {new_status.value}"
            )

        appointment.status = new_status
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    async def _validate_doctor_availability(
        self,
        doctor_id: int,
        start_time: datetime,
        duration: int,
        exclude_appointment_id: Optional[int] = None,
    ) -> None:
        """
        Check if doctor is available at given datetime.
        Raises DoctorUnavailableError or AppointmentConflictError.
        """
        # 1. Check working hours (example: 9am-5pm weekdays)
        if not self._is_within_working_hours(start_time, duration):
            raise DoctorUnavailableError("Appointment time outside doctor's working hours")

        # 2. Check for overlapping appointments
        end_time = start_time + timedelta(minutes=duration)
        query = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
            or_(
                and_(
                    Appointment.appointment_datetime <= start_time,
                    Appointment.appointment_datetime + timedelta(minutes=Appointment.duration_minutes) > start_time,
                ),
                and_(
                    Appointment.appointment_datetime >= start_time,
                    Appointment.appointment_datetime < end_time,
                ),
            ),
        )
        if exclude_appointment_id:
            query = query.where(Appointment.id != exclude_appointment_id)

        result = await self.db.execute(query)
        overlapping = result.scalars().first()
        if overlapping:
            raise AppointmentConflictError(
                f"Doctor {doctor_id} already has an appointment at {overlapping.appointment_datetime}"
            )

    @staticmethod
    def _is_within_working_hours(dt: datetime, duration_minutes: int) -> bool:
        """Check if appointment time falls within clinic's working hours (e.g., Mon-Fri 9:00-17:00)."""
        # Example implementation: can be overridden via settings
        if dt.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
        start_hour = dt.hour + dt.minute / 60.0
        end_hour = (dt + timedelta(minutes=duration_minutes)).hour + (dt + timedelta(minutes=duration_minutes)).minute / 60.0
        if start_hour < 9.0 or end_hour > 17.0:
            return False
        return True

    async def get_available_slots(
        self,
        doctor_id: int,
        date: datetime,
        duration_minutes: int = 30,
        interval_minutes: int = 30,
    ) -> List[datetime]:
        """Get all free time slots for a doctor on a given date."""
        start_of_day = datetime.combine(date.date(), datetime.min.time())
        end_of_day = datetime.combine(date.date(), datetime.max.time())

        # Get all appointments for that doctor on that day
        query = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_datetime >= start_of_day,
            Appointment.appointment_datetime <= end_of_day,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
        )
        result = await self.db.execute(query)
        appointments = result.scalars().all()

        # Generate all possible slots (9am-5pm, step = interval_minutes)
        slots = []
        current = datetime.combine(date.date(), datetime.min.time().replace(hour=9))
        end = datetime.combine(date.date(), datetime.min.time().replace(hour=17))
        while current + timedelta(minutes=duration_minutes) <= end:
            slots.append(current)
            current += timedelta(minutes=interval_minutes)

        # Remove slots that overlap with existing appointments
        available = []
        for slot in slots:
            slot_end = slot + timedelta(minutes=duration_minutes)
            conflict = False
            for apt in appointments:
                apt_end = apt.appointment_datetime + timedelta(minutes=apt.duration_minutes)
                if max(slot, apt.appointment_datetime) < min(slot_end, apt_end):
                    conflict = True
                    break
            if not conflict:
                available.append(slot)
        return available