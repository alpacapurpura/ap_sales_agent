"""IdempotencyService — imperative API for sites that cannot use the decorator.

Use this when DI/composition is preferred over function decoration,
e.g. tool dispatch, service layer methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from src.shared.idempotency.domain.key import IdempotencyKey
    from src.shared.idempotency.infrastructure.redis_store import IdempotencyStore

logger = structlog.get_logger(__name__)


class IdempotencyService:
    """Imperative idempotency check-and-execute service.

    Equivalent to the ``@idempotent`` decorator but composable via DI.
    """

    def __init__(self, store: IdempotencyStore) -> None:
        """Initialize with an IdempotencyStore backend."""
        self._store = store

    async def with_dedupe(
        self,
        key: IdempotencyKey,
        func: Callable[[], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Check idempotency key, execute func if first call, return cached on repeat.

        Args:
            key: IdempotencyKey for the operation.
            func: Zero-arg async callable returning a dict result.

        Returns:
            dict result from func or cached result from previous invocation.
        """
        claimed = await self._store.claim(key)

        if not claimed:
            cached = await self._store.cached_result(key)
            if cached is not None:
                logger.info(
                    "idempotency_cache_hit",
                    namespace=key.namespace,
                    key=key.key,
                )
                return cached
            # Claim conflict but no cache → TTL race, execute
            logger.warning(
                "idempotency_claim_lost_no_cache",
                namespace=key.namespace,
                key=key.key,
            )

        result = await func()

        # Store minimal projection
        if isinstance(result, dict):
            projected = {k: result[k] for k in ("id", "status", "external_id") if k in result}
            if projected:
                await self._store.store_result(key, projected)

        return result
