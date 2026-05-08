"""TDD — EtlRefreshGuard unit tests. Written RED first.

Tests cover:
- rate_limit_exceeded → returns retry_after_seconds correctly
- confirm_threshold (1 prior in window) → requires_confirmation=true
- soft_fail Redis unavailable → fail-open + structlog warning
- DEFAULT_LIMIT=3 + WINDOW=3600s
"""

from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
CHANNEL = "meta-ads"


@pytest.fixture
def mock_redis():
    """Mock async Redis client with pipeline support."""
    redis = MagicMock()
    pipeline = AsyncMock()
    redis.pipeline = MagicMock(return_value=pipeline)
    pipeline.zremrangebyscore = MagicMock()
    pipeline.zcard = MagicMock()
    pipeline.zadd = MagicMock()
    pipeline.expire = MagicMock()
    pipeline.execute = AsyncMock()
    return redis, pipeline


@pytest.fixture
def mock_config_repo():
    """Mock channel config repo that returns None (use default limit)."""
    repo = AsyncMock()
    repo.get_limit = AsyncMock(return_value=None)
    return repo


class TestGuardDecisionDataclass:
    """Verify GuardDecision is a frozen dataclass with expected fields."""

    def test_guard_decision_allowed_fields(self) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            GuardDecision,
        )

        d = GuardDecision(allowed=True, current_count=1, limit=3)
        assert d.allowed is True
        assert d.current_count == 1
        assert d.limit == 3
        assert d.retry_after_seconds is None
        assert d.requires_confirmation is False
        assert d.soft_fail is False

    def test_guard_decision_blocked_fields(self) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            GuardDecision,
        )

        d = GuardDecision(
            allowed=False,
            current_count=3,
            limit=3,
            retry_after_seconds=1234,
        )
        assert d.allowed is False
        assert d.retry_after_seconds == 1234
        assert d.requires_confirmation is False

    def test_guard_decision_requires_confirmation_fields(self) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            GuardDecision,
        )

        d = GuardDecision(
            allowed=False,
            current_count=2,
            limit=3,
            requires_confirmation=True,
        )
        assert d.requires_confirmation is True
        assert d.allowed is False


class TestEtlRefreshGuardConstants:
    """Verify class-level constants match spec."""

    def test_default_limit_is_3(self) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        assert EtlRefreshGuard.DEFAULT_LIMIT == 3

    def test_window_is_3600_seconds(self) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        assert EtlRefreshGuard.WINDOW_SECONDS == 3600

    def test_confirm_threshold_is_1(self) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        assert EtlRefreshGuard.CONFIRM_THRESHOLD == 1


class TestEtlRefreshGuardAllowed:
    """First call in window → allowed, counter incremented."""

    @pytest.mark.asyncio
    async def test_first_call_allowed(self, mock_redis, mock_config_repo) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis, pipeline = mock_redis
        # Simulate: window has 0 existing entries
        pipeline.execute = AsyncMock(return_value=[None, 0])

        add_pipeline = AsyncMock()
        add_pipeline.zadd = MagicMock()
        add_pipeline.expire = MagicMock()
        add_pipeline.execute = AsyncMock(return_value=[1, True])
        redis.pipeline = MagicMock(side_effect=[pipeline, add_pipeline])

        guard = EtlRefreshGuard(redis, mock_config_repo)
        decision = await guard.check(TENANT_ID, CHANNEL, confirmed=False)

        assert decision.allowed is True
        assert decision.current_count == 1  # 0 + 1
        assert decision.limit == 3


class TestEtlRefreshGuardConfirmThreshold:
    """After 1 refresh in window, second requires confirmation (not confirmed)."""

    @pytest.mark.asyncio
    async def test_second_call_requires_confirmation_if_not_confirmed(self, mock_redis, mock_config_repo) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis, pipeline = mock_redis
        # Simulate: window has 2 entries (> CONFIRM_THRESHOLD=1)
        pipeline.execute = AsyncMock(return_value=[None, 2])

        redis.pipeline = MagicMock(return_value=pipeline)

        guard = EtlRefreshGuard(redis, mock_config_repo)
        decision = await guard.check(TENANT_ID, CHANNEL, confirmed=False)

        assert decision.allowed is False
        assert decision.requires_confirmation is True
        assert decision.current_count == 2
        assert decision.limit == 3

    @pytest.mark.asyncio
    async def test_second_call_allowed_if_confirmed(self, mock_redis, mock_config_repo) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis, pipeline = mock_redis
        # Simulate: window has 2 entries, but confirmed=True
        pipeline.execute = AsyncMock(return_value=[None, 2])

        add_pipeline = AsyncMock()
        add_pipeline.zadd = MagicMock()
        add_pipeline.expire = MagicMock()
        add_pipeline.execute = AsyncMock(return_value=[1, True])
        redis.pipeline = MagicMock(side_effect=[pipeline, add_pipeline])

        guard = EtlRefreshGuard(redis, mock_config_repo)
        decision = await guard.check(TENANT_ID, CHANNEL, confirmed=True)

        assert decision.allowed is True
        assert decision.requires_confirmation is False


