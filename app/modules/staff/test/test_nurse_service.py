import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.staff import DuplicateLicenseError, NurseNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.modules.staff.models.nurse_profile import NurseProfile
from app.modules.staff.services.nurse_profile import NurseProfileService
from app.modules.user.schemas.base import NurseProfileCreate, NurseProfileUpdate



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
    return NurseProfileService(mock_db)

# ------------------------------------------------------------------
# Test create_nurse
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_nurse_success(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_db.get.return_value = mock_user
    with patch.object(service, 'get_nurse_by_license', new_callable=AsyncMock) as mock_license:
        mock_license.return_value = None
        data = NurseProfileCreate(user_id=1, license_number="N123")
        result = await service.create_nurse(data)
        assert result.user_id == 1
        assert result.license_number == "N123"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_nurse_user_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = NurseProfileCreate(user_id=999, license_number="X")
    with pytest.raises(UserNotFoundError):
        await service.create_nurse(data)

@pytest.mark.asyncio
async def test_create_nurse_duplicate_license(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_db.get.return_value = mock_user
    with patch.object(service, 'get_nurse_by_license', new_callable=AsyncMock) as mock_license:
        mock_license.return_value = NurseProfile(id=1)
        data = NurseProfileCreate(user_id=1, license_number="DUPLICATE")
        with pytest.raises(DuplicateLicenseError):
            await service.create_nurse(data)

# ------------------------------------------------------------------
# Test get_nurse and get_nurses
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_nurse_found(service, mock_db):
    expected = NurseProfile(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_nurse(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_nurse_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_nurse(999)
    assert result is None

# ------------------------------------------------------------------
# Test update_nurse
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_nurse_success(service, mock_db):
    existing = NurseProfile(id=1, license_number="OLD")
    mock_db.get.return_value = existing
    with patch.object(service, 'get_nurse_by_license', new_callable=AsyncMock) as mock_license:
        mock_license.return_value = None
        update_data = NurseProfileUpdate(license_number="NEW")
        result = await service.update_nurse(1, update_data)
        assert result.license_number == "NEW"
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_nurse_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(NurseNotFoundError):
        await service.update_nurse(999, NurseProfileUpdate())

# ------------------------------------------------------------------
# Test delete_nurse
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_nurse_success(service, mock_db):
    existing = NurseProfile(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_nurse(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)