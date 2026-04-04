"""Redis cache layer for dashboard metrics.

MetricsCache is a thin wrapper around Redis that:
- Caches dashboard query results with a 5-minute TTL
- Silently falls back to None when Redis is unavailable
- Never raises exceptions — Redis is purely an optimization

Key format: metrics:{tenant_id}:{stage}:{period}
"""

import json
import logging
from typing import Dict, Optional

from src.modules.analytics.application.config import CacheConfig

logger = logging.getLogger(__name__)

# Per-stage TTL overrides derived from centralized CacheConfig.
# Paid ad data changes less frequently (extracted nightly).
# CRM/general dashboard queries use shorter TTL for fresher data.
STAGE_TTL: Dict[str, int] = {
    "attraction": CacheConfig.ATTRACTION_TTL,
    "capture": CacheConfig.DETAIL_STAGE_TTL,
    "nurture": CacheConfig.DETAIL_STAGE_TTL,
    "opportunity": CacheConfig.DETAIL_STAGE_TTL,
    "sales": CacheConfig.DETAIL_STAGE_TTL,
    "adoption": CacheConfig.DETAIL_STAGE_TTL,
    "expansion": CacheConfig.DETAIL_STAGE_TTL,
    "evangelization": CacheConfig.DETAIL_STAGE_TTL,
    "summary": CacheConfig.SUMMARY_TTL,
}
DEFAULT_TTL = CacheConfig.DEFAULT_TTL


class MetricsCache:
    """Redis-backed cache for dashboard metrics with silent fallback."""

    def __init__(self, redis_client):
        """Initialize with a redis client instance.

        Args:
            redis_client: A Redis client (from redis-py or compatible).
        """
        self._redis = redis_client

    def _key(self, tenant_id: str, stage: str, period: str) -> str:
        """Build the cache key."""
        return f"metrics:{tenant_id}:{stage}:{period}"

    async def get(
        self, tenant_id: str, stage: str, period: str
    ) -> Optional[dict]:
        """Retrieve cached metrics data.

        Returns:
            Parsed dict on cache hit, None on miss or Redis error.
        """
        try:
            key = self._key(tenant_id, stage, period)
            raw = self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.debug(
                "Redis cache get failed for tenant=%s stage=%s period=%s",
                tenant_id, stage, period,
                exc_info=True,
            )
            return None

    async def set(
        self, tenant_id: str, stage: str, period: str, data: dict
    ) -> None:
        """Store metrics data in cache with TTL.

        Silently ignores errors — cache is an optimization only.
        """
        try:
            key = self._key(tenant_id, stage, period)
            ttl = STAGE_TTL.get(stage, DEFAULT_TTL)
            self._redis.setex(key, ttl, json.dumps(data))
        except Exception:
            logger.debug(
                "Redis cache set failed for tenant=%s stage=%s period=%s",
                tenant_id, stage, period,
                exc_info=True,
            )

    async def invalidate_tenant(self, tenant_id: str) -> None:
        """Delete all cached metrics for a tenant.

        Called after successful ETL extraction to ensure fresh data.
        """
        try:
            pattern = f"metrics:{tenant_id}:*"
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
        except Exception:
            logger.debug(
                "Redis cache invalidation failed for tenant=%s",
                tenant_id,
                exc_info=True,
            )
