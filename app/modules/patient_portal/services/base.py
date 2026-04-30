# app/modules/patient_portal/patient_portal_access_service.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.common.exceptions.base import PatientNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.patient_portal.models.patient_portal import PatientPortalAccess
from app.modules.patient_portal.schemas.base import PatientPortalAccessCreate, PatientPortalAccessUpdate
from app.modules.patients.models.patient import Patient


class PatientPortalAccessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------
    async def get_access_record(self, record_id: int) -> Optional[PatientPortalAccess]:
        result = await self.db.execute(
            select(PatientPortalAccess).where(PatientPortalAccess.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_access_records(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "login_time",
        descending: bool = True,
    ) -> PaginatedResponse[PatientPortalAccess]:
        query = select(PatientPortalAccess)
        if filters:
            if "patient_id" in filters:
                query = query.where(PatientPortalAccess.patient_id == filters["patient_id"])
            if "ip_address" in filters:
                query = query.where(PatientPortalAccess.ip_address == filters["ip_address"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Order by
        order_col = getattr(PatientPortalAccess, order_by, PatientPortalAccess.login_time)
        if descending:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=page_size,
            pages=pages
        )

    async def create_access_record(self, data: PatientPortalAccessCreate) -> PatientPortalAccess:
        # Validate patient exists
        patient = await self.db.get(Patient, data.patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {data.patient_id} not found")

        record = PatientPortalAccess(
            patient_id=data.patient_id,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            login_time=data.login_time or datetime.utcnow(),
            logout_time=data.logout_time,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def update_access_record(
        self, record_id: int, data: PatientPortalAccessUpdate
    ) -> Optional[PatientPortalAccess]:
        record = await self.get_access_record(record_id)
        if not record:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def delete_access_record(self, record_id: int) -> bool:
        record = await self.get_access_record(record_id)
        if not record:
            return False
        await self.db.delete(record)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities: Login/Logout tracking
    # ------------------------------------------------------------------
    async def record_login(
        self,
        patient_id: int,
        ip_address: str,
        user_agent: str,
    ) -> PatientPortalAccess:
        """
        Create a new access record with login_time = now.
        Automatically logs out any previous active session (if desired).
        """
        # Optional: auto-logout previous active session for same patient
        await self.logout_active_session(patient_id)

        record = PatientPortalAccess(
            patient_id=patient_id,
            ip_address=ip_address,
            user_agent=user_agent,
            login_time=datetime.utcnow(),
            logout_time=None,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def record_logout(self, patient_id: int) -> bool:
        """Logout the currently active session (the one with logout_time IS NULL)."""
        active = await self.get_active_session(patient_id)
        if not active:
            return False
        active.logout_time = datetime.utcnow()
        await self.db.commit()
        return True

    async def get_active_session(self, patient_id: int) -> Optional[PatientPortalAccess]:
        """Find the access record for this patient that has no logout_time."""
        result = await self.db.execute(
            select(PatientPortalAccess).where(
                PatientPortalAccess.patient_id == patient_id,
                PatientPortalAccess.logout_time.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def logout_active_session(self, patient_id: int) -> bool:
        """Force logout of any active session for the patient."""
        active = await self.get_active_session(patient_id)
        if not active:
            return False
        active.logout_time = datetime.utcnow()
        await self.db.commit()
        return True

    async def is_session_active(self, patient_id: int, session_timeout_minutes: int = 30) -> bool:
        """
        Check if a patient has an active session that hasn't timed out.
        Session is considered active if:
        - logout_time is NULL
        - login_time is within timeout period (to handle stale sessions)
        """
        active = await self.get_active_session(patient_id)
        if not active:
            return False
        # Check if login_time is too old (timeout)
        if active.login_time < datetime.utcnow() - timedelta(minutes=session_timeout_minutes):
            # Auto-expire
            await self.logout_active_session(patient_id)
            return False
        return True

    # ------------------------------------------------------------------
    # Additional Utilities
    # ------------------------------------------------------------------
    async def get_patient_access_history(
        self,
        patient_id: int,
        limit: int = 50,
    ) -> List[PatientPortalAccess]:
        """Get all access records for a patient, ordered by login_time DESC."""
        query = (
            select(PatientPortalAccess)
            .where(PatientPortalAccess.patient_id == patient_id)
            .order_by(PatientPortalAccess.login_time.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_statistics(
        self,
        patient_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get access statistics: total logins, unique IPs, average session duration, etc."""
        query = select(PatientPortalAccess)
        if patient_id:
            query = query.where(PatientPortalAccess.patient_id == patient_id)
        if start_date:
            query = query.where(PatientPortalAccess.login_time >= start_date)
        if end_date:
            query = query.where(PatientPortalAccess.login_time <= end_date)

        result = await self.db.execute(query)
        records = result.scalars().all()

        total_logins = len(records)
        unique_ips = set(r.ip_address for r in records if r.ip_address)
        # Calculate average session duration (where logout_time is present)
        durations = []
        for r in records:
            if r.logout_time and r.login_time:
                duration = (r.logout_time - r.login_time).total_seconds() / 60  # minutes
                durations.append(duration)
        avg_duration = sum(durations) / len(durations) if durations else None

        return {
            "total_logins": total_logins,
            "unique_ip_count": len(unique_ips),
            "average_session_minutes": round(avg_duration, 2) if avg_duration else None,
            "record_count": total_logins,
        }

    async def cleanup_stale_sessions(self, timeout_minutes: int = 30) -> int:
        """
        Find all records with login_time older than timeout and logout_time IS NULL,
        then set logout_time = login_time + timeout_minutes.
        Returns count of cleaned records.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        query = select(PatientPortalAccess).where(
            PatientPortalAccess.logout_time.is_(None),
            PatientPortalAccess.login_time < cutoff,
        )
        result = await self.db.execute(query)
        stale = result.scalars().all()
        count = 0
        for record in stale:
            record.logout_time = record.login_time + timedelta(minutes=timeout_minutes)
            count += 1
        await self.db.commit()
        return count