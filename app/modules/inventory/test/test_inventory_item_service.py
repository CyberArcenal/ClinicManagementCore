import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.inventory import InsufficientStockError, InventoryItemNotFoundError
from app.modules.inventory.models.inventory_item import InventoryItem
from app.modules.inventory.schemas.base import InventoryItemCreate, InventoryItemUpdate
from app.modules.inventory.services.inventory_item import InventoryItemService


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
    return InventoryItemService(mock_db)

# ------------------------------------------------------------------
# Test create_item
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_item_success(service, mock_db):
    # Mock SKU uniqueness check returns None
    service.get_item_by_sku = AsyncMock(return_value=None)
    data = InventoryItemCreate(
        name="Paracetamol",
        category="Medicine",
        sku="MED001",
        quantity_on_hand=100,
        unit="bottle",
        reorder_level=20,
        unit_cost=Decimal("5.00"),
        selling_price=Decimal("10.00")
    )
    result = await service.create_item(data)
    assert result.name == "Paracetamol"
    assert result.sku == "MED001"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_item_duplicate_sku(service, mock_db):
    service.get_item_by_sku = AsyncMock(return_value=MagicMock(id=1))
    data = InventoryItemCreate(name="Aspirin", sku="MED001")
    with pytest.raises(ValueError, match="already exists"):
        await service.create_item(data)

# ------------------------------------------------------------------
# Test get_item and get_items
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_item_found(service, mock_db):
    expected = InventoryItem(id=1, name="Item")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_item(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_item_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_item(999)
    assert result is None

# ------------------------------------------------------------------
# Test update_item
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_item_success(service, mock_db):
    existing = InventoryItem(id=1, name="Old", sku="OLD", quantity_on_hand=50)
    mock_db.get.return_value = existing
    update_data = InventoryItemUpdate(name="New Name", selling_price=Decimal("15.00"))
    result = await service.update_item(1, update_data)
    assert result.name == "New Name"
    assert result.selling_price == Decimal("15.00")
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_item_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(InventoryItemNotFoundError):
        await service.update_item(999, InventoryItemUpdate(name="X"))

# ------------------------------------------------------------------
# Test stock management
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_add_stock_success(service, mock_db):
    existing = InventoryItem(id=1, quantity_on_hand=50)
    mock_db.get.return_value = existing
    result = await service.add_stock(1, 20)
    assert result.quantity_on_hand == 70
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_stock_zero_quantity(service, mock_db):
    with pytest.raises(ValueError, match="positive"):
        await service.add_stock(1, 0)

@pytest.mark.asyncio
async def test_remove_stock_success(service, mock_db):
    existing = InventoryItem(id=1, quantity_on_hand=50)
    mock_db.get.return_value = existing
    result = await service.remove_stock(1, 20)
    assert result.quantity_on_hand == 30
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_remove_stock_insufficient(service, mock_db):
    existing = InventoryItem(id=1, quantity_on_hand=10)
    mock_db.get.return_value = existing
    with pytest.raises(InsufficientStockError):
        await service.remove_stock(1, 20)

@pytest.mark.asyncio
async def test_adjust_stock(service, mock_db):
    existing = InventoryItem(id=1, quantity_on_hand=50)
    mock_db.get.return_value = existing
    result = await service.adjust_stock(1, 30)
    assert result.quantity_on_hand == 30
    mock_db.commit.assert_awaited_once()

# ------------------------------------------------------------------
# Test low stock and expired
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_low_stock_items(service, mock_db):
    mock_items = [InventoryItem(id=1, quantity_on_hand=5, reorder_level=10)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_items
    mock_db.execute.return_value = mock_result
    result = await service.get_low_stock_items()
    assert len(result) == 1