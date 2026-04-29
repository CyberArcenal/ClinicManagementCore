import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import PatientNotFoundError
from app.modules.billing.enums.base import InvoiceStatus
from app.modules.billing.models.base import Invoice
from app.modules.billing.schemas.base import InvoiceCreate
from app.modules.billing.services.invoice import InvoiceService

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
    return InvoiceService(mock_db)

@pytest.mark.asyncio
async def test_create_invoice_success(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_db.get.return_value = mock_patient
    # Mock generate_invoice_number to return fixed string
    with patch.object(service, '_generate_invoice_number', return_value='INV-20240001'):
        data = InvoiceCreate(
            patient_id=1,
            invoice_number='',
            issue_date=datetime.now(),
            subtotal=Decimal('100.00'),
            tax=Decimal('10.00'),
            total=Decimal('110.00'),
            status=InvoiceStatus.DRAFT
        )
        result = await service.create_invoice(data)
        assert result.invoice_number == 'INV-20240001'
        assert result.total == Decimal('110.00')
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_invoice_patient_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = InvoiceCreate(patient_id=999, subtotal=0, tax=0, total=0)
    with pytest.raises(PatientNotFoundError):
        await service.create_invoice(data)

@pytest.mark.asyncio
async def test_get_invoice_by_number(service, mock_db):
    expected = Invoice(id=1, invoice_number='INV-001')
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_invoice_by_number('INV-001')
    assert result == expected