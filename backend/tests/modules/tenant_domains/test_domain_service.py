"""Tests for DomainService — mocks CloudflareClient, uses real repo + DB."""
import uuid
from unittest.mock import MagicMock

import pytest

from src.modules.tenant_domains.application.domain_service import DomainService
from src.modules.tenant_domains.domain.domain_entity import DomainStatus, DomainType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(db) -> DomainService:
    """Build a DomainService with a mocked (no-op) CloudflareClient."""
    service = DomainService(db)
    service.cf = MagicMock()
    service.cf.is_configured = False
    service.cf.put_kv = MagicMock()
    service.cf.delete_kv = MagicMock()
    service.cf.create_custom_hostname = MagicMock(return_value={})
    service.cf.delete_custom_hostname = MagicMock()
    service.cf.get_hostname_status = MagicMock(return_value={})
    return service


# ---------------------------------------------------------------------------
# Platform domain
# ---------------------------------------------------------------------------

class TestCreatePlatformDomain:
    def test_creates_active_platform_domain(self, db, tenant_id):
        service = _make_service(db)
        domain = service.create_platform_domain(tenant_id, slug="myshop")

        assert domain.hostname == "myshop.nicolify.com"
        assert domain.domain_type is DomainType.PLATFORM
        assert domain.status is DomainStatus.ACTIVE

    def test_platform_domain_syncs_kv(self, db, tenant_id):
        service = _make_service(db)
        # Enable CF for this test so put_kv gets called
        service.cf.is_configured = True
        service.create_platform_domain(tenant_id, slug="testslug")

        service.cf.put_kv.assert_called_once()
        call_args = service.cf.put_kv.call_args
        assert "testslug.nicolify.com" in call_args[0]

    def test_platform_domain_kv_failure_is_tolerated(self, db, tenant_id):
        """If KV sync fails, the domain is still persisted."""
        service = _make_service(db)
        service.cf.is_configured = True
        service.cf.put_kv.side_effect = Exception("CF timeout")

        domain = service.create_platform_domain(tenant_id, slug="resilient")
        assert domain.id is not None  # domain was saved despite CF error


# ---------------------------------------------------------------------------
# Custom domain
# ---------------------------------------------------------------------------

class TestCreateCustomDomain:
    def test_creates_pending_custom_domain_no_cf(self, db, tenant_id):
        """When CF is not configured, domain is saved with no CF fields."""
        service = _make_service(db)
        service.cf.create_custom_hostname.return_value = {}

        domain = service.create_custom_domain(tenant_id, hostname="shop.example.com")

        assert domain.hostname == "shop.example.com"
        assert domain.domain_type is DomainType.CUSTOM
        assert domain.status is DomainStatus.PENDING_VERIFICATION

    def test_creates_custom_domain_with_cf_data(self, db, tenant_id):
        """When CF returns verification data, fields are persisted."""
        service = _make_service(db)
        service.cf.create_custom_hostname.return_value = {
            "id": "cf-hostname-id-abc",
            "ssl": {"status": "pending"},
            "ownership_verification": {
                "type": "txt",
                "name": "_cf.example.com",
                "value": "token-xyz",
            },
        }

        domain = service.create_custom_domain(tenant_id, hostname="shop.example.com")

        assert domain.cloudflare_hostname_id == "cf-hostname-id-abc"
        assert domain.ssl_status == "pending"
        assert domain.verification_method == "txt"
        assert domain.verification_txt_name == "_cf.example.com"
        assert domain.verification_txt_value == "token-xyz"

    def test_cf_failure_saves_domain_as_failed(self, db, tenant_id):
        """If CF call raises, domain is saved with FAILED status."""
        service = _make_service(db)
        service.cf.create_custom_hostname.side_effect = Exception("CF down")

        domain = service.create_custom_domain(tenant_id, hostname="broken.example.com")

        assert domain.status is DomainStatus.FAILED


# ---------------------------------------------------------------------------
# Verify domain
# ---------------------------------------------------------------------------

class TestVerifyDomain:
    def test_verify_active_ssl_sets_domain_active(self, db, tenant_id):
        service = _make_service(db)
        # First create the domain
        created = service.create_custom_domain(tenant_id, hostname="verify.example.com")
        # Manually set a CF hostname ID so verify_domain doesn't raise
        created.cloudflare_hostname_id = "cf-id-verify"
        service.repo.update(created)

        service.cf.get_hostname_status.return_value = {"ssl": {"status": "active"}}
        updated = service.verify_domain(created.id, tenant_id)

        assert updated.status is DomainStatus.ACTIVE
        assert updated.ssl_status == "active"
        assert updated.verified_at is not None

    def test_verify_pending_ssl_sets_domain_verifying(self, db, tenant_id):
        service = _make_service(db)
        created = service.create_custom_domain(tenant_id, hostname="pending.example.com")
        created.cloudflare_hostname_id = "cf-id-pending"
        service.repo.update(created)

        service.cf.get_hostname_status.return_value = {"ssl": {"status": "pending_validation"}}
        updated = service.verify_domain(created.id, tenant_id)

        assert updated.status is DomainStatus.VERIFYING
        assert updated.ssl_status == "pending_validation"

    def test_verify_nonexistent_domain_raises(self, db, tenant_id):
        service = _make_service(db)
        with pytest.raises(ValueError, match="Domain not found"):
            service.verify_domain(uuid.uuid4(), tenant_id)

    def test_verify_domain_without_cf_id_raises(self, db, tenant_id):
        service = _make_service(db)
        created = service.create_custom_domain(tenant_id, hostname="nocf.example.com")
        # cloudflare_hostname_id is None — cannot verify

        with pytest.raises(ValueError, match="No CF hostname ID"):
            service.verify_domain(created.id, tenant_id)


# ---------------------------------------------------------------------------
# Delete domain
# ---------------------------------------------------------------------------

class TestDeleteDomain:
    def test_delete_soft_deletes_domain(self, db, tenant_id):
        service = _make_service(db)
        created = service.create_platform_domain(tenant_id, slug="todelete")

        service.delete_domain(created.id, tenant_id)

        result = service.get_domain(created.id, tenant_id)
        assert result is None

    def test_delete_calls_cf_cleanup_when_cf_id_set(self, db, tenant_id):
        service = _make_service(db)
        service.cf.create_custom_hostname.return_value = {"id": "cf-cleanup-id", "ssl": {}}
        created = service.create_custom_domain(tenant_id, hostname="cleanup.example.com")

        service.delete_domain(created.id, tenant_id)

        service.cf.delete_custom_hostname.assert_called_once_with("cf-cleanup-id")

    def test_delete_nonexistent_domain_raises(self, db, tenant_id):
        service = _make_service(db)
        with pytest.raises(ValueError, match="Domain not found"):
            service.delete_domain(uuid.uuid4(), tenant_id)

    def test_delete_cf_error_still_soft_deletes(self, db, tenant_id):
        """If CF cleanup fails, the domain record should still be soft-deleted."""
        service = _make_service(db)
        service.cf.delete_kv.side_effect = Exception("CF unavailable")
        created = service.create_platform_domain(tenant_id, slug="cfbroken")

        service.delete_domain(created.id, tenant_id)

        result = service.get_domain(created.id, tenant_id)
        assert result is None  # still deleted despite CF error
