"""Tests for LLMConfigService — cache + pub/sub + env fallback.

PI-2 S4 PR-1 db-registry-admin-ui.

Covers:
- Cache hit returns same instance without DB I/O.
- Cache miss + no session_factory → env fallback.
- TTL expiry → re-resolve.
- invalidate_cache(role) flushes single key.
- invalidate_cache() flushes all.
- publish_invalidation soft-fail on Redis error.
- Singleton get/init/reset lifecycle.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.enums import AIProvider, ModelRole
from src.shared.infrastructure.llm.application.config_service import (
    CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL,
    LLMConfigService,
    get_llm_config_service,
    init_llm_config_service,
    reset_llm_config_service,
)
from src.shared.infrastructure.llm.domain.resolved import ResolvedModel


@pytest.fixture(autouse=True)
def _reset_singleton_after_each() -> None:
    """Ensure module singleton is reset between tests."""
    reset_llm_config_service()
    yield
    reset_llm_config_service()


def test_resolve_sync_returns_env_fallback_when_cache_empty() -> None:
    """Cache empty + no session → env fallback path."""
    service = LLMConfigService(session_factory=None, redis_client=None)
    result = service.resolve_sync_cached_only(ModelRole.NANO)
    assert isinstance(result, ResolvedModel)
    assert result.source == "env_fallback"
    assert result.binding_id is None
    assert result.model  # non-empty


def test_resolve_sync_returns_cached_when_present() -> None:
    """Cache hit returns stored value without I/O."""
    service = LLMConfigService(session_factory=None)
    cached = ResolvedModel(
        provider=AIProvider.DEEPSEEK,
        model="deepseek-v4-flash",
        config={},
        source="db_binding",
        binding_id="abc-123",
    )
    service._cache_put(ModelRole.NANO, cached)
    result = service.resolve_sync_cached_only(ModelRole.NANO)
    assert result.binding_id == "abc-123"
    assert result.source == "db_binding"


def test_cache_ttl_expiry_triggers_re_resolve() -> None:
    """After TTL expires, cache returns None and falls back to env."""
    service = LLMConfigService(session_factory=None, ttl_seconds=0.01)
    cached = ResolvedModel(
        provider=AIProvider.DEEPSEEK,
        model="deepseek-v4-flash",
        config={},
        source="db_binding",
        binding_id="abc-123",
    )
    service._cache_put(ModelRole.NANO, cached)
    time.sleep(0.05)
    result = service.resolve_sync_cached_only(ModelRole.NANO)
    assert result.source == "env_fallback"  # cache expired, fell to env


def test_invalidate_cache_specific_role() -> None:
    """invalidate_cache(role) flushes only that role."""
    service = LLMConfigService(session_factory=None)
    a = ResolvedModel(provider=AIProvider.OPENAI, model="m1", config={}, source="db_binding", binding_id="1")
    b = ResolvedModel(provider=AIProvider.OPENAI, model="m2", config={}, source="db_binding", binding_id="2")
    service._cache_put(ModelRole.NANO, a)
    service._cache_put(ModelRole.FAST, b)

    service.invalidate_cache(ModelRole.NANO)

    assert service._cache_get(ModelRole.NANO) is None
    assert service._cache_get(ModelRole.FAST) is not None


def test_invalidate_cache_all() -> None:
    """invalidate_cache() with no arg flushes everything."""
    service = LLMConfigService(session_factory=None)
    a = ResolvedModel(provider=AIProvider.OPENAI, model="m1", config={}, source="db_binding", binding_id="1")
    service._cache_put(ModelRole.NANO, a)
    service._cache_put(ModelRole.FAST, a)

    service.invalidate_cache()

    assert service._cache_get(ModelRole.NANO) is None
    assert service._cache_get(ModelRole.FAST) is None


@pytest.mark.asyncio
async def test_publish_invalidation_no_redis_is_noop() -> None:
    """publish_invalidation with no Redis client returns silently."""
    service = LLMConfigService(session_factory=None, redis_client=None)
    # Should not raise
    await service.publish_invalidation()


@pytest.mark.asyncio
async def test_publish_invalidation_calls_redis_publish() -> None:
    """publish_invalidation publishes to canonical channel."""
    redis_mock = MagicMock()
    redis_mock.publish = AsyncMock()
    service = LLMConfigService(session_factory=None, redis_client=redis_mock)

    await service.publish_invalidation()

    redis_mock.publish.assert_called_once_with(CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL, "")


@pytest.mark.asyncio
async def test_publish_invalidation_soft_fails_on_redis_exception() -> None:
    """publish_invalidation does not raise when Redis publish fails."""
    redis_mock = MagicMock()
    redis_mock.publish = AsyncMock(side_effect=ConnectionError("redis down"))
    service = LLMConfigService(session_factory=None, redis_client=redis_mock)

    # Must NOT raise.
    await service.publish_invalidation()


def test_singleton_init_and_get() -> None:
    """init_llm_config_service stores singleton; get returns it."""
    assert get_llm_config_service() is None
    svc = init_llm_config_service(session_factory=None, redis_client=None)
    assert get_llm_config_service() is svc


def test_singleton_reset_clears() -> None:
    """reset_llm_config_service nullifies singleton."""
    init_llm_config_service(session_factory=None, redis_client=None)
    assert get_llm_config_service() is not None
    reset_llm_config_service()
    assert get_llm_config_service() is None


@pytest.mark.asyncio
async def test_resolve_async_cache_hit_short_circuits() -> None:
    """async resolve returns cached value without DB call."""
    service = LLMConfigService(session_factory=None)
    cached = ResolvedModel(
        provider=AIProvider.DEEPSEEK,
        model="deepseek-v4-flash",
        config={},
        source="db_binding",
        binding_id="cache-hit-id",
    )
    service._cache_put(ModelRole.NANO, cached)

    result = await service.resolve(ModelRole.NANO)

    assert result.binding_id == "cache-hit-id"


@pytest.mark.asyncio
async def test_resolve_async_no_session_factory_falls_back_env() -> None:
    """async resolve with no session_factory returns env_fallback."""
    service = LLMConfigService(session_factory=None)
    result = await service.resolve(ModelRole.NANO)
    assert result.source == "env_fallback"


def test_settings_get_model_uses_service_when_initialized() -> None:
    """Settings.get_model wraps via singleton when service is set."""
    from src.core.config import settings

    # Pre-init: should use env fallback.
    pre_init_value = settings.get_model(ModelRole.NANO)
    assert pre_init_value  # non-empty

    # Init service + populate cache.
    svc = init_llm_config_service(session_factory=None, redis_client=None)
    cached = ResolvedModel(
        provider=AIProvider.DEEPSEEK,
        model="custom-cached-model",
        config={},
        source="db_binding",
        binding_id="cache-id",
    )
    svc._cache_put(ModelRole.NANO, cached)

    # Now Settings.get_model should return cached value.
    assert settings.get_model(ModelRole.NANO) == "custom-cached-model"

    reset_llm_config_service()
