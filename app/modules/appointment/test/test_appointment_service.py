import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import AppointmentConflictError, DoctorNotFoundError, InvalidStatusTransitionError, PatientNotFoundError
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.appointment.models.appointment import Appointment
from app.modules.appointment.schemas.base import AppointmentCreate
from app.modules.appointment.services.base import AppointmentService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------
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
    return AppointmentService(mock_db)

# ------------------------------------------------------------------
# Test create_appointment
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_appointment_success(service, mock_db):
    # Arrange: patient and doctor exist
    mock_patient = MagicMock(id=1)
    mock_doctor = MagicMock(id=1)
    mock_db.get.side_effect = [mock_patient, mock_doctor]
    
    # Mock validation method to do nothing
    with patch.object(service, '_validate_doctor_availability', new_callable=AsyncMock):
        data = AppointmentCreate(
            patient_id=1,
            doctor_id=1,
            appointment_datetime=datetime.now() + timedelta(days=1),
            duration_minutes=30,
            reason="Annual checkup"
        )
        # Act
        result = await service.create_appointment(data, created_by_id=2)
        # Assert
        assert result.patient_id == 1
        assert result.doctor_id == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_appointment_patient_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = AppointmentCreate(patient_id=999, doctor_id=1, appointment_datetime=datetime.now())
    with pytest.raises(PatientNotFoundError):
        await service.create_appointment(data)

@pytest.mark.asyncio
async def test_create_appointment_doctor_not_found(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_db.get.side_effect = [mock_patient, None]
    data = AppointmentCreate(patient_id=1, doctor_id=999, appointment_datetime=datetime.now())
    with pytest.raises(DoctorNotFoundError):
        await service.create_appointment(data)

@pytest.mark.asyncio
async def test_create_appointment_conflict(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_doctor = MagicMock(id=1)
    mock_db.get.side_effect = [mock_patient, mock_doctor]
    # Simulate availability check raising conflict
    with patch.object(service, '_validate_doctor_availability', side_effect=AppointmentConflictError("Conflict")):
        data = AppointmentCreate(patient_id=1, doctor_id=1, appointment_datetime=datetime.now())
        with pytest.raises(AppointmentConflictError):
            await service.create_appointment(data)

# ------------------------------------------------------------------
# Test get_appointment
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_appointment_found(service, mock_db):
    expected_appt = Appointment(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected_appt
    mock_db.execute.return_value = mock_result
    result = await service.get_appointment(1)
    assert result == expected_appt

@pytest.mark.asyncio
async def test_get_appointment_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_appointment(999)
    assert result is None

# ------------------------------------------------------------------
# Test change_status
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_change_status_valid(service, mock_db):
    appt = Appointment(id=1, status=AppointmentStatus.SCHEDULED)
    mock_db.get.return_value = appt
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    result = await service.change_status(1, AppointmentStatus.CONFIRMED)
    assert result.status == AppointmentStatus.CONFIRMED

@pytest.mark.asyncio
async def test_change_status_invalid_transition(service, mock_db):
    appt = Appointment(id=1, status=AppointmentStatus.COMPLETED)
    mock_db.get.return_value = appt
    with pytest.raises(InvalidStatusTransitionError):
        await service.change_status(1, AppointmentStatus.SCHEDULED)

# ------------------------------------------------------------------
# Test get_available_slots (simplified)
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_available_slots(service, mock_db):
    # Prepare mock appointments – none on that day
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result
    target_date = datetime(2025, 6, 1)
    slots = await service.get_available_slots(doctor_id=1, date=target_date, duration_minutes=30)
    # Should return all slots between 9AM and 5PM
    assert len(slots) > 0
    assert slots[0].hour >= 9
    assert slots[-1].hour + (slots[-1].minute/60) <= 17