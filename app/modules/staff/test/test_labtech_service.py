import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.staff.labtech_profile_service import LabTechProfileService
from app.modules.staff.schemas import LabTechProfileCreate, LabTechProfileUpdate
from app.modules.staff.models import LabTechProfile
from app.common.exceptions import LabTechNotFoundError, UserNotFoundError

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
    return LabTechProfileService(mock_db)

@pytest.mark.asyncio
async def test_create_labtech_success(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_db.get.return_value = mock_user
    data = LabTechProfileCreate(user_id=1)
    result = await service.create_lab_tech(data)
    assert result.user_id == 1
    mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_get_labtech_found(service, mock_db):
    expected = LabTechProfile(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_lab_tech(1)
    assert result == expected

@pytest.mark.asyncio
async def test_delete_labtech_success(service, mock_db):
    existing = LabTechProfile(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_lab_tech(1)
    assert result is True