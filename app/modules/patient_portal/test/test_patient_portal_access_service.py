import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import PatientNotFoundError
from app.modules.patient_portal.models.models import PatientPortalAccess
from app.modules.patient_portal.schemas.base import PatientPortalAccessCreate
from app.modules.patient_portal.services.base import PatientPortalAccessService



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
    return PatientPortalAccessService(mock_db)

# ------------------------------------------------------------------
# Test create_access_record
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_record_success(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_db.get.return_value = mock_patient
    data = PatientPortalAccessCreate(
        patient_id=1,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        login_time=datetime.now()
    )
    result = await service.create_access_record(data)
    assert result.patient_id == 1
    assert result.ip_address == "192.168.1.1"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_record_patient_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = PatientPortalAccessCreate(patient_id=999)
    with pytest.raises(PatientNotFoundError):
        await service.create_access_record(data)

# ------------------------------------------------------------------
# Test record_login and record_logout
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_record_login(service, mock_db):
    # Ensure logout_active_session is called, then create new
    with patch.object(service, 'logout_active_session', new_callable=AsyncMock) as mock_logout:
        mock_logout.return_value = True
        result = await service.record_login(1, "192.168.1.1", "Chrome")
        assert result.patient_id == 1
        assert result.login_time is not None
        assert result.logout_time is None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_record_logout_success(service, mock_db):
    active = PatientPortalAccess(id=1, patient_id=1, logout_time=None)
    with patch.object(service, 'get_active_session', new_callable=AsyncMock) as mock_active:
        mock_active.return_value = active
        result = await service.record_logout(1)
        assert result is True
        assert active.logout_time is not None
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_record_logout_no_active_session(service, mock_db):
    with patch.object(service, 'get_active_session', new_callable=AsyncMock) as mock_active:
        mock_active.return_value = None
        result = await service.record_logout(1)
        assert result is False

# ------------------------------------------------------------------
# Test get_active_session and is_session_active
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_active_session_found(service, mock_db):
    expected = PatientPortalAccess(id=1, logout_time=None)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_active_session(1)
    assert result == expected

@pytest.mark.asyncio
async def test_is_session_active_within_timeout(service, mock_db):
    active = PatientPortalAccess(id=1, login_time=datetime.now() - timedelta(minutes=10))
    with patch.object(service, 'get_active_session', new_callable=AsyncMock) as mock_active:
        mock_active.return_value = active
        result = await service.is_session_active(1, session_timeout_minutes=30)
        assert result is True

@pytest.mark.asyncio
async def test_is_session_active_expired(service, mock_db):
    active = PatientPortalAccess(id=1, login_time=datetime.now() - timedelta(minutes=40))
    with patch.object(service, 'get_active_session', new_callable=AsyncMock) as mock_active:
        mock_active.return_value = active
        with patch.object(service, 'logout_active_session', new_callable=AsyncMock) as mock_logout:
            mock_logout.return_value = True
            result = await service.is_session_active(1, session_timeout_minutes=30)
            assert result is False
            mock_logout.assert_awaited_once()

# ------------------------------------------------------------------
# Test get_patient_access_history
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_patient_access_history(service, mock_db):
    records = [PatientPortalAccess(id=1), PatientPortalAccess(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = records
    mock_db.execute.return_value = mock_result
    result = await service.get_patient_access_history(1, limit=50)
    assert len(result) == 2