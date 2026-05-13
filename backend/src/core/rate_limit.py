"""Redis-based rate limiting for API endpoints.

Uses a sliding-window counter backed by Redis.
Gracefully degrades (allows all requests) when Redis is unavailable.
"""

from __future__ import annotations

import time

import structlog
from fastapi import HTTPException
from luana_core_platform.core.database import redis_client

logger = structlog.get_logger(__name__)

# Default: 30 messages per 60 seconds
DEFAULT_MAX_REQUESTS = 30
DEFAULT_WINDOW_SECONDS = 60

# Redis key prefix for rate limit counters
_KEY_PREFIX = "ratelimit"


class RateLimitExceeded(HTTPException):
    """429 Too Many Requests with Retry-After header."""

    def __init__(self, retry_after: int) -> None:  # noqa: D107
        super().__init__(
            status_code=429,
            detail=(
                f"Límite de mensajes excedido. "
                f"Máximo {DEFAULT_MAX_REQUESTS} mensajes por minuto. "
                f"Intenta de nuevo en {retry_after} segundos."
            ),
            headers={"Retry-After": str(retry_after)},
        )


def check_rate_limit(
    user_id: str,
    scope: str = "copilot-chat",
    max_requests: int = DEFAULT_MAX_REQUESTS,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> None:
    """Check if user has exceeded the rate limit.

    Uses a Redis sorted set with timestamps as scores for a
    sliding-window counter. If Redis is unavailable, silently allows
    the request (graceful degradation).

    Args:
        user_id: Unique identifier for the user.
        scope: Namespace for the rate limit (e.g. "copilot-chat").
        max_requests: Maximum requests allowed in the window.
        window_seconds: Window size in seconds.

    Raises:
        RateLimitExceeded: If the user has exceeded the limit.
    """
    if not redis_client:
        logger.debug("rate_limit_skip_no_redis", scope=scope)
        return

    now = time.time()
    key = f"{_KEY_PREFIX}:{scope}:{user_id}"
    window_start = now - window_seconds

    exceeded = False
    retry_after = window_seconds

    try:
        pipe = redis_client.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, "-inf", window_start)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set TTL so keys auto-expire
        pipe.expire(key, window_seconds)
        results = pipe.execute()

        current_count = results[1]

        if current_count >= max_requests:
            # Find oldest entry to calculate retry-after
            oldest = redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_ts = oldest[0][1]
                retry_after = max(1, int((oldest_ts + window_seconds) - now))

            logger.warning(
                "rate_limit_exceeded",
                user_id=user_id,
                scope=scope,
                current_count=current_count,
                max_requests=max_requests,
                retry_after=retry_after,
            )
            # Remove the entry we just added since we're rejecting
            redis_client.zrem(key, str(now))
            exceeded = True

    except Exception:
        logger.exception("rate_limit_redis_error", scope=scope, user_id=user_id)

    if exceeded:
        raise RateLimitExceeded(retry_after=retry_after)
