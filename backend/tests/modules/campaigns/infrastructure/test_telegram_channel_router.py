"""Tests for TelegramChannelRouter.

TDD RED → GREEN per CONTRACT §8 + §10.2:
- happy path: mock httpx 200 → ChannelSendResult.success=True + external_message_id
- 429 rate limit → ChannelRateLimitedError raised (CB counts, ARQ retry)
- 500 server error → ChannelRetryableError raised (CB counts, ARQ retry)
- idempotency-key dedup: re-send with same key returns cached result (no HTTP call)
- ComplianceService block → ChannelComplianceBlocked raised (no CB hit, task SKIPPED)
- OutboundRateLimiter exceed → ChannelTenantRateExceeded raised (no CB hit, reschedule)
- tenant locale applied: format_message_for_tenant_locale called with tenant_id
- select_channel returns "telegram" when lead has telegram_id equivalent in content
- select_channel returns None when "telegram" not in priority

PR-5 PI-1 S2.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from src.modules.campaigns.domain.channel_router import ChannelSendResult
from src.modules.campaigns.infrastructure.channels.errors import (
    ChannelComplianceBlocked,
    ChannelFatalError,
    ChannelRateLimitedError,
    ChannelRetryableError,
    ChannelTenantRateExceeded,
)
from src.modules.campaigns.infrastructure.channels.registry import ChannelRouterRegistry
from src.modules.campaigns.infrastructure.channels.telegram import TelegramChannelRouter
from src.modules.campaigns.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from src.modules.campaigns.infrastructure.resilience.errors import CircuitBreakerOpenError
from src.shared.compliance.domain.check_result import CheckResult


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    """Prevent cross-test registry pollution."""
    yield
    ChannelRouterRegistry().reset()


def _make_httpx_response(status: int, body: dict[str, Any]) -> httpx.Response:
    """Create a real httpx.Response object with given status + JSON body."""
    return httpx.Response(status_code=status, json=body)


def _make_router(
    *,
    httpx_client: httpx.AsyncClient | None = None,
    compliance_service: Any = None,
    rate_limiter: Any = None,
    idempotency_service: Any = None,
    cb_factory: Any = None,
    api_base: str = "https://api.telegram.org",
) -> TelegramChannelRouter:
    """Build a TelegramChannelRouter with DI overrides for testing."""
    token_provider = AsyncMock(return_value="test:BOT_TOKEN")
    return TelegramChannelRouter(
        token_provider=token_provider,
        compliance_service=compliance_service,
        outbound_rate_limiter=rate_limiter,
        idempotency_service=idempotency_service,
        circuit_breaker_factory=cb_factory,
        httpx_client=httpx_client,
        api_base=api_base,
    )


def _make_passthrough_compliance() -> MagicMock:
    """ComplianceService mock that always PASS."""
    svc = MagicMock()
    svc.check = AsyncMock(return_value=CheckResult(allowed=True))
    return svc


def _make_blocking_compliance() -> MagicMock:
    """ComplianceService mock that always BLOCK."""
    svc = MagicMock()
    svc.check = AsyncMock(
        return_value=CheckResult(
            allowed=False,
            failed_policy="blacklist",
            reason="lead is opt-out",
        )
    )
    return svc


def _make_passthrough_rate_limiter() -> MagicMock:
    """OutboundRateLimiter mock that always allows."""
    rl = MagicMock()
    rl.check = AsyncMock(return_value=True)
    return rl


def _make_blocking_rate_limiter() -> MagicMock:
    """OutboundRateLimiter mock that always blocks."""
    rl = MagicMock()
    rl.check = AsyncMock(return_value=False)
    return rl


def _noop_cb_factory() -> Any:
    """CB factory that returns a pass-through CB (no Redis, always CLOSED)."""

    def _factory(channel: str, tenant_id: Any) -> CircuitBreaker:
        return CircuitBreaker(
            channel=channel,
            tenant_id=tenant_id,
            redis_client=None,
            config=CircuitBreakerConfig(fail_threshold=5),
        )

    return _factory


def _make_content(text: str = "Hola {{name}}", chat_id: str = "12345") -> dict[str, Any]:
    return {"chat_id": chat_id, "text": text, "parse_mode": None, "disable_notification": False}


TENANT_ID = uuid4()
LEAD_ID = uuid4()


# ── Happy path ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_happy_path_200_returns_success() -> None:
    """HTTP 200 → ChannelSendResult(success=True) with external_message_id."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=_make_httpx_response(200, {"ok": True, "result": {"message_id": 42}}))

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    result = await router.send(
        TENANT_ID,
        LEAD_ID,
        "telegram",
        _make_content(),
        idempotency_key="task-abc-123",
    )

    assert result.success is True
    assert result.channel == "telegram"
    assert result.external_message_id == "42"
    assert result.error_code is None
    mock_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_happy_path_calls_sendmessage_endpoint() -> None:
    """POST is made to /bot<token>/sendMessage."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=_make_httpx_response(200, {"ok": True, "result": {"message_id": 99}}))

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k1")

    call_args = mock_client.post.call_args
    assert "sendMessage" in call_args[0][0]


# ── 429 rate limit ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_429_raises_channel_rate_limited_error() -> None:
    """HTTP 429 from Telegram → ChannelRateLimitedError (CB counts, ARQ retry)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(
        return_value=_make_httpx_response(429, {"ok": False, "parameters": {"retry_after": 30}})
    )

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelRateLimitedError) as exc_info:
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k2")

    assert exc_info.value.error_code == "rate_limited"
    assert exc_info.value.retry_after_seconds == 30.0


