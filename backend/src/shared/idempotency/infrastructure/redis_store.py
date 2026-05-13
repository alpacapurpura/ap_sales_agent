"""Redis-backed IdempotencyStore with soft-fail when Redis unavailable.

Decision D9 (architect): Redis unavailable → log warning + allow execution.
Better to double-process than to lose the operation entirely.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from luana_core_idempotency.domain.key import IdempotencyKey

logger = structlog.get_logger(__name__)


class IdempotencyStore(ABC):
    """Abstract idempotency store interface."""

    @abstractmethod
    async def claim(self, key: IdempotencyKey) -> bool:
        """Atomic SETNX with TTL.

        Returns:
            True if claim succeeded (first call — execute the function).
            False if key already exists (duplicate call — use cached result).
        """

    @abstractmethod
    async def cached_result(self, key: IdempotencyKey) -> dict[str, Any] | None:
        """Return cached result if previously stored, None otherwise."""

    @abstractmethod
    async def store_result(
        self,
        key: IdempotencyKey,
        result: dict[str, Any],
    ) -> None:
        """Persist minimal result subset (id + status) for duplicate handling."""


class RedisIdempotencyStore(IdempotencyStore):
    """Redis-backed idempotency store.

    Uses SET NX EX for atomic claim.
    Soft-fail when Redis is unavailable (log + allow execution).
    Cached result uses a sub-key: ``{storage_key}:result``.
    """

    def __init__(self, redis_client: Any) -> None:  # noqa: ANN401
        """Initialize with a Redis client (or None for soft-fail mode)."""
        self._redis = redis_client

    async def claim(self, key: IdempotencyKey) -> bool:
        """Atomic SETNX + EX. Returns True if new (first call)."""
        if self._redis is None:
            logger.warning(
                "idempotency_redis_unavailable_softfail",
                namespace=key.namespace,
                storage_key=key.storage_key,
            )
            return True  # Soft-fail: allow execution
        try:
            result = self._redis.set(
                key.storage_key,
                "1",
                nx=True,
                ex=key.ttl_seconds,
            )
            return bool(result)
        except Exception:  # noqa: BLE001 — soft-fail, allow execution on Redis error
            logger.warning(
                "idempotency_redis_claim_error",
                namespace=key.namespace,
                exc_info=True,
            )
            return True  # Soft-fail on Redis error

    async def cached_result(self, key: IdempotencyKey) -> dict[str, Any] | None:
        """Return cached result dict or None if missing/expired."""
        if self._redis is None:
            return None
        try:
            raw = self._redis.get(f"{key.storage_key}:result")
            if not raw:
                return None
            return json.loads(raw)  # type: ignore[no-any-return]
        except (ValueError, TypeError):  # json decode errors
            return None
        except Exception:  # noqa: BLE001 — soft-fail on Redis errors
            return None

    async def store_result(
        self,
        key: IdempotencyKey,
        result: dict[str, Any],
    ) -> None:
        """Persist minimal result. Soft-fail on error."""
        if self._redis is None:
            return
        try:
            self._redis.setex(
                f"{key.storage_key}:result",
                key.ttl_seconds,
                json.dumps(result),
            )
        except Exception:  # noqa: BLE001 — soft-fail, store_result is best-effort
            logger.warning(
                "idempotency_redis_store_result_error",
                namespace=key.namespace,
                exc_info=True,
            )
