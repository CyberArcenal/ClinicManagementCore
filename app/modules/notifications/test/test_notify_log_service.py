import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.enums.base import NotifyStatus
from app.modules.notifications.models.notify_log import NotifyLog
from app.modules.notifications.schemas.base import NotifyLogCreate
from app.modules.notifications.services.notify_log_service import NotifyLogService


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
    return NotifyLogService(mock_db)

# ------------------------------------------------------------------
# Test create_log
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_log_success(service, mock_db):
    data = NotifyLogCreate(
        recipient_email="patient@example.com",
        subject="Appointment Reminder",
        payload="Your appointment at 10am",
        type="reminder",
        status=NotifyStatus.QUEUED.value,
        channel="email"
    )
    result = await service.create_log(data)
    assert result.recipient_email == "patient@example.com"
    assert result.status == NotifyStatus.QUEUED.value
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

# ------------------------------------------------------------------
# Test retry_failed_log
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retry_failed_log_success(service, mock_db):
    existing = NotifyLog(id=1, status=NotifyStatus.FAILED.value, retry_count=0)
    mock_db.get.return_value = existing
    result = await service.retry_failed_log(1)
    assert result.status == NotifyStatus.QUEUED.value
    assert result.retry_count == 1
    mock_db.commit.assert_awaited_once()

# ------------------------------------------------------------------
# Test statistics and cleanup
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_statistics(service, mock_db):
    logs = [
        NotifyLog(status=NotifyStatus.SENT.value, channel="email"),
        NotifyLog(status=NotifyStatus.SENT.value, channel="email"),
        NotifyLog(status=NotifyStatus.FAILED.value, channel="sms")
    ]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = logs
    mock_db.execute.return_value = mock_result
    stats = await service.get_statistics()
    assert stats["total"] == 3
    assert stats["by_status"][NotifyStatus.SENT.value] == 2
    assert stats["by_channel"]["sms"] == 1

@pytest.mark.asyncio
async def test_cleanup_old_logs(service, mock_db):
    old_logs = [NotifyLog(id=1), NotifyLog(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = old_logs
    mock_db.execute.return_value = mock_result
    count = await service.cleanup_old_logs(days=30)
    assert count == 2
    mock_db.delete.assert_called()