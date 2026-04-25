"""Redis cache wrapper for ``ask_tenant_data`` (F5).

60-second TTL keyed on ``(tenant_id, question, output_channel)``. Designed to
fail open: any Redis exception swallowed and the pipeline runs without cache.
Also accepts ``redis=None`` so tests / dev environments without Redis stay
fully functional.

Cache invalidation strategy: TTL only — no proactive bust on mutation. F5 plan
§5.4 picks 60s deliberately because the data this caches (offer search, lead
counts, conversation counts) does not need real-time freshness for natural-
language Q&A. If a mutation tool changes data and the user asks again within
60s, they may see the previous answer; the synthesizer adds no "as of" stamp,
so this is invisible. Granular invalidation can land in F8 routing/cost optim
once cache hit-rate is measured.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()

DEFAULT_TTL_SECONDS = 60


def make_cache_key(tenant_id: UUID, question: str, output_channel: str) -> str:
    """Build a stable Redis key for the (tenant, question, channel) triple.

    The question is hashed (md5, 16 hex chars) so the key length stays
    bounded and unicode/emoji content is normalised away. md5 is fine here
    because the key is non-secret and only needs collision-resistance at the
    per-tenant level (15 bits more than enough).
    """
    digest = hashlib.md5(
        f"{question}|{output_channel}".encode(),
    ).hexdigest()[:16]
    return f"copilot:ask:{tenant_id}:{digest}"


class DataQueryCache:
    """Thin wrapper around redis.Redis with safe fallbacks.

    ``redis`` may be ``None`` to disable caching entirely. Any runtime error
    from the underlying client is swallowed and logged at WARN level so the
    pipeline keeps working.
    """

    def __init__(self, redis: Any | None = None) -> None:  # noqa: ANN401 — opaque redis client
        """Pass ``None`` to disable caching; otherwise pass any redis-py-compatible client."""
        self._redis = redis

    @property
    def enabled(self) -> bool:
        """``True`` when a redis client is wired (cache is active)."""
        return self._redis is not None

    def get(self, key: str) -> str | None:
        """Return the cached value or ``None`` on miss / Redis failure."""
        if self._redis is None:
            return None
        try:
            raw = self._redis.get(key)
        except Exception:  # noqa: BLE001 — redis failures must fail open
            logger.warning("data_query_cache_get_failed", key=key)
            return None
        if raw is None:
            return None
        if isinstance(raw, bytes):
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return None
        return str(raw)

    def set(
        self,
        key: str,
        value: str,
        *,
        ttl: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Store ``value`` under ``key`` with the given TTL; no-op on Redis failure."""
        if self._redis is None:
            return
        try:
            self._redis.setex(key, ttl, value)
        except Exception:  # noqa: BLE001 — redis failures must fail open
            logger.warning("data_query_cache_set_failed", key=key)


__all__ = ("DEFAULT_TTL_SECONDS", "DataQueryCache", "make_cache_key")
