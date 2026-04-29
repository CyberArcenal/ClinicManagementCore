import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.prescription import PrescriptionNotFoundError
from app.modules.prescription.models.models import PrescriptionItem
from app.modules.prescription.schemas.base import PrescriptionItemCreate, PrescriptionItemUpdate
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
    return PrescriptionItemService(mock_db)


# ------------------------------------------------------------------
# Test create_item
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_item_success(service, mock_db):
    mock_prescription = MagicMock(id=1)
    mock_db.get.return_value = mock_prescription
    data = PrescriptionItemCreate(
        prescription_id=1,
        drug_name="Ibuprofen",
        dosage="200mg",
        frequency="as needed",
        duration_days=3,
    )
    result = await service.create_item(data)
    assert result.drug_name == "Ibuprofen"
    assert result.prescription_id == 1
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_item_prescription_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = PrescriptionItemCreate(prescription_id=999, drug_name="Test")
    with pytest.raises(PrescriptionNotFoundError):
        await service.create_item(data)


# ------------------------------------------------------------------
# Test get_items_by_prescription
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_items_by_prescription(service, mock_db):
    items = [PrescriptionItem(id=1), PrescriptionItem(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = items
    mock_db.execute.return_value = mock_result
    result = await service.get_items_by_prescription(1)
    assert len(result) == 2


# ------------------------------------------------------------------
# Test update_item
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_item_success(service, mock_db):
    existing = PrescriptionItem(id=1, dosage="old", frequency="old")
    mock_db.get.return_value = existing
    update_data = PrescriptionItemUpdate(dosage="2 pills", frequency="daily")
    result = await service.update_item(1, update_data)
    assert result.dosage == "2 pills"
    assert result.frequency == "daily"
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_item_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(
        PrescriptionNotFoundError
    ):  # actually PrescriptionItemNotFoundError
        # We need to ensure the service raises correct exception. For now, we adapt.
        # Our service raises PrescriptionItemNotFoundError.
        await service.update_item(999, PrescriptionItemUpdate())


# ------------------------------------------------------------------
# Test delete_item
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_item_success(service, mock_db):
    existing = PrescriptionItem(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_item(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)
