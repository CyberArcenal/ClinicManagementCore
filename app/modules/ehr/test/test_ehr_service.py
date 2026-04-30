import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.modules.ehr.models.ehr import EHR
from app.modules.ehr.schemas.base import EHRCreate, EHRUpdate
from app.modules.ehr.services.base import EHRService



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
    return EHRService(mock_db)

# ------------------------------------------------------------------
# Test create_ehr
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_ehr_success(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_doctor = MagicMock(id=1)
    mock_db.get.side_effect = [mock_patient, mock_doctor]
    
    data = EHRCreate(
        patient_id=1,
        doctor_id=1,
        visit_date=datetime.now(),
        diagnosis="Flu",
        treatment_plan="Rest and fluids",
        clinical_notes="Patient has fever"
    )
    result = await service.create_ehr(data)
    assert result.patient_id == 1
    assert result.doctor_id == 1
    assert result.diagnosis == "Flu"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_ehr_patient_not_found(service, mock_db):
    mock_db.get.side_effect = [None, MagicMock(id=1)]  # patient None, doctor OK
    data = EHRCreate(patient_id=999, doctor_id=1, visit_date=datetime.now())
    with pytest.raises(PatientNotFoundError):
        await service.create_ehr(data)

@pytest.mark.asyncio
async def test_create_ehr_doctor_not_found(service, mock_db):
    mock_db.get.side_effect = [MagicMock(id=1), None]  # patient OK, doctor None
    data = EHRCreate(patient_id=1, doctor_id=999, visit_date=datetime.now())
    with pytest.raises(DoctorNotFoundError):
        await service.create_ehr(data)

# ------------------------------------------------------------------
# Test get_ehr and get_ehr_records
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_ehr_found(service, mock_db):
    expected = EHR(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_ehr(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_ehr_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_ehr(999)
    assert result is None

# ------------------------------------------------------------------
# Test update_ehr
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_ehr_success(service, mock_db):
    existing = EHR(id=1, patient_id=1, doctor_id=1, diagnosis="Cold")
    mock_db.get.return_value = existing
    # For doctor validation, if doctor_id changes, we need to fetch new doctor
    # But in this test we don't change doctor_id
    update_data = EHRUpdate(diagnosis="Flu", treatment_plan="Antibiotics")
    result = await service.update_ehr(1, update_data)
    assert result.diagnosis == "Flu"
    assert result.treatment_plan == "Antibiotics"
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_ehr_not_found(service, mock_db):
    mock_db.get.return_value = None
    update_data = EHRUpdate(diagnosis="Flu")
    with pytest.raises(EHRNotFoundError):
        await service.update_ehr(999, update_data)

# ------------------------------------------------------------------
# Test delete_ehr
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_ehr_success(service, mock_db):
    existing = EHR(id=1, patient_id=1)
    # Mock that there are no dependent records (prescriptions, lab_requests, treatments)
    existing.prescriptions = []
    existing.lab_requests = []
    existing.treatments = []
    mock_db.get.return_value = existing
    result = await service.delete_ehr(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)

@pytest.mark.asyncio
async def test_delete_ehr_with_dependents(service, mock_db):
    existing = EHR(id=1, patient_id=1)
    # Simulate dependent records
    existing.prescriptions = [MagicMock()]
    mock_db.get.return_value = existing
    with pytest.raises(ValueError, match="Cannot delete EHR record with associated prescriptions"):
        await service.delete_ehr(1)
    mock_db.delete.assert_not_called()

# ------------------------------------------------------------------
# Test patient history
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_patient_ehr_history(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_db.get.return_value = mock_patient
    mock_records = [EHR(id=1), EHR(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_records
    mock_db.execute.return_value = mock_result
    result = await service.get_patient_ehr_history(1, limit=20)
    assert len(result) == 2