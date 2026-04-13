"""Tests for IAM domain models — Pydantic validation, defaults, construction."""

import uuid

import pytest
from pydantic import ValidationError

from src.modules.iam.domain.tenant import (
    AISettings,
    GeneralSettings,
    GeneralSettingsUpdate,
    Tenant,
    TenantProfile,
    TenantSettingsUpdate,
    WebhookSettings,
)
from src.modules.iam.domain.tracking_config import TrackingConfig
from src.modules.iam.domain.user import SystemUserProfile, TeamMemberCreate, User


class TestTenant:
    def test_minimal_construction(self):
        t = Tenant(id=uuid.uuid4(), name="Acme", slug="acme")
        assert t.name == "Acme"
        assert t.slug == "acme"
        assert t.config_json == {}
        assert t.is_active is True
        assert t.can_use_platform_keys is False

    def test_full_construction(self):
        tid = uuid.uuid4()
        t = Tenant(
            id=tid,
            name="Big Corp",
            slug="big-corp",
            config_json={"company_name": "Big Corp"},
            openai_api_key="sk-abc",
            gemini_api_key="gm-xyz",
            webhook_secret="secret",
            can_use_platform_keys=True,
            is_active=False,
        )
        assert t.id == tid
        assert t.openai_api_key == "sk-abc"
        assert t.can_use_platform_keys is True
        assert t.is_active is False

    def test_optional_keys_default_none(self):
        t = Tenant(id=uuid.uuid4(), name="X", slug="x")
        assert t.openai_api_key is None
        assert t.gemini_api_key is None
        assert t.webhook_secret is None

    def test_name_required(self):
        with pytest.raises(ValidationError):
            Tenant(id=uuid.uuid4(), slug="no-name")  # type: ignore[call-arg]

    def test_slug_required(self):
        with pytest.raises(ValidationError):
            Tenant(id=uuid.uuid4(), name="No Slug")  # type: ignore[call-arg]

    def test_from_orm_mode(self):
        """model_validate works with dict (simulating ORM row)."""
        data = {
            "id": str(uuid.uuid4()),
            "name": "ORM Tenant",
            "slug": "orm-tenant",
            "config_json": {},
            "openai_api_key": None,
            "gemini_api_key": None,
            "webhook_secret": None,
            "can_use_platform_keys": False,
            "is_active": True,
            "created_at": None,
            "updated_at": None,
        }
        t = Tenant.model_validate(data)
        assert t.name == "ORM Tenant"


class TestAISettings:
    def test_defaults(self):
        s = AISettings()
        assert s.openai_api_key is None
        assert s.gemini_api_key is None
        assert s.can_use_platform_keys is False

    def test_with_keys(self):
        s = AISettings(openai_api_key="sk-123", can_use_platform_keys=True)
        assert s.openai_api_key == "sk-123"
        assert s.can_use_platform_keys is True


class TestTenantSettingsUpdate:
    def test_all_optional(self):
        u = TenantSettingsUpdate()
        assert u.openai_api_key is None
        assert u.gemini_api_key is None

    def test_partial_update(self):
        u = TenantSettingsUpdate(openai_api_key="new-key")
        assert u.openai_api_key == "new-key"
        assert u.gemini_api_key is None


class TestGeneralSettings:
    def test_defaults(self):
        g = GeneralSettings()
        assert g.default_currency == "USD"
        assert g.timezone == "UTC"

    def test_custom_values(self):
        g = GeneralSettings(default_currency="EUR", timezone="America/Bogota")
        assert g.default_currency == "EUR"
        assert g.timezone == "America/Bogota"


class TestGeneralSettingsUpdate:
    def test_all_optional(self):
        u = GeneralSettingsUpdate()
        assert u.default_currency is None
        assert u.timezone is None


