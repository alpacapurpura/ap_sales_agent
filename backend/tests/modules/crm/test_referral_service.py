"""
Tests for ReferralService: code generation, retrieval, deactivation, Shopify extraction.

CRM-07: Referral code generation with collision retry, tenant isolation, Shopify import.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from luana_core_crm.infrastructure.models.referral_code_model import ReferralCodeModel

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_referral_code(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    customer_id: uuid.UUID | None = None,
    code: str = "REF-TEST01",
    source: str = "internal",
    is_active: bool = True,
) -> ReferralCodeModel:
    record = ReferralCodeModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id or uuid.uuid4(),
        code=code,
        source=source,
        is_active=is_active,
    )
    db.add(record)
    db.flush()
    return record


# ---------------------------------------------------------------------------
# Tests: Generate Code
# ---------------------------------------------------------------------------


class TestGenerateCode:
    """generate_code creates REF-XXXXXX format with collision retry."""

    def test_generate_code_format(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        svc = ReferralService(db)
        profile_id = uuid.uuid4()
        result = svc.generate_code(tenant_id=tenant_id, customer_id=profile_id)

        assert result.code.startswith("REF-")
        suffix = result.code.split("-", 1)[1]
        assert len(suffix) == 6
        assert suffix.isalnum()

    def test_generate_two_codes_different(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        svc = ReferralService(db)
        profile_id = uuid.uuid4()
        code1 = svc.generate_code(tenant_id=tenant_id, customer_id=profile_id)
        code2 = svc.generate_code(tenant_id=tenant_id, customer_id=profile_id)

        assert code1.code != code2.code

    def test_generate_code_collision_retry(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        svc = ReferralService(db)
        profile_id = uuid.uuid4()

        call_count = 0
        original_flush = db.flush

        def flaky_flush(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                msg = "duplicate key"
                raise IntegrityError(msg, {}, None)
            return original_flush(*args, **kwargs)

        with patch.object(db, "flush", side_effect=flaky_flush):
            result = svc.generate_code(tenant_id=tenant_id, customer_id=profile_id)

        assert result is not None
        assert call_count == 3

    def test_generate_code_tenant_isolation(self, db: Session, other_tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        svc = ReferralService(db)
        profile_a = uuid.uuid4()
        profile_b = uuid.uuid4()

        code_a = svc.generate_code(tenant_id=SAMPLE_TENANT_ID, customer_id=profile_a)
        code_b = svc.generate_code(tenant_id=other_tenant_id, customer_id=profile_b)

        codes_a = svc.get_codes_by_tenant(SAMPLE_TENANT_ID)
        codes_b = svc.get_codes_by_tenant(other_tenant_id)

        assert code_a.code in [c.code for c in codes_a]
        assert code_a.code not in [c.code for c in codes_b]
        assert code_b.code in [c.code for c in codes_b]
        assert code_b.code not in [c.code for c in codes_a]


# ---------------------------------------------------------------------------
# Tests: Get Codes By Tenant
# ---------------------------------------------------------------------------


class TestGetCodesByTenant:
    """get_codes_by_tenant filters by tenant and active status."""

    def test_active_only_returns_active(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        _make_referral_code(db, tenant_id=tenant_id, code="REF-ACTIVE1", is_active=True)
        _make_referral_code(db, tenant_id=tenant_id, code="REF-INACTIVE1", is_active=False)

        svc = ReferralService(db)
        results = svc.get_codes_by_tenant(tenant_id, active_only=True)

        assert len(results) == 1
        assert results[0].code == "REF-ACTIVE1"

    def test_all_returns_inactive_too(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        _make_referral_code(db, tenant_id=tenant_id, code="REF-ACTIVE2", is_active=True)
        _make_referral_code(db, tenant_id=tenant_id, code="REF-INACTIVE2", is_active=False)

        svc = ReferralService(db)
        results = svc.get_codes_by_tenant(tenant_id, active_only=False)

        assert len(results) == 2

    def test_tenant_isolation(self, db: Session, tenant_id, other_tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        _make_referral_code(db, tenant_id=tenant_id, code="REF-TENANTA", is_active=True)
        _make_referral_code(db, tenant_id=other_tenant_id, code="REF-TENANTB", is_active=True)

        svc = ReferralService(db)
        results_a = svc.get_codes_by_tenant(tenant_id)
        results_b = svc.get_codes_by_tenant(other_tenant_id)

        assert len(results_a) == 1
        assert results_a[0].code == "REF-TENANTA"
        assert len(results_b) == 1
        assert results_b[0].code == "REF-TENANTB"


# ---------------------------------------------------------------------------
# Tests: Get Code By Customer
# ---------------------------------------------------------------------------


class TestGetCodeByCustomer:
    """get_code_by_customer retrieves active code for a specific customer."""

    def test_returns_active_code(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        customer = uuid.uuid4()
        _make_referral_code(db, tenant_id=tenant_id, customer_id=customer, code="REF-CUST1")

        svc = ReferralService(db)
        result = svc.get_code_by_customer(tenant_id, customer)

        assert result is not None
        assert result.code == "REF-CUST1"

    def test_returns_none_when_no_code(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        svc = ReferralService(db)
        result = svc.get_code_by_customer(tenant_id, uuid.uuid4())

        assert result is None

    def test_returns_none_when_deactivated(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        customer = uuid.uuid4()
        _make_referral_code(db, tenant_id=tenant_id, customer_id=customer, code="REF-DEACT", is_active=False)

        svc = ReferralService(db)
        result = svc.get_code_by_customer(tenant_id, customer)

        assert result is None


# ---------------------------------------------------------------------------
# Tests: Deactivate Code
# ---------------------------------------------------------------------------


class TestDeactivateCode:
    """deactivate_code soft-deactivates a referral code."""

    def test_deactivate_sets_inactive(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        code_record = _make_referral_code(db, tenant_id=tenant_id, code="REF-DEACT1")

        svc = ReferralService(db)
        svc.deactivate_code(tenant_id, code_record.id)

        db.refresh(code_record)
        assert code_record.is_active is False

    def test_deactivate_other_tenant_no_effect(self, db: Session, tenant_id, other_tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        code_record = _make_referral_code(db, tenant_id=tenant_id, code="REF-NOEFFECT")

        svc = ReferralService(db)
        svc.deactivate_code(other_tenant_id, code_record.id)

        db.refresh(code_record)
        assert code_record.is_active is True

    def test_deactivate_nonexistent_id_silent(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        svc = ReferralService(db)
        svc.deactivate_code(tenant_id, uuid.uuid4())


# ---------------------------------------------------------------------------
# Tests: Extract Shopify Codes
# ---------------------------------------------------------------------------


class TestExtractShopifyCodes:
    """extract_shopify_codes imports codes from Shopify GraphQL API."""

    @pytest.mark.asyncio
    async def test_import_shopify_codes(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        mock_response = MagicMock()
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = {
            "data": {
                "codeDiscountNodes": {
                    "nodes": [
                        {
                            "codeDiscount": {
                                "title": "Summer Sale",
                                "codes": {"nodes": [{"code": "SUMMER20"}, {"code": "SUMMER30"}]},
                            }
                        },
                    ]
                }
            }
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        svc = ReferralService(db)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await svc.extract_shopify_codes(
                tenant_id=tenant_id,
                shop_domain="test-shop.myshopify.com",
                access_token="test-token",
            )

        assert len(result) == 2
        assert result[0].source == "shopify"
        assert result[0].code in ("SUMMER20", "SUMMER30")
        assert result[1].code in ("SUMMER20", "SUMMER30")

    @pytest.mark.asyncio
    async def test_skip_duplicate_code(self, db: Session, tenant_id):
        from luana_core_crm.application.services.referral_service import ReferralService

        _make_referral_code(db, tenant_id=tenant_id, code="EXISTING", source="internal")

        mock_response = MagicMock()
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = {
            "data": {
                "codeDiscountNodes": {
                    "nodes": [
                        {
                            "codeDiscount": {
                                "title": "Dup",
                                "codes": {"nodes": [{"code": "EXISTING"}, {"code": "NEWCODE"}]},
                            }
                        },
                    ]
                }
            }
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        svc = ReferralService(db)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await svc.extract_shopify_codes(
                tenant_id=tenant_id,
                shop_domain="test-shop.myshopify.com",
                access_token="test-token",
            )

        assert len(result) == 1
        assert result[0].code == "NEWCODE"

    @pytest.mark.asyncio
    async def test_network_error_returns_empty(self, db: Session, tenant_id):
        import httpx

        from luana_core_crm.application.services.referral_service import ReferralService

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        svc = ReferralService(db)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await svc.extract_shopify_codes(
                tenant_id=tenant_id,
                shop_domain="test-shop.myshopify.com",
                access_token="test-token",
            )

        assert result == []