class TestEtlRefreshGuardRateLimit:
    """When current_count >= limit → blocked with retry_after_seconds."""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_returns_retry_after(self, mock_redis, mock_config_repo) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis, pipeline = mock_redis
        # Simulate: window already has 3 entries (>= DEFAULT_LIMIT)
        pipeline.execute = AsyncMock(return_value=[None, 3])

        # oldest score = 1000 seconds ago (within 3600s window)
        now = time.time()
        oldest_score = now - 1000
        redis.zrange = AsyncMock(return_value=[(b"some-uuid", oldest_score)])
        redis.pipeline = MagicMock(return_value=pipeline)

        guard = EtlRefreshGuard(redis, mock_config_repo)
        decision = await guard.check(TENANT_ID, CHANNEL, confirmed=False)

        assert decision.allowed is False
        assert decision.requires_confirmation is False
        assert decision.retry_after_seconds is not None
        assert decision.retry_after_seconds > 0
        # Retry after should be approximately WINDOW - elapsed = 3600 - 1000 = 2600
        assert 2500 <= decision.retry_after_seconds <= 2700

    @pytest.mark.asyncio
    async def test_rate_limit_with_custom_limit_from_config(self, mock_redis) -> None:
        """Custom limit from channel config overrides default."""
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis, pipeline = mock_redis
        # Custom limit = 5; window has 5 entries → blocked
        pipeline.execute = AsyncMock(return_value=[None, 5])

        config_repo = AsyncMock()
        config_repo.get_limit = AsyncMock(return_value=5)

        now = time.time()
        oldest_score = now - 500
        redis.zrange = AsyncMock(return_value=[(b"uuid", oldest_score)])
        redis.pipeline = MagicMock(return_value=pipeline)

        guard = EtlRefreshGuard(redis, config_repo)
        decision = await guard.check(TENANT_ID, CHANNEL, confirmed=False)

        assert decision.allowed is False
        assert decision.limit == 5


class TestEtlRefreshGuardSoftFail:
    """Redis unavailable → fail-open + structlog warning."""

    @pytest.mark.asyncio
    async def test_redis_unavailable_fail_open(self, mock_config_repo) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis = MagicMock()
        # pipeline.execute raises ConnectionError
        pipeline = AsyncMock()
        pipeline.zremrangebyscore = MagicMock()
        pipeline.zcard = MagicMock()
        pipeline.execute = AsyncMock(side_effect=ConnectionError("Redis down"))
        redis.pipeline = MagicMock(return_value=pipeline)

        guard = EtlRefreshGuard(redis, mock_config_repo)

        with patch("structlog.get_logger") as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger

            decision = await guard.check(TENANT_ID, CHANNEL, confirmed=False)

        assert decision.allowed is True
        assert decision.soft_fail is True
        assert decision.current_count == 0

    @pytest.mark.asyncio
    async def test_redis_unavailable_logs_warning(self, mock_config_repo) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis = MagicMock()
        pipeline = AsyncMock()
        pipeline.zremrangebyscore = MagicMock()
        pipeline.zcard = MagicMock()
        pipeline.execute = AsyncMock(side_effect=RuntimeError("Redis timeout"))
        redis.pipeline = MagicMock(return_value=pipeline)

        guard = EtlRefreshGuard(redis, mock_config_repo)

        with patch("src.modules.analytics.application.services.etl_refresh_guard.logger") as mock_logger:
            decision = await guard.check(TENANT_ID, CHANNEL, confirmed=False)

        assert decision.soft_fail is True
        mock_logger.warning.assert_called_once()
        call_kwargs = mock_logger.warning.call_args
        # Verify first positional arg is the event name
        assert "etl_refresh_guard_redis_unavailable_fail_open" in call_kwargs[0]


class TestEtlRefreshGuardKeyTemplate:
    """Verify Redis key includes tenant_id and channel."""

    @pytest.mark.asyncio
    async def test_key_includes_tenant_and_channel(self, mock_redis, mock_config_repo) -> None:
        from src.modules.analytics.application.services.etl_refresh_guard import (
            EtlRefreshGuard,
        )

        redis, pipeline = mock_redis
        pipeline.execute = AsyncMock(return_value=[None, 0])

        add_pipeline = AsyncMock()
        add_pipeline.zadd = MagicMock()
        add_pipeline.expire = MagicMock()
        add_pipeline.execute = AsyncMock(return_value=[1, True])
        redis.pipeline = MagicMock(side_effect=[pipeline, add_pipeline])

        guard = EtlRefreshGuard(redis, mock_config_repo)
        await guard.check(TENANT_ID, CHANNEL, confirmed=False)

        # Verify zadd was called with the correct key
        expected_key = f"etl_refresh:{TENANT_ID}:{CHANNEL}"
        # zadd is called on the add_pipeline
        add_pipeline.zadd.assert_called_once()
        call_args = add_pipeline.zadd.call_args
        assert call_args[0][0] == expected_key
