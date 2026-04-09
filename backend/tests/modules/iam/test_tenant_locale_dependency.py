"""Tests for get_tenant_locale FastAPI dependency."""

import uuid

from sqlalchemy.orm import Session

from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.domain.locale import TenantLocale


class TestGetTenantLocale:
    """Unit tests for the tenant locale resolution logic."""

    def test_returns_tenant_values(self, db: Session) -> None:
        """When tenant has currency=PEN and timezone=America/Lima, return those."""
        tenant_id = uuid.uuid4()
        tenant = TenantModel(
            id=tenant_id,
            name="Test",
            slug=f"test-{tenant_id.hex[:8]}",
            default_currency="PEN",
            timezone="America/Lima",
        )
        db.add(tenant)
        db.commit()

        from src.modules.iam.api.dependencies import _resolve_tenant_locale

        result = _resolve_tenant_locale(db, tenant_id)
        assert isinstance(result, TenantLocale)
        assert result.currency == "PEN"
        assert result.timezone == "America/Lima"

    def test_fallback_when_fields_null(self, db: Session) -> None:
        """When tenant has null currency/timezone, fall back to defaults."""
        tenant_id = uuid.uuid4()
        tenant = TenantModel(
            id=tenant_id,
            name="Test Null",
            slug=f"test-null-{tenant_id.hex[:8]}",
        )
        db.add(tenant)
        db.commit()

        from src.modules.iam.api.dependencies import _resolve_tenant_locale

        result = _resolve_tenant_locale(db, tenant_id)
        assert result.currency == "USD"
        assert result.timezone == "UTC"

    def test_missing_tenant_returns_default(self, db: Session) -> None:
        """When tenant doesn't exist, return default locale."""
        from src.modules.iam.api.dependencies import _resolve_tenant_locale

        result = _resolve_tenant_locale(db, uuid.uuid4())
        assert result == TenantLocale.default()