class TestWebhookSettings:
    def test_required_url(self):
        w = WebhookSettings(webhook_url="https://example.com/hook")
        assert w.webhook_url == "https://example.com/hook"
        assert w.webhook_secret is None

    def test_with_secret(self):
        w = WebhookSettings(
            webhook_url="https://example.com/hook",
            webhook_secret="mysecret",
        )
        assert w.webhook_secret == "mysecret"

    def test_url_required(self):
        with pytest.raises(ValidationError):
            WebhookSettings()  # type: ignore[call-arg]


class TestTenantProfile:
    def test_construction(self):
        p = TenantProfile(id="abc-123", name="Acme", slug="acme")
        assert p.id == "abc-123"
        assert p.timezone == "UTC"

    def test_custom_timezone(self):
        p = TenantProfile(id="x", name="X", slug="x", timezone="America/Bogota")
        assert p.timezone == "America/Bogota"


class TestUser:
    def test_minimal_construction(self):
        u = User(id=uuid.uuid4(), email="user@example.com")
        assert u.email == "user@example.com"
        assert u.role == "admin"
        assert u.is_active is True
        assert u.full_name is None
        assert u.tenant_id is None

    def test_full_construction(self):
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        u = User(
            id=uid,
            full_name="Alice",
            email="alice@example.com",
            phone="+1234567890",
            clerk_id="clerk_123",
            role="member",
            is_active=False,
            tenant_id=tid,
        )
        assert u.full_name == "Alice"
        assert u.clerk_id == "clerk_123"
        assert u.role == "member"
        assert u.is_active is False
        assert u.tenant_id == tid

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            User(id=uuid.uuid4(), email="not-an-email")

    def test_email_required(self):
        with pytest.raises(ValidationError):
            User(id=uuid.uuid4())  # type: ignore[call-arg]

    def test_from_orm_mode(self):
        data = {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "full_name": "Test User",
            "phone": None,
            "clerk_id": None,
            "role": "admin",
            "is_active": True,
            "created_at": None,
            "updated_at": None,
        }
        u = User.model_validate(data)
        assert u.email == "test@example.com"


class TestSystemUserProfile:
    def test_minimal(self):
        p = SystemUserProfile(id="u1", full_name=None, email="u@example.com")
        assert p.id == "u1"
        assert p.full_name is None
        assert p.tenant is None

    def test_with_tenant(self):
        p = SystemUserProfile(
            id="u1",
            full_name="Alice",
            email="alice@example.com",
            tenant={"id": "t1"},
        )
        assert p.tenant == {"id": "t1"}


class TestTeamMemberCreate:
    def test_construction(self):
        m = TeamMemberCreate(
            full_name="Bob",
            email="bob@example.com",
            password="secret123",
        )
        assert m.full_name == "Bob"
        assert m.password == "secret123"

    def test_all_fields_required(self):
        with pytest.raises(ValidationError):
            TeamMemberCreate(full_name="Bob")  # type: ignore[call-arg]


class TestTrackingConfig:
    def test_all_optional_defaults(self):
        tc = TrackingConfig()
        assert tc.gtm_container_id is None
        assert tc.gtm_server_url is None
        assert tc.meta_pixel_id is None
        assert tc.ga_measurement_id is None

    def test_full_construction(self):
        tc = TrackingConfig(
            gtm_container_id="GTM-XXXX",
            gtm_server_url="https://ss.example.com",
            meta_pixel_id="123456789",
            ga_measurement_id="G-XXXXXXXXXX",
        )
        assert tc.gtm_container_id == "GTM-XXXX"
        assert tc.ga_measurement_id == "G-XXXXXXXXXX"

    def test_partial_construction(self):
        tc = TrackingConfig(gtm_container_id="GTM-ONLY")
        assert tc.gtm_container_id == "GTM-ONLY"
        assert tc.meta_pixel_id is None

    def test_from_attributes(self):
        """from_attributes=True allows ORM-style objects."""

        class FakeORM:
            gtm_container_id = "GTM-TEST"
            gtm_server_url = None
            meta_pixel_id = "999"
            ga_measurement_id = None

        tc = TrackingConfig.model_validate(FakeORM())
        assert tc.gtm_container_id == "GTM-TEST"
        assert tc.meta_pixel_id == "999"
