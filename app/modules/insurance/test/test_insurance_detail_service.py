import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.base import PatientNotFoundError
from app.modules.insurance.schemas.base import (
    InsuranceDetailCreate,
    InsuranceDetailUpdate,
)
from app.modules.insurance.services.insurance_detail import InsuranceDetailService
from app.common.exceptions.billing import InvoiceNotFoundError
from app.common.exceptions.insurance import (
    ClaimAmountExceedsInvoiceError,
    DuplicateInsuranceError,
    InsuranceClaimNotFoundError,
    InsuranceCoverageExpiredError,
    InsuranceDetailNotFoundError,
)
from app.modules.billing.models.base import Invoice
from app.modules.insurance.models.models import InsuranceClaim, InsuranceDetail
from app.modules.insurance.schemas.base import (
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
)
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
    return InsuranceDetailService(mock_db)


# ------------------------------------------------------------------
# Test create_insurance_detail
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_detail_success(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_db.get.return_value = mock_patient
    # Mock overlapping check returns False
    with patch.object(service, "_check_overlapping_policies", return_value=False):
        data = InsuranceDetailCreate(
            patient_id=1,
            provider_name="Blue Cross",
            policy_number="POL123",
            coverage_start=date(2025, 1, 1),
            coverage_end=date(2025, 12, 31),
            copay_percent=20.0,
        )
        result = await service.create_insurance_detail(data)
        assert result.provider_name == "Blue Cross"
        assert result.policy_number == "POL123"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_detail_patient_not_found(service, mock_db):
    mock_db.get.return_value = None
    data = InsuranceDetailCreate(patient_id=999, provider_name="X", policy_number="123")
    with pytest.raises(PatientNotFoundError):
        await service.create_insurance_detail(data)


@pytest.mark.asyncio
async def test_create_detail_overlapping_policy(service, mock_db):
    mock_patient = MagicMock(id=1)
    mock_db.get.return_value = mock_patient
    with patch.object(service, "_check_overlapping_policies", return_value=True):
        data = InsuranceDetailCreate(
            patient_id=1, provider_name="X", policy_number="123"
        )
        with pytest.raises(DuplicateInsuranceError):
            await service.create_insurance_detail(data)


# ------------------------------------------------------------------
# Test get_insurance_detail and get_all
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_detail_found(service, mock_db):
    expected = InsuranceDetail(id=1)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute.return_value = mock_result
    result = await service.get_insurance_detail(1)
    assert result == expected


@pytest.mark.asyncio
async def test_get_detail_not_found(service, mock_db):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await service.get_insurance_detail(999)
    assert result is None


# ------------------------------------------------------------------
# Test update_insurance_detail
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_detail_success(service, mock_db):
    existing = InsuranceDetail(id=1, provider_name="Old", policy_number="OLD123")
    mock_db.get.return_value = existing
    update_data = InsuranceDetailUpdate(provider_name="New Provider")
    result = await service.update_insurance_detail(1, update_data)
    assert result.provider_name == "New Provider"
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_detail_not_found(service, mock_db):
    mock_db.get.return_value = None
    update_data = InsuranceDetailUpdate(provider_name="X")
    with pytest.raises(InsuranceDetailNotFoundError):
        await service.update_insurance_detail(999, update_data)


# ------------------------------------------------------------------
# Test delete_insurance_detail
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_detail_success(service, mock_db):
    existing = InsuranceDetail(id=1)
    existing.claims = []  # no claims
    mock_db.get.return_value = existing
    result = await service.delete_insurance_detail(1)
    assert result is True
    mock_db.delete.assert_called_once_with(existing)


@pytest.mark.asyncio
async def test_delete_detail_with_claims(service, mock_db):
    existing = InsuranceDetail(id=1)
    existing.claims = [MagicMock()]  # has claims
    mock_db.get.return_value = existing
    with pytest.raises(
        ValueError, match="Cannot delete insurance detail with existing claims"
    ):
        await service.delete_insurance_detail(1)
    mock_db.delete.assert_not_called()
