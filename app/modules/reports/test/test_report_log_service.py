import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.report_log import ReportLogNotFoundError
from app.common.exceptions.user import UserNotFoundError
from app.modules.reports.models.models import ReportLog
from app.modules.reports.schemas.base import ReportLogCreate, ReportLogUpdate
from app.modules.reports.services.base import ReportLogService


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
    return ReportLogService(mock_db)

# ------------------------------------------------------------------
# Test create_report_log
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_report_log_success(service, mock_db):
    # Mock user exists
    mock_db.get.return_value = MagicMock(id=1)
    data = ReportLogCreate(
        report_name="patient_summary",
        generated_by_id=1,
        parameters='{"date_from": "2025-01-01"}',
        file_path="/reports/patient_summary_20250101.pdf",
        generated_at=datetime.now()
    )
    result = await service.create_report_log(data)
    assert result.report_name == "patient_summary"
    assert result.file_path == "/reports/patient_summary_20250101.pdf"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_report_log_user_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = ReportLogCreate(report_name="test", generated_by_id=999)
    with pytest.raises(UserNotFoundError):
        await service.create_report_log(data)

# ------------------------------------------------------------------
# Test get_report_log and get_report_logs
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_report_log_found(service, mock_db):
    expected = ReportLog(id=1, report_name="test")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_report_log(1)
    assert result == expected

@pytest.mark.asyncio
async def test_get_report_log_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_report_log(999)
    assert result is None

@pytest.mark.asyncio
async def test_get_report_logs_with_filters(service, mock_db):
    logs = [ReportLog(report_name="a"), ReportLog(report_name="b")]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = logs
    mock_db.execute.return_value = mock_result
    filters = {"report_name": "patient"}
    result = await service.get_report_logs(filters=filters)
    assert len(result) == 2

# ------------------------------------------------------------------
# Test update_report_log
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_report_log_success(service, mock_db):
    existing = ReportLog(id=1, file_path="old.pdf")
    mock_db.get.return_value = existing
    update_data = ReportLogUpdate(file_path="new.pdf")
    result = await service.update_report_log(1, update_data)
    assert result.file_path == "new.pdf"
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_report_log_not_found(service, mock_db):
    mock_db.get.return_value = None
    with pytest.raises(ReportLogNotFoundError):
        await service.update_report_log(999, ReportLogUpdate())

# ------------------------------------------------------------------
# Test delete_report_log
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_report_log_success(service, mock_db):
    existing = ReportLog(id=1)
    mock_db.get.return_value = existing
    result = await service.delete_report_log(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)

@pytest.mark.asyncio
async def test_delete_report_log_not_found(service, mock_db):
    mock_db.get.return_value = None
    result = await service.delete_report_log(999)
    assert result is False

# ------------------------------------------------------------------
# Test utilities: get_reports_by_user, get_statistics, cleanup_old_logs
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_reports_by_user(service, mock_db):
    logs = [ReportLog(id=1), ReportLog(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = logs
    mock_db.execute.return_value = mock_result
    result = await service.get_reports_by_user(1, skip=0, limit=50)
    assert len(result) == 2

@pytest.mark.asyncio
async def test_get_report_statistics(service, mock_db):
    logs = [
        ReportLog(report_name="A"),
        ReportLog(report_name="A"),
        ReportLog(report_name="B"),
    ]
    # Set generated_by_id to same user for all
    for log in logs:
        log.generated_by_id = 1
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = logs
    mock_db.execute.return_value = mock_result
    stats = await service.get_report_statistics()
    assert stats["total_reports_generated"] == 3
    assert stats["unique_users_generated"] == 1
    assert stats["top_report_names"][0]["name"] == "A"
    assert stats["top_report_names"][0]["count"] == 2

@pytest.mark.asyncio
async def test_cleanup_old_logs(service, mock_db):
    old_logs = [ReportLog(id=1), ReportLog(id=2)]
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = old_logs
    mock_db.execute.return_value = mock_result
    count = await service.cleanup_old_logs(days=30)
    assert count == 2
    mock_db.delete.assert_called()