import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import PatientNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.modules.patients.models.models import Patient
from app.modules.patients.schemas.base import PatientCreate, PatientUpdate
from app.modules.patients.services.patient import PatientService
from app.modules.user.models.base import User


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
    return PatientService(mock_db)

# ------------------------------------------------------------------
# Test create_patient
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_patient_success(service, mock_db):
    mock_user = MagicMock(spec=User)
    mock_db.get.return_value = mock_user
    data = PatientCreate(
        user_id=1,
        date_of_birth=datetime(1990, 1, 1),
        gender="M",
        blood_type="A+",
        address="123 Main St",
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="1234567890"
    )
    result = await service.create_patient(data)
    assert result.user_id == 1
    assert result.gender == "M"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_patient_user_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = PatientCreate(user_id=999, date_of_birth=datetime.now())
    with pytest.raises(UserNotFoundError):
        await service.create_patient(data)

# ------------------------------------------------------------------
# Test get_patient and get_patients
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_patient_found(service, mock_db):
    expected = Patient(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_patient(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_patient_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_patient(999)
    assert result is None

@pytest.mark.asyncio
async def test_get_patient_by_user_id(service, mock_db):
    expected = Patient(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_patient_by_user_id(1)
    assert result == expected

# ------------------------------------------------------------------
# Test update_patient
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_patient_success(service, mock_db):
    existing = Patient(id=1, gender="M", blood_type="A+")
    mock_db.get.return_value = existing
    update_data = PatientUpdate(gender="F")
    result = await service.update_patient(1, update_data)
    assert result.gender == "F"
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_patient_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(PatientNotFoundError):
        await service.update_patient(999, PatientUpdate())

# ------------------------------------------------------------------
# Test delete_patient
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_patient_success(service, mock_db):
    existing = Patient(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_patient(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)

@pytest.mark.asyncio
async def test_delete_patient_not_found(service, mock_db):
    mock_db.get.return_value = None
    result = await service.delete_patient(999)
    assert result is False

# ------------------------------------------------------------------
# Test search_patients
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_search_patients(service, mock_db):
    patients = [Patient(id=1), Patient(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = patients
    mock_db.execute.return_value = mock_result
    result = await service.search_patients("john", skip=0, limit=10)
    assert len(result) == 2

# ------------------------------------------------------------------
# Test get_patient_summary
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_patient_summary(service, mock_db):
    patient = Patient(id=1)
    mock_db.get.return_value = patient
    # Mock counts for each relationship
    mock_scalar = AsyncMock()
    mock_scalar.side_effect = [5, 3, 8, 2, 4, 3]  # appointment, prescription, ehr, lab, invoice, payment
    mock_db.scalar = mock_scalar
    summary = await service.get_patient_summary(1)
    assert summary["appointment_count"] == 5
    assert summary["prescription_count"] == 3
    assert summary["ehr_record_count"] == 8
    assert summary["lab_result_count"] == 2
    assert summary["invoice_count"] == 4
    assert summary["payment_count"] == 3

# ------------------------------------------------------------------
# Test get_patients_birthday_today
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_birthdays_today(service, mock_db):
    patients = [Patient(id=1), Patient(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = patients
    mock_db.execute.return_value = mock_result
    result = await service.get_patients_birthday_today()
    assert len(result) == 2