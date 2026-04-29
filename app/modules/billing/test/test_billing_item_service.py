import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.billing import InvoiceNotFoundError
from app.modules.billing.models.base import BillingItem, Invoice
from app.modules.billing.schemas.base import BillingItemCreate, BillingItemUpdate
from app.modules.billing.services.billing import BillingItemService


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
    return BillingItemService(mock_db)

@pytest.mark.asyncio
async def test_create_item_success(service, mock_db):
    mock_invoice = MagicMock(spec=Invoice, status='draft')
    mock_db.get.return_value = mock_invoice
    data = BillingItemCreate(
        invoice_id=1,
        description='Consultation',
        quantity=1,
        unit_price=Decimal('50.00'),
        total=Decimal('50.00')
    )
    with patch.object(service, '_recalculate_invoice_totals', new_callable=AsyncMock):
        result = await service.create_item(data)
        assert result.description == 'Consultation'
        assert result.total == Decimal('50.00')
        mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_create_item_invoice_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = BillingItemCreate(invoice_id=999, description='x', quantity=1, unit_price=10, total=10)
    with pytest.raises(InvoiceNotFoundError):
        await service.create_item(data)

@pytest.mark.asyncio
async def test_update_item_recalculates_total(service, mock_db):
    item = BillingItem(id=1, invoice_id=1, quantity=1, unit_price=Decimal('10.00'), total=Decimal('10.00'))
    mock_db.get.return_value = item
    # Mock invoice fetch for status check
    mock_invoice = MagicMock(spec=Invoice, status='draft')
    mock_db.get.side_effect = [item, mock_invoice]
    update_data = BillingItemUpdate(quantity=2)
    with patch.object(service, '_recalculate_invoice_totals', new_callable=AsyncMock):
        result = await service.update_item(1, update_data)
        assert result.quantity == 2
        assert result.total == Decimal('20.00')