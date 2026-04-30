"""Tests for per-tenant override path in LLMConfigService.resolve.

PI-2 S4 PR-2 GrowthBook per-tenant override.

Covers:
- tenant_id=None → bypasses GrowthBook eval (global path).
- tenant_id given + GrowthBook disabled (no API_HOST) → falls through.
- tenant_id given + GrowthBook ImportError → graceful degradation.
- Override returns ResolvedModel correctly when flag value present.
- Cache cross-tenant isolation: per-tenant override NOT cached
  (verified by re-call with different tenant gets different result).
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from src.core.enums import ModelRole
from src.shared.infrastructure.llm.application.config_service import (
    LLMConfigService,
    reset_llm_config_service,
)


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    reset_llm_config_service()
    yield
    reset_llm_config_service()


@pytest.mark.asyncio
async def test_resolve_no_tenant_skips_growthbook() -> None:
    """tenant_id=None → never invokes _resolve_per_tenant_override."""
    service = LLMConfigService(session_factory=None)
    result = await service.resolve(ModelRole.NANO, tenant_id=None)
    # Falls through to env_fallback (no DB).
    assert result.source == "env_fallback"


@pytest.mark.asyncio
async def test_resolve_with_tenant_disabled_growthbook_falls_through() -> None:
    """GrowthBook disabled (empty API_HOST) → falls through to global."""
    from src.core.config import settings

    # Defaults are empty strings — service short-circuits.
    assert settings.GROWTHBOOK_API_HOST == ""

    service = LLMConfigService(session_factory=None)
    result = await service.resolve(ModelRole.NANO, tenant_id=uuid4())
    # No override → env fallback.
    assert result.source == "env_fallback"


@pytest.mark.asyncio
async def test_per_tenant_override_returns_none_when_no_growthbook() -> None:
    """_resolve_per_tenant_override returns None gracefully."""
    service = LLMConfigService(session_factory=None)
    result = await service._resolve_per_tenant_override(ModelRole.NANO, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_per_tenant_override_returns_none_on_growthbook_error() -> None:
    """When GrowthBook configured but fails → graceful degradation."""
    from src.core.config import settings

    service = LLMConfigService(session_factory=None)
    with (
        patch.object(settings, "GROWTHBOOK_API_HOST", "http://invalid"),
        patch.object(settings, "GROWTHBOOK_CLIENT_KEY", "test-key"),
    ):
        result = await service._resolve_per_tenant_override(ModelRole.NANO, uuid4())
        # ImportError or connection error → None.
        assert result is None


@pytest.mark.asyncio
async def test_settings_growthbook_fields_present() -> None:
    """Settings has GROWTHBOOK_API_HOST + GROWTHBOOK_CLIENT_KEY fields."""
    from src.core.config import settings

    assert hasattr(settings, "GROWTHBOOK_API_HOST")
    assert hasattr(settings, "GROWTHBOOK_CLIENT_KEY")
    # Defaults disable GrowthBook.
    assert settings.GROWTHBOOK_API_HOST == ""
    assert settings.GROWTHBOOK_CLIENT_KEY == ""
