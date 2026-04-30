"""Tests for CircuitBreaker — asyncio Redis-backed per-(channel, tenant_id).

TDD RED → GREEN:
- State machine: CLOSED → OPEN → HALF_OPEN → CLOSED/OPEN
- Per-key isolation (tenant A open does not affect tenant B)
- Soft-fail on Redis unavailable

PR-5 PI-1 S2.
PR-5 Sub-G: FakeRedis updated to async methods to match redis.asyncio.Redis
(fixes F-6 — CB uses await on Redis calls, tests must use async fakes).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.campaigns.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from src.modules.campaigns.infrastructure.resilience.errors import CircuitBreakerOpenError


# ── Fake Redis ────────────────────────────────────────────────────────────────


class FakeRedis:
    """Async in-process fake Redis for circuit breaker tests.

    All methods are async to match redis.asyncio.Redis (production client).
    Circuit breaker awaits all Redis calls — sync fakes would silently return
    coroutines instead of values.
    """

    def __init__(self) -> None:
        self._store: dict = {}
        self._zsets: dict = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value, nx: bool = False, ex: int | None = None):
        if nx and key in self._store:
            return None
        self._store[key] = value if isinstance(value, bytes) else str(value).encode()
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
            if k in self._zsets:
                del self._zsets[k]
                count += 1
        return count

    async def zadd(self, key: str, mapping: dict) -> int:
        if key not in self._zsets:
            self._zsets[key] = {}
        self._zsets[key].update(mapping)
        return len(mapping)

    async def zremrangebyscore(self, key: str, min_score, max_score) -> int:
        if key not in self._zsets:
            return 0
        before = len(self._zsets[key])
        to_remove = [m for m, s in self._zsets[key].items() if s <= float(max_score)]
        for m in to_remove:
            del self._zsets[key][m]
        return before - len(self._zsets[key])

    async def zcard(self, key: str) -> int:
        return len(self._zsets.get(key, {}))

    async def incr(self, key: str) -> int:
        raw = self._store.get(key)
        current = int(raw) if raw else 0
        new_val = current + 1
        self._store[key] = str(new_val).encode()
        return new_val

    async def expire(self, key: str, seconds: int) -> int:
        return 1  # no-op for test


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def fast_config() -> CircuitBreakerConfig:
    """Config with tight thresholds for testing."""
    return CircuitBreakerConfig(
        fail_threshold=2,
        open_duration_seconds=1,
        half_open_probes=1,
        rolling_window_seconds=60,
    )


def _make_cb(fake_redis, config=None, tenant_id=None) -> CircuitBreaker:
    return CircuitBreaker(
        channel="telegram",
        tenant_id=tenant_id or uuid4(),
        redis_client=fake_redis,
        config=config,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_closed_state_passes_calls(fake_redis, fast_config) -> None:
    """CLOSED: fn executes normally."""
    cb = _make_cb(fake_redis, fast_config)

    async def ok_fn() -> str:
        return "success"

    result = await cb.call(ok_fn)
    assert result == "success"


@pytest.mark.asyncio
async def test_transitions_to_open_after_threshold_failures(fake_redis, fast_config) -> None:
    """CLOSED → OPEN after fail_threshold failures."""
    cb = _make_cb(fake_redis, fast_config)

    async def failing_fn() -> None:
        msg = "provider down"
        raise RuntimeError(msg)

    # First failure
    with pytest.raises(RuntimeError):
        await cb.call(failing_fn)

    # Second failure → should open
    with pytest.raises(RuntimeError):
        await cb.call(failing_fn)

    state = await cb.state
    assert state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_open_state_raises_circuit_breaker_error(fake_redis, fast_config) -> None:
    """OPEN: subsequent calls raise CircuitBreakerOpenError."""
    cb = _make_cb(fake_redis, fast_config)
    await cb.force_open()

    async def any_fn() -> str:
        return "should not run"

    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        await cb.call(any_fn)

    assert exc_info.value.channel == "telegram"
    assert exc_info.value.retry_after_seconds > 0


@pytest.mark.asyncio
async def test_half_open_probe_success_transitions_to_closed(fake_redis) -> None:
    """HALF_OPEN probe success → CLOSED."""
    # Config with 0s open_duration so probe immediately available
    config = CircuitBreakerConfig(
        fail_threshold=1, open_duration_seconds=0, half_open_probes=1, rolling_window_seconds=60
    )
    cb = _make_cb(fake_redis, config)
    await cb.force_open()

    async def ok_fn() -> str:
        return "ok"

    # Should probe and succeed → CLOSED
    result = await cb.call(ok_fn)
    assert result == "ok"
    state = await cb.state
    assert state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_half_open_probe_failure_returns_to_open(fake_redis) -> None:
    """HALF_OPEN probe failure → back to OPEN."""
    config = CircuitBreakerConfig(
        fail_threshold=1, open_duration_seconds=0, half_open_probes=1, rolling_window_seconds=60
    )
    cb = _make_cb(fake_redis, config)
    await cb.force_open()

    async def fail_fn() -> None:
        msg = "still down"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError):
        await cb.call(fail_fn)

    state = await cb.state
    assert state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_per_tenant_isolation(fake_redis, fast_config) -> None:
    """Opening breaker for tenant_A does NOT affect tenant_B."""
    tenant_a = uuid4()
    tenant_b = uuid4()
    cb_a = CircuitBreaker(channel="telegram", tenant_id=tenant_a, redis_client=fake_redis, config=fast_config)
    cb_b = CircuitBreaker(channel="telegram", tenant_id=tenant_b, redis_client=fake_redis, config=fast_config)

    await cb_a.force_open()

    state_a = await cb_a.state
    state_b = await cb_b.state

    assert state_a == CircuitState.OPEN
    assert state_b == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_per_channel_isolation(fake_redis, fast_config) -> None:
    """Opening breaker for telegram does NOT affect whatsapp (future PI-2 prep)."""
    tenant_id = uuid4()
    cb_telegram = CircuitBreaker(channel="telegram", tenant_id=tenant_id, redis_client=fake_redis, config=fast_config)
    cb_whatsapp = CircuitBreaker(channel="whatsapp", tenant_id=tenant_id, redis_client=fake_redis, config=fast_config)

    await cb_telegram.force_open()

    state_telegram = await cb_telegram.state
    state_whatsapp = await cb_whatsapp.state

    assert state_telegram == CircuitState.OPEN
    assert state_whatsapp == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_soft_fail_when_redis_unavailable() -> None:
    """Redis=None → soft-fail → calls pass through (not blocked)."""
    config = CircuitBreakerConfig(
        fail_threshold=2, open_duration_seconds=60, half_open_probes=1, rolling_window_seconds=60
    )
    cb = CircuitBreaker(channel="telegram", tenant_id=uuid4(), redis_client=None, config=config)

    async def ok_fn() -> str:
        return "ok"

    result = await cb.call(ok_fn)
    assert result == "ok"


@pytest.mark.asyncio
async def test_reset_clears_all_state(fake_redis, fast_config) -> None:
    """reset() clears state so breaker is CLOSED again."""
    cb = _make_cb(fake_redis, fast_config)
    await cb.force_open()

    state_before = await cb.state
    assert state_before == CircuitState.OPEN

    await cb.reset()
    state_after = await cb.state
    assert state_after == CircuitState.CLOSED
