import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.inventory import InventoryItemNotFoundError
from app.modules.inventory.models.models import InventoryTransaction
from app.modules.inventory.schemas.base import InventoryTransactionCreate, InventoryTransactionUpdate
from app.modules.inventory.services.inventory_transaction import InventoryTransactionService


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
    return InventoryTransactionService(mock_db)

# ------------------------------------------------------------------
# Test create_transaction
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_transaction_success(service, mock_db):
    # Mock item exists via InventoryItemService.get_item
    with patch('app.modules.inventory.inventory_item_service.InventoryItemService.get_item', new_callable=AsyncMock) as mock_get_item:
        mock_get_item.return_value = MagicMock(id=1)
        data = InventoryTransactionCreate(
            item_id=1,
            transaction_type="purchase",
            quantity=100,
            reference_document="PO-123",
            performed_by_id=1
        )
        result = await service.create_transaction(data)
        assert result.transaction_type == "purchase"
        assert result.quantity == 100
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_transaction_item_not_found(service, mock_db):
    with patch('app.modules.inventory.inventory_item_service.InventoryItemService.get_item', new_callable=AsyncMock) as mock_get_item:
        mock_get_item.return_value = None
        data = InventoryTransactionCreate(item_id=999, transaction_type="sale", quantity=1)
        with pytest.raises(InventoryItemNotFoundError):
            await service.create_transaction(data)

# ------------------------------------------------------------------
# Test get_transaction and get_transactions
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_transaction_found(service, mock_db):
    expected = InventoryTransaction(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_transaction(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_transaction_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_transaction(999)
    assert result is None

# ------------------------------------------------------------------
# Test update_transaction
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_transaction_success(service, mock_db):
    existing = InventoryTransaction(id=1, transaction_type="purchase", quantity=100)
    mock_db.get.return_value = existing
    update_data = InventoryTransactionUpdate(reference_document="NEW-PO")
    result = await service.update_transaction(1, update_data)
    assert result.reference_document == "NEW-PO"
    mock_db.commit.assert_awaited_once()