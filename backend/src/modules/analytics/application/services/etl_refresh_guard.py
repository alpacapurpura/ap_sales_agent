"""EtlRefreshGuard — per-tenant per-channel ETL refresh sliding window guard.

Duplicates the Redis sliding-window mechanics from OutboundRateLimiter
(src.shared.billing.application.rate_limiter) with a 1-hour window
keyed by (tenant_id, channel_slug) instead of 24h outbound messages.

Bounded scope per 03-arch.md § 1: standalone parallel implementation, NOT
a wrapper or composition. Distinct key schema, window, limit, confirmation
threshold, collaborators (`channel_config_repo` vs `PlanService`), and
return shape (`GuardDecision` vs `bool`). Anti-duplication compliance: 1
consumer for 1 use case — no shared lift required today. If a 3rd
sliding-window consumer materialises (Story 3+), promote both
implementations to a shared `BaseSlidingWindowGuard` in shared/billing/.

Per tessl__graceful-degradation: Redis unavailable → fail-open (log warning).

Story 2B T-1 — growth-studio-actions-schemas-real
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class GuardDecision:
    """Immutable result of EtlRefreshGuard.check().

    Fields:
        allowed: Whether the refresh is permitted.
        current_count: Number of refreshes in the current window.
        limit: Per-tenant per-channel limit for this window.
        retry_after_seconds: Seconds until next refresh allowed (if blocked).
        requires_confirmation: True if user must explicitly confirm another refresh.
        soft_fail: True if guard decision was made due to Redis unavailability.
    """

    allowed: bool
    current_count: int
    limit: int
    retry_after_seconds: int | None = None
    requires_confirmation: bool = False
    soft_fail: bool = False


class EtlRefreshGuard:
    """Per-tenant per-channel ETL refresh sliding window guard.

    Invariants:
    - Limit: DEFAULT_LIMIT refreshes / WINDOW_SECONDS window per tenant per channel.
    - Custom limit: from channel_config_repo.get_limit() if configured.
    - Confirmation: when current_count > CONFIRM_THRESHOLD (already refreshed once
      this hour), requires_confirmation=True returned (per spec Q4).
    - Soft-fail: Redis unavailable → fail-open (log warning, allow) per
      tessl__graceful-degradation Iron Rule.
    - Key schema: etl_refresh:{tenant_id}:{channel_slug} (distinct from
      OutboundRateLimiter's rate_limit:outbound:{tenant_id}).
    """

    KEY_TEMPLATE = "etl_refresh:{tenant_id}:{channel}"
    WINDOW_SECONDS = 3600  # 1 hour
    DEFAULT_LIMIT = 3
    CONFIRM_THRESHOLD = 1  # > 1 refresh in window → require confirmation

    def __init__(self, redis_client: object, channel_config_repo: object) -> None:
        """Bind guard to Redis client and channel config repository.

        Args:
            redis_client: Async Redis client (aioredis compatible).
            channel_config_repo: Repository with get_limit(tenant_id, channel_slug)
                → int | None. Returns None if no override configured.
        """
        self._redis = redis_client
        self._config = channel_config_repo

    async def check(
        self,
        tenant_id: UUID,
        channel_slug: str,
        *,
        confirmed: bool,
    ) -> GuardDecision:
        """Check if ETL refresh is allowed for this tenant+channel.

        Algorithm (Redis sorted set sliding window):
        1. Get per-tenant limit from config repo (fallback: DEFAULT_LIMIT).
        2. ZREMRANGEBYSCORE: purge entries older than WINDOW_SECONDS.
        3. ZCARD: count current entries in window.
        4. If count >= limit → blocked (rate limit exceeded).
        5. If count > CONFIRM_THRESHOLD and not confirmed → requires_confirmation.
        6. Otherwise: ZADD new entry + EXPIRE key → allowed.

        Soft-fail: any Redis exception → fail-open (allowed=True, soft_fail=True).

        Args:
            tenant_id: Tenant UUID (from context, never from caller payload).
            channel_slug: Canonical channel slug (e.g. 'meta-ads').
            confirmed: Whether user explicitly confirmed a subsequent refresh.

        Returns:
            GuardDecision describing the outcome.
        """
        limit = (await self._config.get_limit(tenant_id, channel_slug)) or self.DEFAULT_LIMIT
        key = self.KEY_TEMPLATE.format(tenant_id=str(tenant_id), channel=channel_slug)
        now = time.time()
        cutoff = now - self.WINDOW_SECONDS

        try:
            pipeline = self._redis.pipeline()
            pipeline.zremrangebyscore(key, 0, cutoff)
            pipeline.zcard(key)
            results = await pipeline.execute()
            current_count: int = results[1]

            if current_count >= limit:
                # Rate limit exceeded — compute retry_after from oldest entry
                oldest = await self._redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_score = oldest[0][1]
                    retry_after = int(self.WINDOW_SECONDS - (now - oldest_score))
                else:
                    retry_after = self.WINDOW_SECONDS
                return GuardDecision(
                    allowed=False,
                    current_count=current_count,
                    limit=limit,
                    retry_after_seconds=max(retry_after, 0),
                )

            if current_count > self.CONFIRM_THRESHOLD and not confirmed:
                return GuardDecision(
                    allowed=False,
                    requires_confirmation=True,
                    current_count=current_count,
                    limit=limit,
                )

            # Accept + record new entry
            member = str(uuid.uuid4())
            add_pipeline = self._redis.pipeline()
            add_pipeline.zadd(key, {member: now})
            add_pipeline.expire(key, self.WINDOW_SECONDS)
            await add_pipeline.execute()

            return GuardDecision(
                allowed=True,
                current_count=current_count + 1,
                limit=limit,
            )

        except Exception as exc:  # noqa: BLE001 — fail-open per tessl__graceful-degradation
            logger.warning(
                "etl_refresh_guard_redis_unavailable_fail_open",
                tenant_id=str(tenant_id),
                channel=channel_slug,
                error=str(exc),
            )
            return GuardDecision(
                allowed=True,
                current_count=0,
                limit=limit,
                soft_fail=True,
            )
