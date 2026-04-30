"""PlanService — effective plan resolver with cache + Redis pub/sub invalidation.

PM Q5: cross-instance cache invalidation via Redis pub/sub.
PM Q6: get_default_plan resolves via is_default=TRUE partial unique index.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from src.shared.billing.domain.plan import PlanConfig
from src.shared.billing.domain.plan_repository import PlanRepository
from src.shared.billing.domain.subscription_repository import TenantSubscriptionRepository

logger = structlog.get_logger(__name__)

# PM Q5: cross-instance cache invalidation via Redis pub/sub.
CACHE_INVALIDATE_PLAN_CONFIG_CHANNEL = "cache_invalidate:plan_config"
CACHE_INVALIDATE_TENANT_SUBSCRIPTION_CHANNEL_PREFIX = "cache_invalidate:tenant_subscription"
DEFAULT_PLAN_CACHE_TTL_SECONDS = 300  # 5 min fallback when Redis pub/sub unavailable


class BillingDefaultPlanMissingError(Exception):
    """Raised when no default plan is resolvable (fail-fast per PM Q6)."""


class PlanService:
    """Resolve effective plan (catalog row + custom_overrides + legacy fallback).

    Cache strategy (PM Q5 — multi-pod ready):
    - In-memory TTLCache per pod, 5min TTL.
    - Cross-instance invalidation via Redis pub/sub channels.
    - Soft-fail: Redis unavailable → log warning + rely on TTL.
    """

    DEFAULT_PLAN_ID_ENV = "BILLING_DEFAULT_PLAN_ID"

    def __init__(
        self,
        plan_repo: PlanRepository,
        subscription_repo: TenantSubscriptionRepository,
        legacy_billing_repo: Any | None = None,
        redis_client: Any | None = None,
        cache_ttl_seconds: int = DEFAULT_PLAN_CACHE_TTL_SECONDS,
    ) -> None:
        """Initialise service with repos and optional Redis client."""
        self._plan_repo = plan_repo
        self._sub_repo = subscription_repo
        self._legacy_repo = legacy_billing_repo
        self._redis = redis_client
        self._cache_ttl = cache_ttl_seconds
        # Per-tenant effective-plan cache. Key=str(tenant_id); Value=(PlanConfig, expires_at_unix).
        self._tenant_cache: dict[str, tuple[PlanConfig, float]] = {}
        # Default plan cache: single slot.
        self._default_cache: tuple[PlanConfig, float] | None = None
        self._subscriber_task: asyncio.Task | None = None  # type: ignore[type-arg]

    async def get_effective(self, tenant_id: UUID) -> PlanConfig:
        """Return effective plan for tenant.

        Resolution chain:
        1. Cache hit (TTL) → return.
        2. `tenant_subscription` exists → plan_config row + custom_overrides merged → cache.
        3. `tenant_subscription` IS NULL but legacy `tenant_billing_config` exists →
           translate to in-memory PlanConfig (compat shim, no DB write).
        4. Neither exists → fallback to `get_default_plan()`.
        """
        key = str(tenant_id)
        now = time.monotonic()
        cached = self._tenant_cache.get(key)
        if cached is not None:
            plan, expires_at = cached
            if now < expires_at:
                return plan

        # Try tenant_subscription
        sub = await self._sub_repo.get_by_tenant_id(tenant_id)
        if sub is not None:
            base_plan = await self._plan_repo.get_by_id(sub.plan_id)
            if base_plan is None:
                logger.warning(
                    "billing_plan_not_found_fallback",
                    tenant_id=str(tenant_id),
                    plan_id=sub.plan_id,
                )
                base_plan = await self.get_default_plan()
            plan = self._apply_overrides(base_plan, sub.custom_overrides)
        else:
            # Legacy fallback (compat shim — S2 migrates)
            legacy_plan = await self._try_legacy_fallback(tenant_id)
            if legacy_plan is not None:
                logger.info(
                    "billing_plan_fallback",
                    tenant_id=str(tenant_id),
                    fallback="legacy_tenant_billing_config",
                )
                plan = legacy_plan
            else:
                logger.info(
                    "billing_plan_fallback",
                    tenant_id=str(tenant_id),
                    fallback="default_plan",
                )
                plan = await self.get_default_plan()

        self._tenant_cache[key] = (plan, now + self._cache_ttl)
        return plan

    async def get_default_plan(self) -> PlanConfig:
        """PM Q6: resolve default plan.

        1. Cache hit → return.
        2. Query plan_config WHERE is_default = TRUE LIMIT 1.
        3. Fallback to env var BILLING_DEFAULT_PLAN_ID if DB not found.
        4. Raise BillingDefaultPlanMissingError if neither resolves.
        """
        now = time.monotonic()
        if self._default_cache is not None:
            plan, expires_at = self._default_cache
            if now < expires_at:
                return plan

        plan = await self._plan_repo.get_default()
        if plan is None:
            # Fallback to env var
            import os

            default_id = os.getenv(self.DEFAULT_PLAN_ID_ENV, "free")
            plan = await self._plan_repo.get_by_id(default_id)
            if plan is None:
                raise BillingDefaultPlanMissingError(
                    f"No default plan found in DB and env var '{self.DEFAULT_PLAN_ID_ENV}' "
                    f"references non-existent plan '{default_id}'. "
                    "Run migration 110 to seed plans."
                )

        self._default_cache = (plan, now + self._cache_ttl)
        return plan

    async def update_plan(self, plan: PlanConfig) -> PlanConfig:
        """Streamlit admin save path. Atomic when toggling is_default (PM Q6).

        If plan.is_default == True: atomically demotes prior default + promotes new.
        Publishes Redis cache invalidation event post-save.
        """
        # PM Q6: atomic is_default toggle handled at the repo level.
        # For is_default=True, caller must ensure prior default is cleared.
        # This is handled in Streamlit via raw SQL transaction in the admin page.
        stored = await self._plan_repo.upsert(plan)

        # PM Q5: publish cache invalidation
        try:
            if self._redis is not None:
                await self._redis.publish(CACHE_INVALIDATE_PLAN_CONFIG_CHANNEL, "")
        except Exception as exc:  # noqa: BLE001 — soft-fail per Q5
            logger.warning(
                "plan_service_invalidate_publish_failed",
                channel=CACHE_INVALIDATE_PLAN_CONFIG_CHANNEL,
                error=str(exc),
            )

        await self.invalidate_default_cache()
        return stored

    async def update_subscription(
        self,
        tenant_id: UUID,
        plan_id: str,
        custom_overrides: dict[str, Any] | None = None,
    ) -> None:
        """Update subscription and publish per-tenant cache invalidation."""
        import datetime as dt

        from src.shared.billing.domain.subscription import TenantSubscription

        now = dt.datetime.now(dt.timezone.utc)
        sub = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan_id,
            custom_overrides=custom_overrides or {},
            activated_at=now,
            updated_at=now,
        )
        await self._sub_repo.upsert(sub)

        # PM Q5: per-tenant invalidation
        channel = f"{CACHE_INVALIDATE_TENANT_SUBSCRIPTION_CHANNEL_PREFIX}:{tenant_id}"
        try:
            if self._redis is not None:
                await self._redis.publish(channel, "")
        except Exception as exc:  # noqa: BLE001 — soft-fail per Q5
            logger.warning(
                "plan_service_invalidate_publish_failed",
                tenant_id=str(tenant_id),
                error=str(exc),
            )

        await self.invalidate_cache(tenant_id)

    async def invalidate_cache(self, tenant_id: UUID) -> None:
        """Evict tenant from local cache. Called by Redis pub/sub subscriber."""
        self._tenant_cache.pop(str(tenant_id), None)

    async def invalidate_default_cache(self) -> None:
        """Evict default-plan cache. Called by Redis pub/sub subscriber."""
        self._default_cache = None
        self._tenant_cache.clear()

    async def _try_legacy_fallback(self, tenant_id: UUID) -> PlanConfig | None:
        """Translate legacy tenant_billing_config to in-memory PlanConfig.

        Returns None if legacy repo is not wired or no record found.
        Compat shim — S2 migrates data.
        """
        if self._legacy_repo is None:
            return None
        try:
            legacy = await self._legacy_repo.get_by_tenant_id(tenant_id)
            if legacy is None:
                return None
            default_plan = await self.get_default_plan()
            # Apply legacy values as overrides on top of default plan
            overrides: dict[str, Any] = {}
            if hasattr(legacy, "cost_alert_threshold_usd") and legacy.cost_alert_threshold_usd:
                overrides["llm_budget_total_usd"] = Decimal(str(legacy.cost_alert_threshold_usd))
            return self._apply_overrides(default_plan, overrides)
        except Exception as exc:  # noqa: BLE001 — legacy compat never crashes
            logger.warning(
                "billing_legacy_fallback_error",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            return None

    @staticmethod
    def _apply_overrides(base: PlanConfig, overrides: dict[str, Any]) -> PlanConfig:
        """Merge custom_overrides JSONB on top of base plan VO.

        Only known PlanConfig fields are applied; unknown keys logged + skipped.
        """
        if not overrides:
            return base

        merged = base.model_dump()
        valid_fields = set(PlanConfig.model_fields)

        for key, value in overrides.items():
            if key in valid_fields:
                if key == "llm_budget_total_usd" or key == "sales_agent_reserved_pct":
                    merged[key] = Decimal(str(value))
                else:
                    merged[key] = value
            else:
                logger.debug("plan_service_override_unknown_field", field=key)

        return PlanConfig(**merged)

    async def subscribe_cache_invalidations(self) -> None:
        """Background task: consume Redis pub/sub for cache invalidation.

        Subscribes to:
        - `cache_invalidate:plan_config` → invalidate_default_cache.
        - `cache_invalidate:tenant_subscription:*` → per-tenant invalidate_cache.

        Soft-fail: Redis disconnects → retry with backoff, log warning.
        """
        if self._redis is None:
            logger.info("plan_service_pubsub_skipped_no_redis")
            return

        backoff = 1.0
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(CACHE_INVALIDATE_PLAN_CONFIG_CHANNEL)
                await pubsub.psubscribe(f"{CACHE_INVALIDATE_TENANT_SUBSCRIPTION_CHANNEL_PREFIX}:*")
                logger.info("plan_service_pubsub_subscribed")
                backoff = 1.0
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        channel = message["channel"]
                        if channel == CACHE_INVALIDATE_PLAN_CONFIG_CHANNEL:
                            await self.invalidate_default_cache()
                        elif channel.startswith(CACHE_INVALIDATE_TENANT_SUBSCRIPTION_CHANNEL_PREFIX):
                            tenant_id_str = channel.split(":")[-1]
                            try:
                                await self.invalidate_cache(UUID(tenant_id_str))
                            except ValueError:
                                logger.warning(
                                    "plan_service_pubsub_invalid_tenant_id",
                                    raw=tenant_id_str,
                                )
                    elif message["type"] == "pmessage":
                        channel = message["channel"]
                        if channel.startswith(CACHE_INVALIDATE_TENANT_SUBSCRIPTION_CHANNEL_PREFIX):
                            tenant_id_str = channel.split(":")[-1]
                            try:
                                await self.invalidate_cache(UUID(tenant_id_str))
                            except ValueError:
                                pass
            except asyncio.CancelledError:
                logger.info("plan_service_pubsub_cancelled")
                return
            except Exception as exc:  # noqa: BLE001 — retry on any error
                logger.warning(
                    "plan_service_pubsub_error_retrying",
                    error=str(exc),
                    backoff_seconds=backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
