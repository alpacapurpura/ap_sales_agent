"""LLM Config Service — runtime SSoT resolution + cache + Redis pub/sub.

PI-2 S4 PR-1 db-registry-admin-ui.

Pattern reuse: mirrors ``shared/billing/application/plan_service.py``
``subscribe_cache_invalidations`` Redis pub/sub task and TTL cache pattern.

Architecture:
- In-memory dict TTL cache 60s per role (≤6 keys global). asyncio
  single-thread = no lock needed (D-6 architect).
- Redis pub/sub channel ``cache_invalidate:llm_role_binding`` flushes
  cache cross-pod when admin commits change (D-3 reuse PlanService pattern).
- ``resolve_sync_cached_only(role)`` for sync paths (Settings.get_model
  callers do NOT block event loop — D-2 architect).
- ``resolve(role, tenant_id=None)`` async path: cache hit → return; miss →
  DB SELECT WHERE role=X AND tenant_id IS NULL AND is_active=TRUE → cache.
- DB unreachable / no active row → fallback to env vars (graceful
  degradation per ``tessl/graceful-degradation``).

D-7: pub/sub subscriber starts via FastAPI ``lifespan`` event in main.py,
NOT a separate worker file (D-3 reuse).
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import structlog

from src.core.config import settings
from src.core.enums import AIProvider, ModelRole
from src.shared.infrastructure.llm.domain.resolved import ResolvedModel

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL = "cache_invalidate:llm_role_binding"
DEFAULT_TTL_SECONDS = 60.0


class LLMConfigService:
    """Runtime resolver for ``ModelRole → (provider, model, config)``.

    Hot path SLA: ``resolve_sync_cached_only`` p99 <1ms (cache hit) /
    fallback env <0.1ms. Async ``resolve`` populates cache on miss.
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession] | None = None,
        redis_client: Redis | None = None,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Initialize service with optional DB factory + Redis client."""
        self._session_factory = session_factory
        self._redis = redis_client
        self._ttl = ttl_seconds
        # Cache: role.value → (resolved, expires_at_monotonic)
        self._cache: dict[str, tuple[ResolvedModel, float]] = {}
        self._subscriber_task: asyncio.Task[None] | None = None

    # ──────────────────────────────────────────────────────────────────
    # Cache primitives
    # ──────────────────────────────────────────────────────────────────

    def _cache_get(self, role: ModelRole) -> ResolvedModel | None:
        entry = self._cache.get(role.value)
        if entry is None:
            return None
        resolved, expires = entry
        if time.monotonic() >= expires:
            del self._cache[role.value]
            return None
        return resolved

    def _cache_put(self, role: ModelRole, resolved: ResolvedModel) -> None:
        self._cache[role.value] = (resolved, time.monotonic() + self._ttl)

    def invalidate_cache(self, role: ModelRole | None = None) -> None:
        """Local cache flush. Called by pub/sub subscriber + activate/deactivate."""
        if role is None:
            self._cache.clear()
        else:
            self._cache.pop(role.value, None)

    # ──────────────────────────────────────────────────────────────────
    # Resolution paths
    # ──────────────────────────────────────────────────────────────────

    def resolve_sync_cached_only(self, role: ModelRole) -> ResolvedModel:
        """Sync resolution. Cache hit → DB binding. Miss → env fallback.

        Never blocks event loop. Used by ``Settings.get_model`` (D-1, D-2).
        """
        cached = self._cache_get(role)
        if cached is not None:
            return cached
        return self._resolve_from_env(role)

    async def resolve(self, role: ModelRole, tenant_id: UUID | None = None) -> ResolvedModel:
        """Async resolution chain ordered by priority.

        Order (S4 PR-2): per-tenant GrowthBook override → cache hit (global) →
        DB global binding → env fallback.

        Per-tenant overrides are NOT cached cross-tenant (would leak isolation).
        """
        # 1. Per-tenant override (S4 PR-2 GrowthBook)
        if tenant_id is not None:
            tenant_override = await self._resolve_per_tenant_override(role, tenant_id)
            if tenant_override is not None:
                return tenant_override

        cached = self._cache_get(role)
        if cached is not None:
            return cached

        if self._session_factory is None:
            return self._resolve_from_env(role)

        try:
            from src.shared.infrastructure.llm.infrastructure.role_binding_repository import (
                SqlAlchemyLLMRoleBindingRepository,
            )

            async with self._session_factory() as session:  # type: ignore[misc]
                repo = SqlAlchemyLLMRoleBindingRepository(session)
                binding = await repo.find_active_global(role)

            if binding is None:
                resolved = self._resolve_from_env(role)
            else:
                resolved = ResolvedModel(
                    provider=binding.provider,
                    model=binding.model,
                    config=binding.config,
                    source="db_binding",
                    binding_id=str(binding.id),
                )
        except Exception as exc:  # noqa: BLE001 — graceful degradation
            logger.warning(
                "llm_config_resolve_db_failed_falling_back_env",
                role=role.value,
                error=str(exc),
            )
            resolved = self._resolve_from_env(role)

        self._cache_put(role, resolved)
        return resolved

    @staticmethod
    def _resolve_from_env(role: ModelRole) -> ResolvedModel:
        return ResolvedModel(
            provider=settings.get_provider_for_role(role),
            model=_get_model_from_env(role),
            config={},
            source="env_fallback",
            binding_id=None,
        )

    async def _resolve_per_tenant_override(self, role: ModelRole, tenant_id: UUID) -> ResolvedModel | None:  # noqa: PLR0911
        """S4 PR-2 — query GrowthBook for per-tenant flag override.

        Returns ResolvedModel when flag set + valid; None otherwise (caller
        falls through to global cache/DB/env chain).

        Graceful degradation: GrowthBook unavailable / SDK not installed /
        flag inactive → returns None silently. Cero impact on global path.
        """
        if not settings.GROWTHBOOK_API_HOST or not settings.GROWTHBOOK_CLIENT_KEY:
            return None

        try:
            from growthbook import GrowthBook  # type: ignore[import-not-found]

            gb = GrowthBook(
                api_host=settings.GROWTHBOOK_API_HOST,
                client_key=settings.GROWTHBOOK_CLIENT_KEY,
                attributes={"tenant_id": str(tenant_id), "role": role.value},
            )
            await gb.load_features()  # type: ignore[func-returns-value]
            flag_value = gb.eval_feature(f"llm_model_override_{role.value.lower()}")
            if flag_value is None or flag_value.value is None:
                return None
            override = flag_value.value
            if not isinstance(override, dict):
                return None
            provider = override.get("provider")
            model = override.get("model")
            if not provider or not model:
                return None
            return ResolvedModel(
                provider=AIProvider(provider),
                model=model,
                config=override.get("config", {}),
                source="db_binding",
                binding_id=f"growthbook:tenant:{tenant_id}",
            )
        except ImportError:
            return None
        except Exception as exc:  # noqa: BLE001 — graceful degradation
            logger.warning(
                "llm_config_growthbook_eval_failed",
                role=role.value,
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            return None

    # ──────────────────────────────────────────────────────────────────
    # Pub/sub (mirror PlanService pattern)
    # ──────────────────────────────────────────────────────────────────

    async def publish_invalidation(self) -> None:
        """Best-effort publish. Soft-fail per graceful-degradation rule."""
        if self._redis is None:
            return
        try:
            await self._redis.publish(CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL, "")
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "llm_config_invalidate_publish_failed",
                channel=CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL,
                error=str(exc),
            )

    async def subscribe_cache_invalidations(self) -> None:
        """Long-running task. Started by FastAPI lifespan event.

        Mirrors PlanService.subscribe_cache_invalidations exactly.
        Soft-fail with exponential backoff on Redis disconnect.
        """
        if self._redis is None:
            logger.info("llm_config_pubsub_skipped_no_redis")
            return
        backoff = 1.0
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL)
                logger.info("llm_config_pubsub_subscribed")
                backoff = 1.0
                async for message in pubsub.listen():
                    if message.get("type") == "message":
                        self.invalidate_cache()
            except asyncio.CancelledError:
                logger.info("llm_config_pubsub_cancelled")
                return
            except Exception as exc:  # noqa: BLE001 — best-effort retry
                logger.warning(
                    "llm_config_pubsub_error_retrying",
                    error=str(exc),
                    backoff_seconds=backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)


# ──────────────────────────────────────────────────────────────────
# Singleton accessor (D-1: Settings.get_model needs lazy lookup)
# ──────────────────────────────────────────────────────────────────

_singleton: LLMConfigService | None = None


def init_llm_config_service(
    session_factory: Callable[[], AsyncSession] | None = None,
    redis_client: Redis | None = None,
) -> LLMConfigService:
    """Initialize module singleton. Called from FastAPI lifespan."""
    global _singleton  # noqa: PLW0603 — module singleton DI
    _singleton = LLMConfigService(session_factory=session_factory, redis_client=redis_client)
    return _singleton


def get_llm_config_service() -> LLMConfigService | None:
    """Module singleton accessor. Returns None pre-init (boot ordering)."""
    return _singleton


def reset_llm_config_service() -> None:
    """Test helper. Resets module singleton."""
    global _singleton  # noqa: PLW0603
    _singleton = None


# ──────────────────────────────────────────────────────────────────
# Env fallback (preserved from pre-S4 Settings.get_model logic)
# ──────────────────────────────────────────────────────────────────


def _get_model_from_env(role: ModelRole) -> str:
    """Pre-PR-1 logic preserved verbatim — env-only resolution."""
    env_map: dict[ModelRole, str] = {
        ModelRole.NANO: settings.AI_MODEL_NANO,
        ModelRole.REASONING: settings.AI_MODEL_REASONING,
        ModelRole.FAST: settings.AI_MODEL_FAST,
        ModelRole.VISION: settings.AI_MODEL_VISION,
        ModelRole.AGENT: settings.AI_MODEL_AGENT,
        ModelRole.EMBEDDING: settings.AI_MODEL_EMBEDDING,
    }
    return env_map[role]


__all__ = [
    "CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL",
    "DEFAULT_TTL_SECONDS",
    "LLMConfigService",
    "get_llm_config_service",
    "init_llm_config_service",
    "reset_llm_config_service",
]


# Mypy / annotation ergonomics — referenced by ResolvedModel imports above.
_ = AIProvider
_ = Any
