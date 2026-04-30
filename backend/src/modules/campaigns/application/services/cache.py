"""CacheBackend protocol + concrete TTLCache implementation with Redis pub/sub invalidation.

Mirrors PlanService cache pattern (PR-2 cementado).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Protocol

import structlog

logger = structlog.get_logger(__name__)


class CacheBackend(Protocol):
    """Abstraction over in-memory TTL + Redis pub/sub invalidation.

    Concrete impl mirrors PlanService.subscribe_cache_invalidations (PR-2).
    - cachetools.TTLCache for hot reads (per-pod)
    - Redis pubsub channel "cache_invalidate:campaigns:{key}" for cross-instance
    """

    async def get(self, key: str) -> Any | None:
        """Return cached value or None if missing/expired."""
        ...

    async def set(self, key: str, value: Any, *, ttl: int) -> None:
        """Store value with TTL in seconds."""
        ...

    async def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        ...

    async def invalidate_pattern(self, pattern: str) -> None:
        """Remove all keys matching pattern (prefix-style)."""
        ...

    async def subscribe_invalidations(self) -> None:
        """Long-running task. Started at app boot via lifespan."""
        ...


class SimpleTTLCache:
    """Simple in-process TTL cache. Thread-safe enough for asyncio single-thread.

    Concrete implementation for CampaignService/SegmentService/TemplateService.
    Mirrors PlanService pattern (PR-2) with Redis pub/sub invalidation support.
    """

    PUBSUB_CHANNEL_PREFIX = "cache_invalidate:campaigns"

    def __init__(
        self,
        max_entries: int = 4096,
        redis_client: Any | None = None,
    ) -> None:
        """Initialize with optional Redis client for cross-instance invalidation."""
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)
        self._max_entries = max_entries
        self._redis = redis_client
        self._subscriber_task: asyncio.Task[None] | None = None

    async def get(self, key: str) -> Any | None:
        """Return cached value or None if missing/expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, *, ttl: int) -> None:
        """Store value with TTL in seconds. Evicts oldest if over max_entries."""
        if len(self._store) >= self._max_entries:
            # Evict the expired entry or oldest (simple LRU-like eviction)
            now = time.monotonic()
            expired_keys = [k for k, (_, exp) in self._store.items() if exp < now]
            if expired_keys:
                for k in expired_keys:
                    del self._store[k]
            elif self._store:
                # Remove arbitrary entry to stay under cap
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
        self._store[key] = (value, time.monotonic() + ttl)

    async def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        self._store.pop(key, None)
        if self._redis is not None:
            try:
                channel = f"{self.PUBSUB_CHANNEL_PREFIX}:{key}"
                await self._redis.publish(channel, "invalidate")
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "campaigns_cache_redis_publish_failed",
                    key=key,
                    error=str(exc),
                )

    async def invalidate_pattern(self, pattern: str) -> None:
        """Remove all keys whose name starts with pattern prefix."""
        # Pattern is like "campaigns:list:{tenant_id}:*" -> prefix is "campaigns:list:{tenant_id}:"
        prefix = pattern.rstrip("*")
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._store[k]
        if self._redis is not None:
            try:
                channel = f"{self.PUBSUB_CHANNEL_PREFIX}:pattern:{prefix}"
                await self._redis.publish(channel, "invalidate_pattern")
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "campaigns_cache_redis_publish_pattern_failed",
                    pattern=pattern,
                    error=str(exc),
                )

    async def subscribe_invalidations(self) -> None:
        """Long-running task for cross-instance cache invalidation via Redis pub/sub.

        Soft-fail: if Redis unavailable, logs warning and returns without raising.
        App continues with TTL-only cache (acceptable degradation per graceful-degradation rules).
        """
        if self._redis is None:
            logger.info("campaigns_cache_redis_not_configured_skip_subscriber")
            return
        try:
            pubsub = self._redis.pubsub()
            pattern = f"{self.PUBSUB_CHANNEL_PREFIX}:*"
            await pubsub.psubscribe(pattern)
            logger.info("campaigns_cache_subscribed_invalidations", pattern=pattern)
            async for message in pubsub.listen():
                if message["type"] not in ("pmessage", "message"):
                    continue
                channel: str = message.get("channel", b"").decode()
                if ":pattern:" in channel:
                    prefix = channel.split(":pattern:", 1)[1]
                    keys_to_delete = [k for k in self._store if k.startswith(prefix)]
                    for k in keys_to_delete:
                        del self._store[k]
                else:
                    key = channel.removeprefix(f"{self.PUBSUB_CHANNEL_PREFIX}:")
                    self._store.pop(key, None)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "campaigns_cache_redis_subscriber_error",
                error=str(exc),
                hint="Falling back to TTL-only cache — acceptable degradation",
            )
