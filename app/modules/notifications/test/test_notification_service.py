import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.user import UserNotFoundError
from app.modules.notifications.models.inapp_notification import Notification
from app.modules.notifications.schemas.base import NotificationCreate
from app.modules.notifications.services.inapp_notification_service import InAppNotificationService


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
    return InAppNotificationService(mock_db)

# ------------------------------------------------------------------
# Test create_notification
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_notification_success(service, mock_db):
    mock_user = MagicMock(id=1)
    mock_actor = MagicMock(id=2)
    mock_db.get.side_effect = [mock_user, mock_actor]
    data = NotificationCreate(
        user_id=1,
        actor_id=2,
        notification_type="appointment_reminder",
        message="You have an appointment tomorrow"
    )
    result = await service.create_notification(data)
    assert result.user_id == 1
    assert result.message == "You have an appointment tomorrow"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_notification_user_not_found(service, mock_db):
    mock_db.get.side_effect = [None, MagicMock(id=2)]
    data = NotificationCreate(user_id=999, actor_id=2, notification_type="x", message="x")
    with pytest.raises(UserNotFoundError):
        await service.create_notification(data)

# ------------------------------------------------------------------
# Test get_user_notifications and mark read
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_user_notifications_unread(service, mock_db):
    mock_records = [Notification(id=1, is_read=False), Notification(id=2, is_read=False)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_records
    mock_db.execute.return_value = mock_result
    result = await service.get_user_notifications(1, unread_only=True)
    assert len(result) == 2

@pytest.mark.asyncio
async def test_mark_as_read_success(service, mock_db):
    existing = Notification(id=1, is_read=False)
    mock_db.get.return_value = existing
    result = await service.mark_as_read(1)
    assert result is True
    assert existing.is_read is True
    mock_db.commit.assert_awaited_once()