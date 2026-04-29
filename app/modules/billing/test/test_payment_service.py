import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions.billing import OverpaymentError
from app.modules.billing.enums.base import PaymentMethod
from app.modules.billing.models.base import Invoice
from app.modules.billing.schemas.base import PaymentCreate
from app.modules.billing.services.payment import PaymentService

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
    return PaymentService(mock_db)

@pytest.mark.asyncio
async def test_create_payment_success(service, mock_db):
    mock_invoice = MagicMock(spec=Invoice, total=Decimal('100.00'), status='sent')
    mock_db.get.return_value = mock_invoice
    # Mock total paid query
    mock_result = AsyncMock()
    mock_result.scalar.return_value = Decimal('0.00')
    mock_db.execute.return_value = mock_result
    data = PaymentCreate(
        invoice_id=1,
        amount=Decimal('50.00'),
        method=PaymentMethod.CASH,
        payment_date=datetime.now()
    )
    with patch.object(service.invoice_service, 'update_invoice_status_from_payments', new_callable=AsyncMock):
        result = await service.create_payment(data)
        assert result.amount == Decimal('50.00')
        mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_create_payment_overpayment(service, mock_db):
    mock_invoice = MagicMock(spec=Invoice, total=Decimal('100.00'), status='sent')
    mock_db.get.return_value = mock_invoice
    mock_result = AsyncMock()
    mock_result.scalar.return_value = Decimal('80.00')  # already paid
    mock_db.execute.return_value = mock_result
    data = PaymentCreate(invoice_id=1, amount=Decimal('30.00'), method=PaymentMethod.CASH)
    with pytest.raises(OverpaymentError):
        await service.create_payment(data)