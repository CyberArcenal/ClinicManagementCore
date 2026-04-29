import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.billing import InvoiceNotFoundError
from app.common.exceptions.insurance import ClaimAmountExceedsInvoiceError, InsuranceClaimNotFoundError, InsuranceCoverageExpiredError, InsuranceDetailNotFoundError
from app.modules.billing.models.base import Invoice
from app.modules.insurance.models.models import InsuranceClaim, InsuranceDetail
from app.modules.insurance.schemas.base import InsuranceClaimCreate, InsuranceClaimUpdate
from app.modules.insurance.services.insurance_claim import InsuranceClaimService


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
    return InsuranceClaimService(mock_db)

# ------------------------------------------------------------------
# Test create_claim
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_claim_success(service, mock_db):
    # Mock insurance detail (active)
    mock_detail = MagicMock(spec=InsuranceDetail, id=1)
    mock_detail.coverage_start = date(2025,1,1)
    mock_detail.coverage_end = date(2025,12,31)
    # Mock the detail_service call inside service
    with patch.object(service.detail_service, 'get_insurance_detail', return_value=mock_detail):
        with patch.object(service.detail_service, 'is_coverage_active', return_value=True):
            mock_invoice = MagicMock(spec=Invoice, id=1, total=Decimal('500.00'), status='sent')
            mock_db.get.return_value = mock_invoice
            # Mock claim number generation
            with patch.object(service, '_generate_claim_number', return_value='CLM-20250001'):
                data = InsuranceClaimCreate(
                    insurance_detail_id=1,
                    invoice_id=1,
                    approved_amount=Decimal('500.00')
                )
                result = await service.create_claim(data)
                assert result.claim_number == 'CLM-20250001'
                assert result.approved_amount == Decimal('500.00')
                mock_db.add.assert_called_once()
                mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_claim_insurance_detail_not_found(service, mock_db):
    with patch.object(service.detail_service, 'get_insurance_detail', return_value=None):
        data = InsuranceClaimCreate(insurance_detail_id=999, invoice_id=1)
        with pytest.raises(InsuranceDetailNotFoundError):
            await service.create_claim(data)

@pytest.mark.asyncio
async def test_create_claim_coverage_expired(service, mock_db):
    mock_detail = MagicMock(id=1)
    with patch.object(service.detail_service, 'get_insurance_detail', return_value=mock_detail):
        with patch.object(service.detail_service, 'is_coverage_active', return_value=False):
            data = InsuranceClaimCreate(insurance_detail_id=1, invoice_id=1)
            with pytest.raises(InsuranceCoverageExpiredError):
                await service.create_claim(data)

@pytest.mark.asyncio
async def test_create_claim_invoice_not_found(service, mock_db):
    mock_detail = MagicMock(id=1)
    with patch.object(service.detail_service, 'get_insurance_detail', return_value=mock_detail):
        with patch.object(service.detail_service, 'is_coverage_active', return_value=True):
            mock_db.get.return_value = None
            data = InsuranceClaimCreate(insurance_detail_id=1, invoice_id=999)
            with pytest.raises(InvoiceNotFoundError):
                await service.create_claim(data)

@pytest.mark.asyncio
async def test_create_claim_amount_exceeds_invoice(service, mock_db):
    mock_detail = MagicMock(id=1)
    with patch.object(service.detail_service, 'get_insurance_detail', return_value=mock_detail):
        with patch.object(service.detail_service, 'is_coverage_active', return_value=True):
            mock_invoice = MagicMock(total=Decimal('100.00'), status='sent')
            mock_db.get.return_value = mock_invoice
            data = InsuranceClaimCreate(
                insurance_detail_id=1, invoice_id=1, approved_amount=Decimal('200.00')
            )
            with pytest.raises(ClaimAmountExceedsInvoiceError):
                await service.create_claim(data)

# ------------------------------------------------------------------
# Test update_claim and status
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_claim_success(service, mock_db):
    existing = InsuranceClaim(id=1, status='submitted')
    mock_db.get.return_value = existing
    update_data = InsuranceClaimUpdate(status='approved')
    result = await service.update_claim(1, update_data)
    assert result.status == 'approved'
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_claim_not_found(service, mock_db):
    mock_db.get.return_value = None
    update_data = InsuranceClaimUpdate(status='approved')
    with pytest.raises(InsuranceClaimNotFoundError):
        await service.update_claim(999, update_data)

@pytest.mark.asyncio
async def test_update_claim_status(service, mock_db):
    existing = InsuranceClaim(id=1, status='submitted')
    mock_db.get.return_value = existing
    result = await service.update_claim_status(1, 'approved')
    assert result.status == 'approved'
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_claim_status_invalid(service, mock_db):
    existing = InsuranceClaim(id=1, status='submitted')
    mock_db.get.return_value = existing
    with pytest.raises(ValueError, match="Invalid status"):
        await service.update_claim_status(1, 'invalid')