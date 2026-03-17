"""Tests for MetricsCache — Redis caching layer with silent fallback.

Tests cover:
- Cache hit returns parsed JSON
- Cache miss returns None
- Redis-down fallback returns None (never raises)
- set() stores data with TTL
- set() silently fails when Redis is down
- invalidate_tenant() deletes matching keys
"""

import json
import asyncio
from unittest.mock import MagicMock, patch

import pytest


TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _run(coro):
    """Run a coroutine synchronously for testing."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestMetricsCacheGet:
    """Tests for MetricsCache.get()."""

    def test_returns_parsed_json_on_cache_hit(self):
        """Cache hit: Redis returns JSON string -> parsed dict."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        data = {"total_visitors": 1234, "channels": ["meta", "google"]}
        mock_redis.get.return_value = json.dumps(data)

        cache = MetricsCache(mock_redis)
        result = _run(cache.get(TENANT_ID, "attraction", "last_30_days"))

        assert result == data
        mock_redis.get.assert_called_once_with(
            f"metrics:{TENANT_ID}:attraction:last_30_days"
        )

    def test_returns_none_on_cache_miss(self):
        """Cache miss: Redis returns None -> None."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        cache = MetricsCache(mock_redis)
        result = _run(cache.get(TENANT_ID, "attraction", "last_30_days"))

        assert result is None

    def test_returns_none_when_redis_down(self):
        """Redis ConnectionError -> None (silent fallback, no raise)."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        mock_redis.get.side_effect = ConnectionError("Redis is down")

        cache = MetricsCache(mock_redis)
        result = _run(cache.get(TENANT_ID, "attraction", "last_30_days"))

        assert result is None


class TestMetricsCacheSet:
    """Tests for MetricsCache.set()."""

    def test_stores_data_with_ttl(self):
        """set() calls redis.setex with 300s TTL and JSON-serialized data."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        cache = MetricsCache(mock_redis)
        data = {"visitors": 42}

        _run(cache.set(TENANT_ID, "attraction", "last_30_days", data))

        mock_redis.setex.assert_called_once_with(
            f"metrics:{TENANT_ID}:attraction:last_30_days",
            3600,
            json.dumps(data),
        )

    def test_silently_fails_when_redis_down(self):
        """set() with Redis error -> no exception raised."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        mock_redis.setex.side_effect = ConnectionError("Redis is down")

        cache = MetricsCache(mock_redis)

        # Should not raise
        _run(cache.set(TENANT_ID, "attraction", "last_30_days", {"x": 1}))


class TestMetricsCacheInvalidate:
    """Tests for MetricsCache.invalidate_tenant()."""

    def test_deletes_matching_keys(self):
        """invalidate_tenant() scans and deletes all metrics:{tenant}:* keys."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        matching_keys = [
            f"metrics:{TENANT_ID}:attraction:last_30_days",
            f"metrics:{TENANT_ID}:capture:daily",
        ]
        mock_redis.keys.return_value = matching_keys

        cache = MetricsCache(mock_redis)
        _run(cache.invalidate_tenant(TENANT_ID))

        mock_redis.keys.assert_called_once_with(f"metrics:{TENANT_ID}:*")
        mock_redis.delete.assert_called_once_with(*matching_keys)

    def test_does_nothing_when_no_keys_found(self):
        """invalidate_tenant() with no matching keys -> no delete call."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        mock_redis.keys.return_value = []

        cache = MetricsCache(mock_redis)
        _run(cache.invalidate_tenant(TENANT_ID))

        mock_redis.delete.assert_not_called()

    def test_silently_fails_when_redis_down(self):
        """invalidate_tenant() with Redis error -> no exception."""
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )

        mock_redis = MagicMock()
        mock_redis.keys.side_effect = ConnectionError("Redis is down")

        cache = MetricsCache(mock_redis)
        # Should not raise
        _run(cache.invalidate_tenant(TENANT_ID))
