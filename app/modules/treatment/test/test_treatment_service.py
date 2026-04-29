import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.staff import NurseNotFoundError
from app.common.exceptions.treatment import TreatmentNotFoundError
from app.modules.treatment.models.models import Treatment
from app.modules.treatment.schemas.treatment import TreatmentCreate, TreatmentUpdate
from app.modules.treatment.services.treatment import TreatmentService

@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    return db

@pytest.fixture
def service(mock_db):
    return TreatmentService(mock_db)

# ------------------------------------------------------------------
# Test create_treatment
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_treatment_success(service, mock_db):
    # Mock patient, doctor, nurse, ehr existence
    mock_patient = MagicMock(id=1)
    mock_doctor = MagicMock(id=1)
    mock_nurse = MagicMock(id=1)
    mock_ehr = MagicMock(id=1)
    mock_db.get.side_effect = [mock_patient, mock_doctor, mock_nurse, mock_ehr]

    data = TreatmentCreate(
        patient_id=1,
        doctor_id=1,
        nurse_id=1,
        ehr_id=1,
        treatment_type="surgery",
        procedure_name="Appendectomy",
        performed_date=datetime.now(),
        notes="Routine"
    )
    result = await service.create_treatment(data)
    assert result.patient_id == 1
    assert result.doctor_id == 1
    assert result.treatment_type == "surgery"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_treatment_patient_not_found(service, mock_db):
    mock_db.get.side_effect = [None, MagicMock(), MagicMock(), MagicMock()]
    data = TreatmentCreate(patient_id=999, doctor_id=1)
    with pytest.raises(PatientNotFoundError):
        await service.create_treatment(data)

@pytest.mark.asyncio
async def test_create_treatment_doctor_not_found(service, mock_db):
    mock_db.get.side_effect = [MagicMock(), None, MagicMock(), MagicMock()]
    data = TreatmentCreate(patient_id=1, doctor_id=999)
    with pytest.raises(DoctorNotFoundError):
        await service.create_treatment(data)

@pytest.mark.asyncio
async def test_create_treatment_nurse_not_found(service, mock_db):
    mock_db.get.side_effect = [MagicMock(), MagicMock(), None, MagicMock()]
    data = TreatmentCreate(patient_id=1, doctor_id=1, nurse_id=999)
    with pytest.raises(NurseNotFoundError):
        await service.create_treatment(data)

# ------------------------------------------------------------------
# Test get_treatment and get_treatments
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_treatment_found(service, mock_db):
    expected = Treatment(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_treatment(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_treatment_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_treatment(999)
    assert result is None

# ------------------------------------------------------------------
# Test update_treatment
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_treatment_success(service, mock_db):
    existing = Treatment(id=1, notes="old")
    mock_db.get.return_value = existing
    update_data = TreatmentUpdate(notes="new")
    result = await service.update_treatment(1, update_data)
    assert result.notes == "new"
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_treatment_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(TreatmentNotFoundError):
        await service.update_treatment(999, TreatmentUpdate())

# ------------------------------------------------------------------
# Test delete_treatment
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_treatment_success(service, mock_db):
    existing = Treatment(id=1, billing_item=None)
    mock_db.get.return_value = existing
    result = await service.delete_treatment(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)

@pytest.mark.asyncio
async def test_delete_treatment_with_billing_item(service, mock_db):
    existing = Treatment(id=1, billing_item=MagicMock())
    mock_db.get.return_value = existing
    with pytest.raises(ValueError, match="associated billing item"):
        await service.delete_treatment(1)
    mock_db.delete.assert_not_called()