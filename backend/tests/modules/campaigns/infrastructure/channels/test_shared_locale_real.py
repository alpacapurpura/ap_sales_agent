"""Tests for _resolve_tenant_locale — real TenantModel lookup + LRU cache.

TDD RED → GREEN for Sub-F:
- TenantModel.config_json {"tenant_locale": {"currency": "PEN", "timezone": "America/Lima"}}
  → locale (PEN, America/Lima)
- TenantModel.config_json without tenant_locale key → fallback default
- TenantModel absent (db error) → fallback default
- LRU cache hit (same tenant_id) → no second db query (mock counter assert <=1 db call)

PR-7 PI-1 S3.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_campaigns.infrastructure.channels.shared import (
    _resolve_tenant_locale,
    invalidate_locale_cache,
)
from luana_core_platform.domain.locale import TenantLocale


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_tenant_model(config_json: dict) -> MagicMock:
    """Return a mock TenantModel with the given config_json."""
    tenant = MagicMock()
    tenant.config_json = config_json
    return tenant


# ── Tests ──────────────────────────────────────────────────────────────────────


def test_resolve_locale_pen_lima() -> None:
    """config_json with tenant_locale → TenantLocale(PEN, America/Lima)."""
    tenant_id = uuid4()
    mock_db = MagicMock()
    tenant = _make_tenant_model({"tenant_locale": {"currency": "PEN", "timezone": "America/Lima"}})

    # Invalidate any cached entry for this tenant_id first
    invalidate_locale_cache()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = tenant
    mock_db.execute.return_value = mock_result

    locale = _resolve_tenant_locale(tenant_id, db=mock_db)

    assert isinstance(locale, TenantLocale)
    assert locale.currency == "PEN"
    assert locale.timezone == "America/Lima"


def test_resolve_locale_missing_tenant_locale_key_returns_default() -> None:
    """config_json without tenant_locale key → TenantLocale.default()."""
    tenant_id = uuid4()
    mock_db = MagicMock()
    tenant = _make_tenant_model({"some_other_key": "value"})

    invalidate_locale_cache()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = tenant
    mock_db.execute.return_value = mock_result

    locale = _resolve_tenant_locale(tenant_id, db=mock_db)

    default = TenantLocale.default()
    assert locale.currency == default.currency
    assert locale.timezone == default.timezone


def test_resolve_locale_tenant_not_found_returns_default() -> None:
    """TenantModel not found (None) → TenantLocale.default()."""
    tenant_id = uuid4()
    mock_db = MagicMock()

    invalidate_locale_cache()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    locale = _resolve_tenant_locale(tenant_id, db=mock_db)

    default = TenantLocale.default()
    assert locale.currency == default.currency
    assert locale.timezone == default.timezone


def test_resolve_locale_db_error_returns_default() -> None:
    """DB raises exception → TenantLocale.default() (graceful degradation)."""
    tenant_id = uuid4()
    mock_db = MagicMock()
    mock_db.execute.side_effect = RuntimeError("Connection refused")

    invalidate_locale_cache()

    locale = _resolve_tenant_locale(tenant_id, db=mock_db)

    default = TenantLocale.default()
    assert locale.currency == default.currency
    assert locale.timezone == default.timezone


def test_resolve_locale_no_db_returns_default() -> None:
    """No db passed → TenantLocale.default() (backward compat — old callers)."""
    tenant_id = uuid4()
    invalidate_locale_cache()

    locale = _resolve_tenant_locale(tenant_id, db=None)

    default = TenantLocale.default()
    assert locale.currency == default.currency
    assert locale.timezone == default.timezone


def test_resolve_locale_lru_cache_second_call_no_db_query() -> None:
    """Same tenant_id called twice → DB queried at most once (LRU cache hit)."""
    tenant_id = uuid4()
    mock_db = MagicMock()
    tenant = _make_tenant_model({"tenant_locale": {"currency": "MXN", "timezone": "America/Mexico_City"}})

    invalidate_locale_cache()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = tenant
    mock_db.execute.return_value = mock_result

    # First call — DB hit
    locale1 = _resolve_tenant_locale(tenant_id, db=mock_db)
    # Second call — should hit LRU cache
    locale2 = _resolve_tenant_locale(tenant_id, db=mock_db)

    # DB called at most once
    assert mock_db.execute.call_count <= 1
    assert locale1.currency == "MXN"
    assert locale2.currency == "MXN"
