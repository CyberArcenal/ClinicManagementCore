import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.schedule import ScheduleConflictError, ScheduleNotFoundError
from app.modules.schedule.enums.base import WeekDay
from app.modules.schedule.models.schedule import DoctorSchedule
from app.modules.schedule.schema.schedule import DoctorScheduleCreate, DoctorScheduleUpdate
from app.modules.schedule.services.schedule import ScheduleService

@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    return db

@pytest.fixture
def service(mock_db):
    return ScheduleService(mock_db)

# ------------------------------------------------------------------
# Test create_schedule
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_schedule_success(service, mock_db):
    mock_doctor = MagicMock(id=1)
    mock_db.get.return_value = mock_doctor
    # Mock existing schedule check returns None (no conflict)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    data = DoctorScheduleCreate(
        doctor_id=1,
        day_of_week=WeekDay.MON,
        start_time="09:00",
        end_time="17:00",
        is_available=True
    )
    result = await service.create_schedule(data)
    assert result.doctor_id == 1
    assert result.day_of_week == WeekDay.MON
    assert result.start_time == "09:00"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_schedule_doctor_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = DoctorScheduleCreate(doctor_id=999, day_of_week=WeekDay.MON)
    with pytest.raises(DoctorNotFoundError):
        await service.create_schedule(data)

@pytest.mark.asyncio
async def test_create_schedule_conflict(service, mock_db):
    mock_doctor = MagicMock(id=1)
    mock_db.get.return_value = mock_doctor
    # Existing schedule found
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = DoctorSchedule(id=1)
    mock_db.execute.return_value = mock_result
    data = DoctorScheduleCreate(doctor_id=1, day_of_week=WeekDay.MON)
    with pytest.raises(ScheduleConflictError):
        await service.create_schedule(data)

# ------------------------------------------------------------------
# Test get_schedule and get_schedules
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_schedule_found(service, mock_db):
    expected = DoctorSchedule(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_schedule(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_schedule_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_schedule(999)
    assert result is None

@pytest.mark.asyncio
async def test_get_schedules_by_doctor(service, mock_db):
    schedules = [DoctorSchedule(id=1), DoctorSchedule(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = schedules
    mock_db.execute.return_value = mock_result
    result = await service.get_schedules_by_doctor(1, only_available=True)
    assert len(result) == 2

# ------------------------------------------------------------------
# Test update_schedule
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_schedule_success(service, mock_db):
    existing = DoctorSchedule(id=1, start_time="09:00", end_time="17:00")
    mock_db.get.return_value = existing
    update_data = DoctorScheduleUpdate(start_time="10:00", end_time="19:00")
    result = await service.update_schedule(1, update_data)
    assert result.start_time == "10:00"
    assert result.end_time == "19:00"
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_schedule_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(ScheduleNotFoundError):
        await service.update_schedule(999, DoctorScheduleUpdate())

# ------------------------------------------------------------------
# Test delete_schedule
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_schedule_success(service, mock_db):
    existing = DoctorSchedule(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_schedule(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)

@pytest.mark.asyncio
async def test_delete_schedule_not_found(service, mock_db):
    mock_db.get.return_value = None
    result = await service.delete_schedule(999)
    assert result is False

# ------------------------------------------------------------------
# Test set_availability
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_set_availability_success(service, mock_db):
    existing = DoctorSchedule(id=1, is_available=True)
    mock_db.get.return_value = existing
    result = await service.set_availability(1, False)
    assert result.is_available is False
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_set_availability_not_found(service, mock_db):
    mock_db.get.return_value = None
    result = await service.set_availability(999, False)
    assert result is None

# ------------------------------------------------------------------
# Test bulk_create_weekly_schedule
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_bulk_create_weekly_schedule(service, mock_db):
    mock_doctor = MagicMock(id=1)
    mock_db.get.return_value = mock_doctor
    weekly_slots = {
        WeekDay.MON: ("09:00", "17:00"),
        WeekDay.WED: ("09:00", "17:00"),
        WeekDay.FRI: ("09:00", "17:00")
    }
    # For each day, existing check returns None
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    results = await service.bulk_create_weekly_schedule(1, weekly_slots, is_available=True)
    assert len(results) == 3
    assert results[0].day_of_week == WeekDay.MON
    assert results[1].day_of_week == WeekDay.WED
    mock_db.add.assert_called()
    mock_db.commit.assert_awaited_once()