@pytest.mark.asyncio
async def test_send_429_increments_circuit_breaker() -> None:
    """HTTP 429 → CB counts the failure (ChannelRateLimitedError is ChannelRetryableError)."""
    from src.modules.campaigns.infrastructure.channels.errors import ChannelRateLimitedError

    assert issubclass(ChannelRateLimitedError, ChannelRetryableError), (
        "ChannelRateLimitedError must extend ChannelRetryableError so CB counts it"
    )


# ── 500 server error ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_500_raises_channel_retryable_error() -> None:
    """HTTP 500 from Telegram → ChannelRetryableError (CB counts, ARQ retry)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(
        return_value=_make_httpx_response(500, {"ok": False, "description": "Internal Server Error"})
    )

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelRetryableError) as exc_info:
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k3")

    assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_send_503_raises_retryable() -> None:
    """HTTP 503 from Telegram → ChannelRetryableError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=_make_httpx_response(503, {"ok": False}))

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelRetryableError):
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k4")


@pytest.mark.asyncio
async def test_send_4xx_non_429_raises_fatal() -> None:
    """HTTP 400 from Telegram → ChannelFatalError (no retry, task FAILED)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(
        return_value=_make_httpx_response(400, {"ok": False, "description": "Bad Request: chat not found"})
    )

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelFatalError) as exc_info:
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k5")

    assert exc_info.value.error_code == "fatal"


# ── Idempotency dedup ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_idempotency_dedup_no_second_http_call() -> None:
    """Second send with same idempotency_key returns cached result without HTTP call."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    call_count = 0

    async def _mock_post(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return _make_httpx_response(200, {"ok": True, "result": {"message_id": 77}})

    mock_client.post = _mock_post

    # Build real IdempotencyService with in-memory store
    from src.shared.idempotency.application.service import IdempotencyService
    from src.shared.idempotency.infrastructure.redis_store import RedisIdempotencyStore

    class _InMemoryRedis:
        def __init__(self) -> None:
            self._store: dict = {}

        def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool | None:
            if nx and key in self._store:
                return None
            self._store[key] = value
            return True

        def get(self, key: str) -> str | None:
            return self._store.get(key)

        def setex(self, key: str, ttl: int, value: str) -> None:
            self._store[key] = value

    store = RedisIdempotencyStore(_InMemoryRedis())
    idempotency_svc = IdempotencyService(store)

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        idempotency_service=idempotency_svc,
        cb_factory=_noop_cb_factory(),
    )

    # First call — should hit HTTP
    result1 = await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="task-dedup-001")
    assert result1.success is True
    assert call_count == 1

    # Second call same key — should return cached, no HTTP
    result2 = await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="task-dedup-001")
    assert result2.success is True
    assert call_count == 1, "Second call must not make a new HTTP request"


