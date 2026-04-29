import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.user import InvalidCredentialsError, UserAlreadyExistsError
from app.modules.user.enums.base import UserRole
from app.modules.user.models.base import User
from app.modules.user.schemas.base import UserCreate, UserUpdate
from app.modules.user.services.user import UserService



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
    return UserService(mock_db)

# ------------------------------------------------------------------
# Test create_user
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_user_success(service, mock_db):
    with patch.object(service, 'get_user_by_email', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="secure123",
            role=UserRole.PATIENT,
            is_active=True,
            phone_number="1234567890"
        )
        result = await service.create_user(data)
        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        assert result.role == UserRole.PATIENT
        assert service.verify_password("secure123", result.hashed_password) is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_user_duplicate_email(service, mock_db):
    with patch.object(service, 'get_user_by_email', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = User(email="exists@example.com")
        data = UserCreate(email="exists@example.com", full_name="Dup", password="x")
        with pytest.raises(UserAlreadyExistsError):
            await service.create_user(data)

# ------------------------------------------------------------------
# Test authenticate
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_authenticate_success(service, mock_db):
    user = User(id=1, email="a@b.com", hashed_password=service.hash_password("secret"), is_active=True)
    with patch.object(service, 'get_user_by_email', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = user
        result = await service.authenticate("a@b.com", "secret")
        assert result == user

@pytest.mark.asyncio
async def test_authenticate_wrong_password(service, mock_db):
    user = User(id=1, email="a@b.com", hashed_password=service.hash_password("secret"), is_active=True)
    with patch.object(service, 'get_user_by_email', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = user
        result = await service.authenticate("a@b.com", "wrong")
        assert result is None

@pytest.mark.asyncio
async def test_authenticate_inactive_user(service, mock_db):
    user = User(id=1, email="a@b.com", hashed_password=service.hash_password("secret"), is_active=False)
    with patch.object(service, 'get_user_by_email', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = user
        result = await service.authenticate("a@b.com", "secret")
        assert result is None

# ------------------------------------------------------------------
# Test JWT token creation (static method, no DB)
# ------------------------------------------------------------------
def test_create_access_token(service):
    token = service.create_access_token(data={"sub": "1", "role": "admin"})
    assert token is not None
    # Optionally decode and verify – but that's an integration test.

# ------------------------------------------------------------------
# Test get_user and get_users
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_user_found(service, mock_db):
    expected = User(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_user(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_user_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_user(999)
    assert result is None

@pytest.mark.asyncio
async def test_get_user_by_email(service, mock_db):
    expected = User(email="test@ex.com")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_user_by_email("test@ex.com")
    assert result == expected

# ------------------------------------------------------------------
# Test update_user
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_user_success(service, mock_db):
    existing = User(id=1, full_name="Old Name", email="old@ex.com")
    mock_db.get.return_value = existing
    with patch.object(service, 'get_user_by_email', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None  # email not taken
        update_data = UserUpdate(full_name="New Name", phone_number="999")
        result = await service.update_user(1, update_data)
        assert result.full_name == "New Name"
        assert result.phone_number == "999"
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_user_password(service, mock_db):
    existing = User(id=1, hashed_password=service.hash_password("old"))
    mock_db.get.return_value = existing
    update_data = UserUpdate(password="newpassword")
    result = await service.update_user(1, update_data)
    assert service.verify_password("newpassword", result.hashed_password) is True

# ------------------------------------------------------------------
# Test change_password
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_change_password_success(service, mock_db):
    user = User(id=1, hashed_password=service.hash_password("old"))
    mock_db.get.return_value = user
    result = await service.change_password(1, "old", "new")
    assert result is True
    assert service.verify_password("new", user.hashed_password) is True

@pytest.mark.asyncio
async def test_change_password_wrong_old(service, mock_db):
    user = User(id=1, hashed_password=service.hash_password("old"))
    mock_db.get.return_value = user
    with pytest.raises(InvalidCredentialsError):
        await service.change_password(1, "wrong", "new")

# ------------------------------------------------------------------
# Test reset_password
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reset_password_success(service, mock_db):
    user = User(id=1, email="reset@ex.com", hashed_password=service.hash_password("old"))
    with patch.object(service, 'get_user_by_email', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = user
        result = await service.reset_password("reset@ex.com", "newreset")
        assert result is True
        assert service.verify_password("newreset", user.hashed_password) is True