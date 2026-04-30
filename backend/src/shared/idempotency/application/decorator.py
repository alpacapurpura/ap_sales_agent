"""@idempotent decorator — function-level Redis-backed deduplication.

Usage:
    @idempotent(
        namespace="webhook:manychat",
        key_fn=lambda req: req.headers.get("X-Signature", ""),
        ttl=86400,
    )
    async def manychat_webhook(req: Request) -> dict: ...

    @idempotent(
        namespace="copilot:extract_card",
        key_fn=lambda *, job_id, section_slug, **_: f"nav:{job_id}:{section_slug}",
        ttl=86400,
    )
    async def emit_section_complete_pill(*, job_id: str, ...) -> None: ...

Behavior (D11 architect — projected result, no full payload):
- First call: claim → execute → store {id, status, external_id} → return result.
- Repeat call: claim fails → return cached_result if available.
- Cache miss (TTL race): log warning + execute again (double-process acceptable).
- Redis down: log warning + execute (soft-fail per tessl__graceful-degradation).
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

import structlog

from src.shared.idempotency.domain.key import IdempotencyKey

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from src.shared.idempotency.infrastructure.redis_store import IdempotencyStore

P = ParamSpec("P")
R = TypeVar("R")
logger = structlog.get_logger(__name__)


def idempotent(
    *,
    namespace: str,
    key_fn: Callable[..., str],
    ttl: int = 86400,
    store_factory: Callable[[], IdempotencyStore] | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator for idempotent async functions.

    Args:
        namespace: Key namespace for Redis. Examples: ``"webhook:manychat"``,
            ``"copilot:extract_card"``.
        key_fn: Callable receiving the same args as the decorated function.
            Returns the natural key string (e.g., signature, job_id+slug).
        ttl: TTL in seconds for the idempotency lock. Default 86400 (24h).
        store_factory: Optional factory for the IdempotencyStore (for testing).
            Defaults to a factory using the global Redis client.

    Returns:
        Decorator that wraps the async function with idempotency protection.
    """

    def deco(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        """Apply the decorator to the function."""

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            store = (store_factory or _default_store_factory)()
            raw_key = key_fn(*args, **kwargs)

            if not raw_key:
                logger.warning(
                    "idempotency_empty_key_skip",
                    namespace=namespace,
                    func=func.__name__,
                )
                return await func(*args, **kwargs)

            ikey = IdempotencyKey(namespace=namespace, key=raw_key, ttl_seconds=ttl)
            claimed = await store.claim(ikey)

            if not claimed:
                cached = await store.cached_result(ikey)
                if cached is not None:
                    logger.info(
                        "idempotency_cache_hit",
                        namespace=namespace,
                        func=func.__name__,
                    )
                    return cached  # type: ignore[return-value]
                # Claim conflict but no cached result → TTL race, execute again
                logger.warning(
                    "idempotency_claim_lost_no_cache",
                    namespace=namespace,
                    func=func.__name__,
                )

            result = await func(*args, **kwargs)

            # Store minimal projection: {id, status, external_id}
            # Only subset that callers need for duplicate detection (D10/D11).
            if isinstance(result, dict):
                projected = {k: result[k] for k in ("id", "status", "external_id") if k in result}
                if projected:
                    await store.store_result(ikey, projected)

            return result

        return wrapper

    return deco


def _default_store_factory() -> IdempotencyStore:
    """Default factory — uses the global Redis client from core.database."""
    from src.core.database import redis_client
    from src.shared.idempotency.infrastructure.redis_store import RedisIdempotencyStore

    return RedisIdempotencyStore(redis_client)
