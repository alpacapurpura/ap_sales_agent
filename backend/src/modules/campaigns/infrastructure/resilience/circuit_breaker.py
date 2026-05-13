"""Asyncio Redis-backed circuit breaker.

Per-(channel, tenant_id) isolation: one failing tenant's Telegram bot does
not open the breaker for other tenants.

State machine:
  CLOSED  → (failures >= threshold in rolling window) → OPEN
  OPEN    → (now - opened_at >= open_duration_seconds) → HALF_OPEN
  HALF_OPEN → (probe success) → CLOSED | (probe failure) → OPEN

Redis keys per (channel, tenant_id):
  cb:campaigns:{channel}:{tenant_id}:state           STRING
  cb:campaigns:{channel}:{tenant_id}:failures        ZSET  (ts:uuid → score=epoch)
  cb:campaigns:{channel}:{tenant_id}:opened_at       STRING (epoch float)
  cb:campaigns:{channel}:{tenant_id}:probes          INT   counter

Tunable env: CAMPAIGNS_CB_FAIL_THRESHOLD, CAMPAIGNS_CB_OPEN_DURATION_SECONDS,
             CAMPAIGNS_CB_HALF_OPEN_PROBES, CAMPAIGNS_CB_ROLLING_WINDOW_SECONDS.

PR-5 PI-1 S2 — tessl__graceful-degradation iron rule: every external call
gets timeout + fallback (circuit breaker IS the fallback pattern).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

import structlog

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from uuid import UUID

from luana_core_campaigns.infrastructure.resilience.errors import CircuitBreakerOpenError


@runtime_checkable
class _RedisClientProtocol(Protocol):
    """Minimal async Redis client protocol for circuit breaker operations.

    Compatible with redis.asyncio.Redis (production) and AsyncMock in tests.
    All methods are async — the CB is async and runs on the asyncio event loop.
    """

    async def get(self, key: str) -> bytes | str | None: ...
    async def set(self, key: str, value: str | int, nx: bool = ..., ex: int | None = ...) -> object: ...
    async def delete(self, *keys: str) -> int: ...
    async def zadd(self, key: str, mapping: dict[str, float]) -> int: ...
    async def zremrangebyscore(self, key: str, min_score: str | float, max_score: str | float) -> int: ...
    async def zcard(self, key: str) -> int: ...
    async def incr(self, key: str) -> int: ...
    async def expire(self, key: str, seconds: int) -> int: ...


logger = structlog.get_logger(__name__)

T = TypeVar("T")

_KEY_PREFIX = "cb:campaigns"


class CircuitState(StrEnum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True, slots=True)
class CircuitBreakerConfig:
    """Tunable circuit breaker configuration.

    Defaults map to env vars (CAMPAIGNS_CB_*). Loaded lazily by factory.
    """

    fail_threshold: int = 5
    open_duration_seconds: int = 60
    half_open_probes: int = 1
    rolling_window_seconds: int = 60


def _default_config() -> CircuitBreakerConfig:
    """Load config from environment with sane defaults."""
    import os

    return CircuitBreakerConfig(
        fail_threshold=int(os.environ.get("CAMPAIGNS_CB_FAIL_THRESHOLD", "5")),
        open_duration_seconds=int(os.environ.get("CAMPAIGNS_CB_OPEN_DURATION_SECONDS", "60")),
        half_open_probes=int(os.environ.get("CAMPAIGNS_CB_HALF_OPEN_PROBES", "1")),
        rolling_window_seconds=int(os.environ.get("CAMPAIGNS_CB_ROLLING_WINDOW_SECONDS", "60")),
    )


class CircuitBreaker:
    """Asyncio Redis-backed per-(channel, tenant_id) circuit breaker.

    Usage::

        cb = CircuitBreaker(channel="telegram", tenant_id=tenant_id, redis_client=r)
        result = await cb.call(my_async_fn, arg1, kwarg=value)

    On OPEN state: raises CircuitBreakerOpenError immediately.
    Callers (workers) catch and mark task failed / skip retry.
    """

    def __init__(
        self,
        *,
        channel: str,
        tenant_id: UUID,
        redis_client: _RedisClientProtocol | None,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        """Initialize per-(channel, tenant_id) breaker."""
        self._channel = channel
        self._tenant_id = tenant_id
        self._redis: _RedisClientProtocol | None = redis_client
        self._config = config or _default_config()
        self._prefix = f"{_KEY_PREFIX}:{channel}:{tenant_id}"

    # ── Key helpers ──────────────────────────────────────────────────────────

    @property
    def _state_key(self) -> str:
        return f"{self._prefix}:state"

    @property
    def _failures_key(self) -> str:
        return f"{self._prefix}:failures"

    @property
    def _opened_at_key(self) -> str:
        return f"{self._prefix}:opened_at"

    @property
    def _probes_key(self) -> str:
        return f"{self._prefix}:probes"

    # ── State reads ──────────────────────────────────────────────────────────

    async def _get_state(self) -> CircuitState:
        """Read current state from Redis. Soft-fail → CLOSED."""
        try:
            if self._redis is None:
                return CircuitState.CLOSED
            raw = await self._redis.get(self._state_key)
            if raw is None:
                return CircuitState.CLOSED
            raw_str = raw.decode() if isinstance(raw, bytes) else raw
            return CircuitState(raw_str)
        except Exception:  # noqa: BLE001
            logger.warning(
                "circuit_breaker_state_read_error",
                channel=self._channel,
                tenant_id=str(self._tenant_id),
                exc_info=True,
            )
            return CircuitState.CLOSED

    async def _get_opened_at(self) -> float | None:
        """Return epoch when breaker opened, or None."""
        try:
            if self._redis is None:
                return None
            raw = await self._redis.get(self._opened_at_key)
            if raw is None:
                return None
            raw_str = raw.decode() if isinstance(raw, bytes) else raw
            return float(raw_str)
        except Exception:  # noqa: BLE001
            return None

    async def _count_recent_failures(self) -> int:
        """Count failures in rolling window using ZSET score (epoch seconds)."""
        try:
            if self._redis is None:
                return 0
            now = time.time()
            cutoff = now - self._config.rolling_window_seconds
            # Remove stale entries first
            await self._redis.zremrangebyscore(self._failures_key, "-inf", cutoff)
            count = await self._redis.zcard(self._failures_key)
            return int(count) if count else 0
        except Exception:  # noqa: BLE001
            return 0

    # ── State transitions ────────────────────────────────────────────────────

    async def _record_failure(self) -> int:
        """Record failure in rolling window. Returns updated count."""
        try:
            if self._redis is None:
                return 0
            now = time.time()
            member = f"{now}:{id(object())}"
            await self._redis.zadd(self._failures_key, {member: now})
            # Set TTL on the ZSET = rolling_window + buffer
            await self._redis.expire(self._failures_key, self._config.rolling_window_seconds + 10)
            count = await self._count_recent_failures()
            return count
        except Exception:  # noqa: BLE001
            logger.warning("circuit_breaker_record_failure_error", channel=self._channel, exc_info=True)
            return 0

    async def _transition_open(self) -> None:
        """Transition to OPEN state. Emits audit log structlog."""
        try:
            if self._redis is None:
                return
            now = time.time()
            await self._redis.set(self._state_key, CircuitState.OPEN.value)
            await self._redis.set(self._opened_at_key, str(now))
            await self._redis.delete(self._probes_key)
        except Exception:  # noqa: BLE001
            logger.warning("circuit_breaker_transition_open_error", channel=self._channel, exc_info=True)
        logger.warning(
            "circuit_breaker_opened",
            channel=self._channel,
            tenant_id=str(self._tenant_id),
            fail_count=await self._count_recent_failures(),
            opened_at=time.time(),
        )

    async def _transition_closed(self) -> None:
        """Transition to CLOSED state. Reset failure counter."""
        try:
            if self._redis is None:
                return
            await self._redis.set(self._state_key, CircuitState.CLOSED.value)
            await self._redis.delete(self._opened_at_key)
            await self._redis.delete(self._failures_key)
            await self._redis.delete(self._probes_key)
        except Exception:  # noqa: BLE001
            logger.warning("circuit_breaker_transition_closed_error", channel=self._channel, exc_info=True)
        logger.info(
            "circuit_breaker_closed",
            channel=self._channel,
            tenant_id=str(self._tenant_id),
            closed_at=time.time(),
        )

    # ── Public API ───────────────────────────────────────────────────────────

    async def call(self, fn: Callable[..., Awaitable[T]], /, *args: object, **kwargs: object) -> T:
        """Execute fn under circuit breaker protection.

        Raises:
            CircuitBreakerOpenError: When OPEN or HALF_OPEN without probe slot.
            Any exception raised by fn (after recording failure).
        """
        state = await self._get_state()

        if state == CircuitState.OPEN:
            opened_at = await self._get_opened_at() or time.time()
            elapsed = time.time() - opened_at
            remaining = self._config.open_duration_seconds - elapsed

            if remaining > 0:
                raise CircuitBreakerOpenError(
                    channel=self._channel,
                    tenant_id=self._tenant_id,
                    retry_after_seconds=remaining,
                )
            # Time expired → transition to HALF_OPEN
            await self._set_half_open()
            state = CircuitState.HALF_OPEN

        if state == CircuitState.HALF_OPEN:
            # Allow only half_open_probes concurrent probes
            probe_count = await self._increment_probe()
            if probe_count > self._config.half_open_probes:
                opened_at = await self._get_opened_at() or time.time()
                raise CircuitBreakerOpenError(
                    channel=self._channel,
                    tenant_id=self._tenant_id,
                    retry_after_seconds=self._config.open_duration_seconds,
                )

        try:
            result = await fn(*args, **kwargs)
            # Success: reset to CLOSED if we were HALF_OPEN
            if state == CircuitState.HALF_OPEN:
                await self._transition_closed()
            return result
        except Exception:
            fail_count = await self._record_failure()
            if fail_count >= self._config.fail_threshold or state == CircuitState.HALF_OPEN:
                await self._transition_open()
            raise

    async def _set_half_open(self) -> None:
        """Transition to HALF_OPEN."""
        try:
            if self._redis is None:
                return
            await self._redis.set(self._state_key, CircuitState.HALF_OPEN.value)
            await self._redis.delete(self._probes_key)
        except Exception:  # noqa: BLE001
            pass

    async def _increment_probe(self) -> int:
        """Increment and return probe count."""
        try:
            if self._redis is None:
                return 1
            count = await self._redis.incr(self._probes_key)
            await self._redis.expire(self._probes_key, self._config.open_duration_seconds * 2)
            return int(count)
        except Exception:  # noqa: BLE001
            return 1

    @property
    async def state(self) -> CircuitState:
        """Read current state. Best-effort: fail → assume CLOSED."""
        return await self._get_state()

    async def force_open(self) -> None:
        """Test-only / ops escape hatch. Manually open this breaker."""
        await self._transition_open()

    async def reset(self) -> None:
        """Test-only. Clear all circuit breaker state for (channel, tenant_id)."""
        try:
            if self._redis is None:
                return
            await self._redis.delete(
                self._state_key,
                self._failures_key,
                self._opened_at_key,
                self._probes_key,
            )
        except Exception:  # noqa: BLE001
            pass
