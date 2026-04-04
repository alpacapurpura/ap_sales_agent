"""Tests for TenantDomain entity, DomainStatus and DomainType enums."""
import uuid
from datetime import datetime, timezone

from src.modules.tenant_domains.domain.domain_entity import (
    DomainStatus,
    DomainType,
    TenantDomain,
)


class TestDomainStatusEnum:
    def test_all_statuses_are_strings(self):
        for status in DomainStatus:
            assert isinstance(status.value, str)

    def test_expected_status_values_exist(self):
        assert DomainStatus.PENDING_VERIFICATION == "pending_verification"
        assert DomainStatus.VERIFYING == "verifying"
        assert DomainStatus.ACTIVE == "active"
        assert DomainStatus.FAILED == "failed"
        assert DomainStatus.SUSPENDED == "suspended"

    def test_status_from_string(self):
        assert DomainStatus("active") is DomainStatus.ACTIVE
        assert DomainStatus("failed") is DomainStatus.FAILED


class TestDomainTypeEnum:
    def test_all_types_are_strings(self):
        for domain_type in DomainType:
            assert isinstance(domain_type.value, str)

    def test_expected_type_values_exist(self):
        assert DomainType.PLATFORM == "platform"
        assert DomainType.CUSTOM == "custom"

    def test_type_from_string(self):
        assert DomainType("platform") is DomainType.PLATFORM
        assert DomainType("custom") is DomainType.CUSTOM


class TestTenantDomainEntity:
    def test_create_platform_domain(self):
        domain_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        domain = TenantDomain(
            id=domain_id,
            tenant_id=tenant_id,
            hostname="myshop.nicolify.com",
            domain_type=DomainType.PLATFORM,
            status=DomainStatus.ACTIVE,
            is_primary=False,
        )
        assert domain.id == domain_id
        assert domain.tenant_id == tenant_id
        assert domain.hostname == "myshop.nicolify.com"
        assert domain.domain_type is DomainType.PLATFORM
        assert domain.status is DomainStatus.ACTIVE
        assert domain.is_primary is False

    def test_create_custom_domain_defaults(self):
        domain = TenantDomain(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            hostname="shop.example.com",
            domain_type=DomainType.CUSTOM,
        )
        assert domain.status is DomainStatus.PENDING_VERIFICATION
        assert domain.is_primary is False
        assert domain.cloudflare_hostname_id is None
        assert domain.ssl_status is None
        assert domain.verification_method is None
        assert domain.verification_cname_target is None
        assert domain.verification_txt_name is None
        assert domain.verification_txt_value is None
        assert domain.verified_at is None
        assert domain.deleted_at is None

    def test_optional_cf_fields_can_be_set(self):
        domain = TenantDomain(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            hostname="shop.example.com",
            domain_type=DomainType.CUSTOM,
            cloudflare_hostname_id="cf-abc-123",
            ssl_status="pending",
            verification_method="txt",
            verification_txt_name="_cf-custom-hostname.example.com",
            verification_txt_value="some-token-value",
        )
        assert domain.cloudflare_hostname_id == "cf-abc-123"
        assert domain.ssl_status == "pending"
        assert domain.verification_method == "txt"
        assert domain.verification_txt_name == "_cf-custom-hostname.example.com"
        assert domain.verification_txt_value == "some-token-value"

    def test_verified_at_can_be_set(self):
        now = datetime.now(timezone.utc)
        domain = TenantDomain(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            hostname="shop.example.com",
            domain_type=DomainType.CUSTOM,
            status=DomainStatus.ACTIVE,
            verified_at=now,
        )
        assert domain.verified_at == now

    def test_domain_is_pydantic_model(self):
        """TenantDomain is a Pydantic BaseModel — can be serialised to dict."""
        domain = TenantDomain(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            hostname="test.nicolify.com",
            domain_type=DomainType.PLATFORM,
        )
        data = domain.model_dump()
        assert "hostname" in data
        assert "tenant_id" in data
        assert "status" in data
