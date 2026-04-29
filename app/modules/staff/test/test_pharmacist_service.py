import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.staff.models.pharmacist_profile import PharmacistProfile
from app.modules.staff.services.pharmacist_profile import PharmacistProfileService
from app.modules.user.schemas.base import PharmacistProfileCreate


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
    return PharmacistProfileService(mock_db)

@pytest.mark.asyncio
async def test_create_pharmacist_success(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_db.get.return_value = mock_user
    data = PharmacistProfileCreate(user_id=1)
    result = await service.create_pharmacist(data)
    assert result.user_id == 1
    mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_get_pharmacist_found(service, mock_db):
    expected = PharmacistProfile(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_pharmacist(1)
    assert result == expected

@pytest.mark.asyncio
async def test_delete_pharmacist_success(service, mock_db):
    existing = PharmacistProfile(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_pharmacist(1)
    assert result is True