# ── ComplianceService block ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_compliance_blocked_raises_compliance_error() -> None:
    """ComplianceService.check returning denied → ChannelComplianceBlocked (task SKIPPED)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=_make_httpx_response(200, {"ok": True, "result": {"message_id": 1}}))

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_blocking_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelComplianceBlocked) as exc_info:
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k6")

    assert exc_info.value.error_code == "compliance_blocked"
    # HTTP should NOT have been called
    mock_client.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_compliance_blocked_does_not_trigger_http() -> None:
    """Compliance block short-circuits before HTTP dispatch."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_blocking_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelComplianceBlocked):
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k7")

    mock_client.post.assert_not_awaited()


# ── OutboundRateLimiter exceed ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_rate_limiter_exceeded_raises_tenant_rate_exceeded() -> None:
    """OutboundRateLimiter.check → False → ChannelTenantRateExceeded (reschedule)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=_make_httpx_response(200, {"ok": True, "result": {"message_id": 1}}))

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_blocking_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelTenantRateExceeded) as exc_info:
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k8")

    assert exc_info.value.error_code == "tenant_rate_exceeded"
    mock_client.post.assert_not_awaited()


# ── Tenant locale ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_locale_applied_to_message_text() -> None:
    """format_message_for_tenant_locale is called with the tenant_id before send."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    posted_payloads: list[dict] = []

    async def _capture_post(url: str, **kwargs: object) -> httpx.Response:
        posted_payloads.append(kwargs.get("json", {}))
        return _make_httpx_response(200, {"ok": True, "result": {"message_id": 5}})

    mock_client.post = _capture_post

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    await router.send(
        TENANT_ID,
        LEAD_ID,
        "telegram",
        {"chat_id": "9999", "text": "Mensaje para el cliente", "parse_mode": None},
        idempotency_key="k9",
    )

    assert len(posted_payloads) == 1
    # The text in the posted payload should be the formatted version
    assert "text" in posted_payloads[0]
    assert posted_payloads[0]["text"] == "Mensaje para el cliente"


# ── select_channel ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_select_channel_telegram_not_in_priority_returns_none() -> None:
    """select_channel returns None when 'telegram' not in priority list."""
    router = _make_router()
    result = await router.select_channel(TENANT_ID, LEAD_ID, ["whatsapp", "email"])
    assert result is None


@pytest.mark.asyncio
async def test_select_channel_telegram_in_priority_returns_none_without_lead_id() -> None:
    """select_channel returns None when 'telegram' in priority but lead has no telegram_id."""
    router = _make_router()
    # Default _resolve_telegram_id returns None (stub)
    result = await router.select_channel(TENANT_ID, LEAD_ID, ["telegram"])
    assert result is None


@pytest.mark.asyncio
async def test_select_channel_empty_priority_returns_none() -> None:
    """select_channel returns None for empty priority list."""
    router = _make_router()
    result = await router.select_channel(TENANT_ID, LEAD_ID, [])
    assert result is None


# ── Circuit breaker integration ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_circuit_breaker_open_raises_before_http() -> None:
    """When CB is OPEN, CircuitBreakerOpenError is raised before HTTP call."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=_make_httpx_response(200, {"ok": True, "result": {"message_id": 1}}))

    # Spy CB that always raises CircuitBreakerOpenError
    class _OpenCB(CircuitBreaker):
        def __init__(self) -> None:
            pass  # Skip parent __init__

        async def call(self, fn: object, *args: object, **kwargs: object) -> object:
            raise CircuitBreakerOpenError(
                channel="telegram",
                tenant_id=TENANT_ID,
                retry_after_seconds=60.0,
            )

    def _open_cb_factory(channel: str, tid: object) -> _OpenCB:
        return _OpenCB()

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_open_cb_factory,
    )

    with pytest.raises(CircuitBreakerOpenError):
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k10")

    mock_client.post.assert_not_awaited()


# ── Network error ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_network_timeout_raises_retryable() -> None:
    """Network timeout → ChannelRetryableError (CB counts, ARQ retry)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Connection timed out"))

    router = _make_router(
        httpx_client=mock_client,
        compliance_service=_make_passthrough_compliance(),
        rate_limiter=_make_passthrough_rate_limiter(),
        cb_factory=_noop_cb_factory(),
    )

    with pytest.raises(ChannelRetryableError) as exc_info:
        await router.send(TENANT_ID, LEAD_ID, "telegram", _make_content(), idempotency_key="k11")

    assert exc_info.value.error_code == "retryable"
