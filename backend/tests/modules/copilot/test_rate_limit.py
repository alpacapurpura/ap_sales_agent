"""Tests for copilot chat rate limiting."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.core.rate_limit import (
    DEFAULT_MAX_REQUESTS,
    RateLimitExceeded,
    check_rate_limit,
)
from src.modules.copilot.api.chat import router
from src.modules.iam.api.dependencies import get_current_user

# ---------------------------------------------------------------------------
# Unit tests for the rate limiter itself
# ---------------------------------------------------------------------------


class TestCheckRateLimit:
    """Unit tests for check_rate_limit function."""

    def test_allows_request_when_redis_unavailable(self) -> None:
        """When Redis is None, requests should always be allowed."""
        with patch("src.core.rate_limit.redis_client", None):
            # Should not raise
            check_rate_limit(user_id="user-1", scope="test")

    def test_allows_request_under_limit(self) -> None:
        """When under the limit, request should be allowed."""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        # zremrangebyscore result, zcard result, zadd result, expire result
        mock_pipe.execute.return_value = [0, 5, 1, True]

        with patch("src.core.rate_limit.redis_client", mock_redis):
            check_rate_limit(user_id="user-1", scope="test", max_requests=10)

    def test_raises_429_when_limit_exceeded(self) -> None:
        """When at or over the limit, should raise RateLimitExceeded."""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        # zcard returns max_requests (already at limit)
        mock_pipe.execute.return_value = [0, 30, 1, True]
        # Oldest entry for retry-after calculation
        mock_redis.zrange.return_value = [("ts", 1000.0)]

        with (
            patch("src.core.rate_limit.redis_client", mock_redis),
            pytest.raises(RateLimitExceeded) as exc_info,
        ):
            check_rate_limit(
                user_id="user-1",
                scope="test",
                max_requests=30,
                window_seconds=60,
            )

        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers
        # Should remove the rejected entry
        mock_redis.zrem.assert_called_once()

    def test_retry_after_header_is_positive_integer(self) -> None:
        """Retry-After header must be a positive integer string."""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [0, 10, 1, True]
        mock_redis.zrange.return_value = [("ts", 1000.0)]

        with (
            patch("src.core.rate_limit.redis_client", mock_redis),
            patch("src.core.rate_limit.time") as mock_time,
            pytest.raises(RateLimitExceeded) as exc_info,
        ):
            mock_time.time.return_value = 1050.0
            check_rate_limit(
                user_id="user-1",
                scope="test",
                max_requests=10,
                window_seconds=60,
            )

        retry_after = int(exc_info.value.headers["Retry-After"])
        assert retry_after >= 1

    def test_graceful_degradation_on_redis_error(self) -> None:
        """When Redis raises an error, should allow the request."""
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("Redis connection lost")

        with patch("src.core.rate_limit.redis_client", mock_redis):
            # Should not raise
            check_rate_limit(user_id="user-1", scope="test")

    def test_custom_scope_and_limits(self) -> None:
        """Custom scope and limits should work."""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [0, 3, 1, True]

        with patch("src.core.rate_limit.redis_client", mock_redis):
            check_rate_limit(
                user_id="user-1",
                scope="custom-scope",
                max_requests=5,
                window_seconds=120,
            )

        # Verify the key uses the custom scope
        mock_pipe.zremrangebyscore.assert_called_once()
        call_args = mock_pipe.zremrangebyscore.call_args[0]
        assert "custom-scope" in call_args[0]


class TestRateLimitExceeded:
    """Tests for the RateLimitExceeded exception."""

    def test_status_code_is_429(self) -> None:
        exc = RateLimitExceeded(retry_after=30)
        assert exc.status_code == 429

    def test_has_retry_after_header(self) -> None:
        exc = RateLimitExceeded(retry_after=30)
        assert exc.headers["Retry-After"] == "30"

    def test_detail_message_in_spanish(self) -> None:
        exc = RateLimitExceeded(retry_after=15)
        assert "Límite" in exc.detail
        assert "15 segundos" in exc.detail


# ---------------------------------------------------------------------------
# Integration test: chat endpoint applies rate limiting
# ---------------------------------------------------------------------------


class TestChatEndpointRateLimit:
    """Verify that the /chat endpoint integrates the rate limiter."""

    def _build_client(self, tenant_id=None):
        if tenant_id is None:
            tenant_id = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/copilot")
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=uuid4(),
            tenant_id=tenant_id,
        )
        return TestClient(app)

    @patch("src.modules.copilot.api.chat.check_rate_limit")
    @patch("src.modules.copilot.api.chat.CopilotOrchestrator")
    def test_chat_calls_rate_limiter(self, mock_orch_cls, mock_rate_limit) -> None:
        """The /chat endpoint must call check_rate_limit."""
        mock_orch = MagicMock()
        mock_orch.stream_chat.return_value = iter([])
        mock_orch_cls.return_value = mock_orch

        client = self._build_client()
        client.post(
            "/api/v1/copilot/chat",
            json={"message": "hello"},
        )

        mock_rate_limit.assert_called_once()
        # Verify it was called with the user_id
        call_kwargs = mock_rate_limit.call_args
        assert "user_id" in call_kwargs.kwargs or len(call_kwargs.args) > 0

    @patch("src.modules.copilot.api.chat.check_rate_limit")
    def test_chat_returns_429_when_rate_limited(self, mock_rate_limit) -> None:
        """When rate limit is exceeded, endpoint returns 429."""
        mock_rate_limit.side_effect = RateLimitExceeded(retry_after=42)

        client = self._build_client()
        response = client.post(
            "/api/v1/copilot/chat",
            json={"message": "hello"},
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "42"

    @patch("src.modules.copilot.api.chat.check_rate_limit")
    @patch("src.modules.copilot.api.chat.CopilotOrchestrator")
    def test_chat_passes_correct_scope(self, mock_orch_cls, mock_rate_limit) -> None:
        """Rate limiter must be called with scope='copilot-chat'."""
        mock_orch = MagicMock()
        mock_orch.stream_chat.return_value = iter([])
        mock_orch_cls.return_value = mock_orch

        client = self._build_client()
        client.post(
            "/api/v1/copilot/chat",
            json={"message": "hello"},
        )

        call_kwargs = mock_rate_limit.call_args.kwargs
        assert call_kwargs.get("scope") == "copilot-chat"

    @patch("src.modules.copilot.api.chat.check_rate_limit")
    @patch("src.modules.copilot.api.chat.CopilotOrchestrator")
    def test_default_max_requests_is_30(self, mock_orch_cls, mock_rate_limit) -> None:
        """Default max_requests should be 30 (from module constant)."""
        mock_orch = MagicMock()
        mock_orch.stream_chat.return_value = iter([])
        mock_orch_cls.return_value = mock_orch

        client = self._build_client()
        client.post(
            "/api/v1/copilot/chat",
            json={"message": "hello"},
        )

        # The default is used (no explicit max_requests kwarg override)
        assert DEFAULT_MAX_REQUESTS == 30
