import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import DoctorNotFoundError, PatientNotFoundError
from app.common.exceptions.ehr import EHRNotFoundError
from app.common.exceptions.prescription import PrescriptionNotFoundError
from app.modules.prescription.models.models import Prescription, PrescriptionItem
from app.modules.prescription.schemas.base import PrescriptionCreate, PrescriptionItemCreate, PrescriptionItemUpdate, PrescriptionUpdate
from app.modules.prescription.services.prescription import PrescriptionService
from app.modules.prescription.services.prescription_item import PrescriptionItemService

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
    return PrescriptionService(mock_db)


# ------------------------------------------------------------------
# Test create_prescription
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_prescription_success(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_doctor = MagicMock(id=1)
    mock_db.get.side_effect = [mock_patient, mock_doctor]  # get patient, then doctor
    data = PrescriptionCreate(
        patient_id=1,
        doctor_id=1,
        issue_date=date.today(),
        notes="Take with food",
        items=[
            PrescriptionItemCreate(
                drug_name="Paracetamol",
                dosage="500mg",
                frequency="3x/day",
                duration_days=5,
            ),
            PrescriptionItemCreate(
                drug_name="Amoxicillin",
                dosage="250mg",
                frequency="2x/day",
                duration_days=7,
            ),
        ],
    )
    # Mock item_service.create_item for both items
    mock_db.add = AsyncMock()
    with patch.object(
        service.item_service, "create_item", new_callable=AsyncMock
    ) as mock_create_item:
        result = await service.create_prescription(data)
        assert result.patient_id == 1
        assert result.doctor_id == 1
        assert result.is_dispensed is False
        assert mock_create_item.call_count == 2
        mock_db.add.assert_called_once_with(result)
        mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_prescription_patient_not_found(service, mock_db):
    mock_db.get.side_effect = [None, MagicMock(id=1)]
    data = PrescriptionCreate(patient_id=999, doctor_id=1)
    with pytest.raises(PatientNotFoundError):
        await service.create_prescription(data)


@pytest.mark.asyncio
async def test_create_prescription_doctor_not_found(service, mock_db):
    mock_db.get.side_effect = [MagicMock(id=1), None]
    data = PrescriptionCreate(patient_id=1, doctor_id=999)
    with pytest.raises(DoctorNotFoundError):
        await service.create_prescription(data)


@pytest.mark.asyncio
async def test_create_prescription_ehr_not_found(service, mock_db):
    mock_db.get.side_effect = [MagicMock(id=1), MagicMock(id=1), None]
    data = PrescriptionCreate(patient_id=1, doctor_id=1, ehr_id=999, items=[])
    with pytest.raises(EHRNotFoundError):
        await service.create_prescription(data)


# ------------------------------------------------------------------
# Test get_prescription and get_prescriptions
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_prescription_found(service, mock_db):
    expected = Prescription(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_prescription(1)
    assert result == expected


@pytest.mark.asyncio
async def test_get_prescription_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_prescription(999)
    assert result is None


# ------------------------------------------------------------------
# Test update_prescription and mark dispensed
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_prescription_success(service, mock_db):
    existing = Prescription(id=1, notes="Old notes")
    mock_db.get.return_value = existing
    update_data = PrescriptionUpdate(notes="New notes")
    result = await service.update_prescription(1, update_data)
    assert result.notes == "New notes"
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_prescription_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(PrescriptionNotFoundError):
        await service.update_prescription(999, PrescriptionUpdate())


@pytest.mark.asyncio
async def test_mark_as_dispensed_success(service, mock_db):
    existing = Prescription(id=1, is_dispensed=False)
    mock_db.get.return_value = existing
    result = await service.mark_as_dispensed(1)
    assert result.is_dispensed is True
    mock_db.commit.assert_awaited_once()


# ------------------------------------------------------------------
# Test delete_prescription
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_prescription_success(service, mock_db):
    existing = Prescription(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_prescription(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)


# ------------------------------------------------------------------
# Test get_patient_prescriptions
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_patient_prescriptions(service, mock_db):
    prescriptions = [Prescription(id=1), Prescription(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = prescriptions
    mock_db.execute.return_value = mock_result
    result = await service.get_patient_prescriptions(1, include_dispensed=True)
    assert len(result) == 2
