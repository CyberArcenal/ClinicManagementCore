import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.user import UserNotFoundError
from app.modules.staff.models.receptionist_profile import ReceptionistProfile
from app.modules.staff.services.receptionist_profile import ReceptionistProfileService
from app.modules.user.schemas.base import ReceptionistProfileCreate, ReceptionistProfileUpdate

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
    return ReceptionistProfileService(mock_db)

@pytest.mark.asyncio
async def test_create_receptionist_success(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_db.get.return_value = mock_user
    data = ReceptionistProfileCreate(user_id=1)
    result = await service.create_receptionist(data)
    assert result.user_id == 1
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_receptionist_user_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = ReceptionistProfileCreate(user_id=999)
    with pytest.raises(UserNotFoundError):
        await service.create_receptionist(data)

@pytest.mark.asyncio
async def test_get_receptionist_found(service, mock_db):
    expected = ReceptionistProfile(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_receptionist(1)
    assert result == expected

@pytest.mark.asyncio
async def test_update_receptionist_success(service, mock_db):
    existing = ReceptionistProfile(id=1)
    mock_db.get.return_value = existing
    result = await service.update_receptionist(1, ReceptionistProfileUpdate())
    assert result is not None
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_receptionist_success(service, mock_db):
    existing = ReceptionistProfile(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_receptionist(1)
    assert result is True