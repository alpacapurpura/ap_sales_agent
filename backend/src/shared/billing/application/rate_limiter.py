"""OutboundRateLimiter — Redis sliding window antispam gate.

Soft-fail: Redis unavailable → fail-open (per tessl__graceful-degradation).
Budget cap still gates LLM cost; rate limiter is complementary antispam.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import time
import uuid as uuid_mod
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from src.shared.billing.application.plan_service import PlanService

logger = structlog.get_logger(__name__)


class OutboundRateLimiter:
    """Sliding window Redis antispam. Complementary to BudgetGuard.

    Uses Redis sorted set (ZADD/ZREMRANGEBYSCORE/ZCARD) for atomic sliding window.
    Key per tenant: `rate_limit:outbound:{tenant_id}`.
    Window: 24h (configurable via DEFAULT_WINDOW_SECONDS).

    Graceful degradation:
    - Redis unavailable → fail-open (log warning, return True).
    - None cap → unlimited (subject to budget only).
    """

    KEY_TEMPLATE = "rate_limit:outbound:{tenant_id}"
    DEFAULT_WINDOW_SECONDS = 86400  # 24h

    def __init__(self, redis_client: object, plan_service: PlanService) -> None:
        """Bind rate limiter to Redis client and plan service."""
        self._redis = redis_client
        self._plan_service = plan_service

    async def check(self, tenant_id: UUID) -> bool:
        """Return True if outbound message is allowed. Increments counter on True.

        If max_outbound_msg_per_day IS NULL → unlimited (return True without Redis).
        Soft-fail: Redis unavailable → fail-open (return True, log warning).
        """
        try:
            plan = await self._plan_service.get_effective(tenant_id)
        except Exception as exc:  # noqa: BLE001 — plan resolution failure
            logger.warning(
                "rate_limiter_plan_resolution_failed",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            return True

        if plan.max_outbound_msg_per_day is None:
            # Unlimited subject to budget
            return True

        limit = plan.max_outbound_msg_per_day
        key = self.KEY_TEMPLATE.format(tenant_id=str(tenant_id))
        now = time.time()
        cutoff = now - self.DEFAULT_WINDOW_SECONDS

        try:
            pipeline = self._redis.pipeline()
            # Purge entries outside window
            pipeline.zremrangebyscore(key, 0, cutoff)
            # Count current window
            pipeline.zcard(key)
            results = await pipeline.execute()
            current_count = results[1]

            if current_count >= limit:
                logger.info(
                    "rate_limiter_outbound_blocked",
                    tenant_id=str(tenant_id),
                    current_count=current_count,
                    limit=limit,
                )
                return False

            # Add new entry (unique member = uuid for idempotency)
            member = str(uuid_mod.uuid4())
            add_pipeline = self._redis.pipeline()
            add_pipeline.zadd(key, {member: now})
            add_pipeline.expire(key, self.DEFAULT_WINDOW_SECONDS)
            await add_pipeline.execute()
            return True

        except Exception as exc:  # noqa: BLE001 — graceful degradation: fail-open
            logger.warning(
                "rate_limiter_redis_unavailable_fail_open",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            return True
