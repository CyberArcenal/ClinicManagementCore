import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.room import RoomNotFoundError
from app.modules.room.models.room import Room
from app.modules.room.schemas.base import RoomCreate, RoomUpdate
from app.modules.room.services.room import RoomService

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
    return RoomService(mock_db)

# ------------------------------------------------------------------
# Test create_room
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_room_success(service, mock_db):
    # Mock get_room_by_number returns None (no existing)
    with patch.object(service, 'get_room_by_number', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        data = RoomCreate(
            room_number="101",
            room_type="consultation",
            capacity=2,
            is_available=True,
            notes="Corner room"
        )
        result = await service.create_room(data)
        assert result.room_number == "101"
        assert result.room_type == "consultation"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_room_duplicate_number(service, mock_db):
    with patch.object(service, 'get_room_by_number', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = Room(id=1)
        data = RoomCreate(room_number="101")
        with pytest.raises(ValueError, match="already exists"):
            await service.create_room(data)

# ------------------------------------------------------------------
# Test get_room and get_rooms
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_room_found(service, mock_db):
    expected = Room(id=1, room_number="101")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_room(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_room_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_room(999)
    assert result is None

@pytest.mark.asyncio
async def test_get_room_by_number(service, mock_db):
    expected = Room(room_number="101")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_room_by_number("101")
    assert result == expected

@pytest.mark.asyncio
async def test_get_rooms_with_filters(service, mock_db):
    rooms = [Room(room_number="101"), Room(room_number="102")]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = rooms
    mock_db.execute.return_value = mock_result
    filters = {"room_type": "consultation"}
    result = await service.get_rooms(filters=filters)
    assert len(result) == 2

# ------------------------------------------------------------------
# Test update_room
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_room_success(service, mock_db):
    existing = Room(id=1, room_number="101", is_available=True)
    mock_db.get.return_value = existing
    # Mock get_room_by_number for uniqueness check if number changed (not changed here)
    with patch.object(service, 'get_room_by_number', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        update_data = RoomUpdate(is_available=False, notes="Under maintenance")
        result = await service.update_room(1, update_data)
        assert result.is_available is False
        assert result.notes == "Under maintenance"
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_room_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(RoomNotFoundError):
        await service.update_room(999, RoomUpdate())

@pytest.mark.asyncio
async def test_update_room_duplicate_number(service, mock_db):
    existing = Room(id=1, room_number="101")
    mock_db.get.return_value = existing
    # Another room with target number
    other = Room(id=2, room_number="102")
    with patch.object(service, 'get_room_by_number', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = other
        update_data = RoomUpdate(room_number="102")
        with pytest.raises(ValueError, match="already exists"):
            await service.update_room(1, update_data)

# ------------------------------------------------------------------
# Test delete_room
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_room_success(service, mock_db):
    existing = Room(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_room(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)

@pytest.mark.asyncio
async def test_delete_room_not_found(service, mock_db):
    mock_db.get.return_value = None
    result = await service.delete_room(999)
    assert result is False

# ------------------------------------------------------------------
# Test set_availability
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_set_availability_success(service, mock_db):
    existing = Room(id=1, is_available=False)
    mock_db.get.return_value = existing
    result = await service.set_availability(1, True)
    assert result.is_available is True
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_set_availability_room_not_found(service, mock_db):
    mock_db.get.return_value = None
    result = await service.set_availability(999, True)
    assert result is None

# ------------------------------------------------------------------
# Test get_available_rooms
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_available_rooms(service, mock_db):
    rooms = [Room(id=1, is_available=True), Room(id=2, is_available=True)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = rooms
    mock_db.execute.return_value = mock_result
    result = await service.get_available_rooms(room_type="consultation", min_capacity=2)
    assert len(result) == 2