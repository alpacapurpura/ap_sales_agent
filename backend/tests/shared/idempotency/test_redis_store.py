"""Unit tests — RedisIdempotencyStore using fakeredis."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.shared.idempotency.domain.key import IdempotencyKey
from src.shared.idempotency.infrastructure.redis_store import RedisIdempotencyStore

try:
    import fakeredis

    _HAS_FAKEREDIS = True
except ImportError:
    _HAS_FAKEREDIS = False


def _make_key(suffix="test") -> IdempotencyKey:
    """Build a test IdempotencyKey."""
    return IdempotencyKey(
        namespace="webhook:manychat",
        key=f"sig-{uuid4()}",
        ttl_seconds=3600,
    )


class TestRedisIdempotencyStoreWithFakeRedis:
    """Tests using fakeredis for realistic in-memory Redis behavior."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_FAKEREDIS, reason="fakeredis not installed")
    async def test_first_claim_returns_true(self):
        """First claim on new key returns True."""
        redis = fakeredis.FakeRedis()
        store = RedisIdempotencyStore(redis)
        key = _make_key()
        result = await store.claim(key)
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_FAKEREDIS, reason="fakeredis not installed")
    async def test_second_claim_returns_false(self):
        """Second claim on same key returns False (already claimed)."""
        redis = fakeredis.FakeRedis()
        store = RedisIdempotencyStore(redis)
        key = _make_key()

        first = await store.claim(key)
        second = await store.claim(key)

        assert first is True
        assert second is False

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_FAKEREDIS, reason="fakeredis not installed")
    async def test_cached_result_returns_none_when_missing(self):
        """cached_result returns None when no result was stored."""
        redis = fakeredis.FakeRedis()
        store = RedisIdempotencyStore(redis)
        key = _make_key()

        result = await store.cached_result(key)
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_FAKEREDIS, reason="fakeredis not installed")
    async def test_store_and_retrieve_result(self):
        """store_result persists dict; cached_result retrieves it."""
        redis = fakeredis.FakeRedis()
        store = RedisIdempotencyStore(redis)
        key = _make_key()
        payload = {"id": "entity-123", "status": "ok"}

        await store.store_result(key, payload)
        result = await store.cached_result(key)

        assert result == payload

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_FAKEREDIS, reason="fakeredis not installed")
    async def test_concurrent_claim_only_one_wins(self):
        """Simulated concurrent claims: only one should win."""
        redis = fakeredis.FakeRedis()
        store = RedisIdempotencyStore(redis)
        key = _make_key()

        results = [await store.claim(key), await store.claim(key), await store.claim(key)]
        # Only the first should be True
        assert results.count(True) == 1
        assert results.count(False) == 2

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_FAKEREDIS, reason="fakeredis not installed")
    async def test_different_keys_dont_interfere(self):
        """Different IdempotencyKeys operate independently."""
        redis = fakeredis.FakeRedis()
        store = RedisIdempotencyStore(redis)
        key1 = IdempotencyKey(namespace="webhook:manychat", key="sig-a", ttl_seconds=3600)
        key2 = IdempotencyKey(namespace="webhook:manychat", key="sig-b", ttl_seconds=3600)

        r1 = await store.claim(key1)
        r2 = await store.claim(key2)

        assert r1 is True
        assert r2 is True


class TestRedisIdempotencyStoreSoftFail:
    """Tests for soft-fail behavior when Redis is unavailable."""

    @pytest.mark.asyncio
    async def test_claim_with_none_redis_returns_true(self):
        """claim() with None redis client returns True (soft-fail)."""
        store = RedisIdempotencyStore(redis_client=None)
        key = _make_key()
        result = await store.claim(key)
        assert result is True

    @pytest.mark.asyncio
    async def test_cached_result_with_none_redis_returns_none(self):
        """cached_result() with None redis returns None (soft-fail)."""
        store = RedisIdempotencyStore(redis_client=None)
        key = _make_key()
        result = await store.cached_result(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_store_result_with_none_redis_no_raise(self):
        """store_result() with None redis silently succeeds."""
        store = RedisIdempotencyStore(redis_client=None)
        key = _make_key()
        # Should not raise
        await store.store_result(key, {"id": "test", "status": "ok"})

    @pytest.mark.asyncio
    async def test_claim_with_failing_redis_returns_true_softfail(self):
        """claim() when Redis raises returns True (soft-fail allows execution)."""
        mock_redis = MagicMock()
        mock_redis.set.side_effect = Exception("Redis connection refused")
        store = RedisIdempotencyStore(redis_client=mock_redis)
        key = _make_key()

        result = await store.claim(key)
        assert result is True  # Soft-fail
