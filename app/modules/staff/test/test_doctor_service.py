import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import DoctorNotFoundError
from app.common.exceptions.staff import DuplicateLicenseError
from app.common.exceptions.user import UserNotFoundError
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.services.doctor_profile import DoctorProfileService
from app.modules.user.schemas.base import DoctorProfileCreate, DoctorProfileUpdate

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
    return DoctorProfileService(mock_db)

# ------------------------------------------------------------------
# Test create_doctor
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_doctor_success(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_db.get.return_value = mock_user
    # Mock get_doctor_by_license returns None
    with patch.object(service, 'get_doctor_by_license', new_callable=AsyncMock) as mock_license:
        mock_license.return_value = None
        data = DoctorProfileCreate(
            user_id=1,
            specialization="Cardiology",
            license_number="LIC123",
            years_of_experience=10
        )
        result = await service.create_doctor(data)
        assert result.user_id == 1
        assert result.license_number == "LIC123"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_doctor_user_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = DoctorProfileCreate(user_id=999, license_number="X")
    with pytest.raises(UserNotFoundError):
        await service.create_doctor(data)

@pytest.mark.asyncio
async def test_create_doctor_duplicate_license(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_db.get.return_value = mock_user
    with patch.object(service, 'get_doctor_by_license', new_callable=AsyncMock) as mock_license:
        mock_license.return_value = DoctorProfile(id=1)
        data = DoctorProfileCreate(user_id=1, license_number="DUPLICATE")
        with pytest.raises(DuplicateLicenseError):
            await service.create_doctor(data)

# ------------------------------------------------------------------
# Test get_doctor and get_doctors
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_doctor_found(service, mock_db):
    expected = DoctorProfile(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_doctor(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_doctor_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_doctor(999)
    assert result is None

# ------------------------------------------------------------------
# Test update_doctor
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_doctor_success(service, mock_db):
    existing = DoctorProfile(id=1, specialization="Old", years_of_experience=5)
    mock_db.get.return_value = existing
    # No license change
    update_data = DoctorProfileUpdate(specialization="New Specialization", years_of_experience=12)
    result = await service.update_doctor(1, update_data)
    assert result.specialization == "New Specialization"
    assert result.years_of_experience == 12
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_doctor_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(DoctorNotFoundError):
        await service.update_doctor(999, DoctorProfileUpdate())

# ------------------------------------------------------------------
# Test delete_doctor
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_doctor_success(service, mock_db):
    existing = DoctorProfile(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_doctor(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)