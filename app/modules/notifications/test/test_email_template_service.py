import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.notification import TemplateNotFoundError
from app.modules.notifications.models.email_template import EmailTemplate
from app.modules.notifications.schemas.base import EmailTemplateCreate, EmailTemplateUpdate
from app.modules.notifications.services.email_template_service import EmailTemplateService

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
    return EmailTemplateService(mock_db)

# ------------------------------------------------------------------
# Test create_template and get
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_template_success(service, mock_db):
    data = EmailTemplateCreate(
        name="welcome_email",
        subject="Welcome to Clinic",
        content="Hello {{ name }}, thank you for registering."
    )
    result = await service.create_template(data)
    assert result.name == "welcome_email"
    assert "{{ name }}" in result.content
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_template_by_name(service, mock_db):
    expected = EmailTemplate(id=1, name="welcome")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_template_by_name("welcome")
    assert result == expected

# ------------------------------------------------------------------
# Test update and delete
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_template_success(service, mock_db):
    existing = EmailTemplate(id=1, name="old", subject="Old Subject", content="Old")
    mock_db.get.return_value = existing
    update_data = EmailTemplateUpdate(subject="New Subject")
    result = await service.update_template(1, update_data)
    assert result.subject == "New Subject"
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_template_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(TemplateNotFoundError):
        await service.update_template(999, EmailTemplateUpdate())

@pytest.mark.asyncio
async def test_delete_template_success(service, mock_db):
    existing = EmailTemplate(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_template(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)

# ------------------------------------------------------------------
# Test render
# ------------------------------------------------------------------
def test_render_template(service):
    template = EmailTemplate(
        name="test",
        subject="Hi {{ name }}",
        content="Hello {{ name }}, your appointment at {{ time }}."
    )
    context = {"name": "John", "time": "10:00"}
    subject, content = service.render_template(template, context)
    assert subject == "Hi John"
    assert content == "Hello John, your appointment at 10:00."