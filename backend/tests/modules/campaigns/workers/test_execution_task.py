"""Unit tests for run_campaign_execution_task ARQ worker.

TDD RED → GREEN. No Postgres — uses AsyncMock repos + fake channel router.

Cases:
- happy: task sent, status='sent', external_id returned
- circuit_open: CircuitBreakerOpenError → mark_failed + no ARQ re-raise
- rate_limited: ChannelRateLimitedError → re-raised (ARQ retries)
- compliance_blocked: mark_skipped, no re-raise
- transient: ChannelRetryableError → re-raised (ARQ retries)
- task not found: noop dict returned
- task already processed (noop idempotency)
- unregistered channel: mark_failed + no re-raise
- SKIP LOCKED semantics: second worker sees noop for already-sent task

Patching strategy: imports inside _process_task() are local-scope, so patch
the definition module (where the class is defined). Python re-binds the name
when the function executes its local import; patching the definition module
means the patched class is what the local import finds.

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from luana_core_campaigns.domain.enums import TaskStatus
from luana_core_campaigns.infrastructure.channels.errors import (
    ChannelComplianceBlocked,
    ChannelFatalError,
    ChannelRateLimitedError,
    ChannelRetryableError,
    ChannelTenantRateExceeded,
)
from luana_core_campaigns.infrastructure.resilience.errors import CircuitBreakerOpenError
from luana_core_campaigns.workers.execution_task import run_campaign_execution_task

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid4()
CAMPAIGN_ID = uuid4()
LEAD_ID = uuid4()
NOW = dt.datetime.now(tz=dt.timezone.utc)

# Patch targets — the definition module (since imports are local in _process_task)
_TASK_REPO_PATH = (
    "luana_core_campaigns.infrastructure.repositories.campaign_task_repository_impl.CampaignTaskRepositoryImpl"
)
_STEP_REPO_PATH = (
    "luana_core_campaigns.infrastructure.repositories.campaign_step_repository_impl.CampaignStepRepositoryImpl"
)
_AUDIT_SVC_PATH = "luana_core_campaigns.application.services.audit_log_service.AuditLogService"
_AUDIT_REPO_PATH = "luana_core_campaigns.infrastructure.repositories.audit_log_repo_impl.AuditLogRepositoryImpl"


# ── Fake channel router ───────────────────────────────────────────────────────


class _FakeChannelRouter:
    """Minimal ChannelRouter fake satisfying the Protocol."""

    def __init__(self, *, side_effect=None, external_message_id: str = "TG123") -> None:
        self._side_effect = side_effect
        self._external_message_id = external_message_id
        self.send_calls: list = []

    async def send(self, tenant_id, lead_id, channel, content, *, idempotency_key=""):
        self.send_calls.append((tenant_id, lead_id, channel, content, idempotency_key))
        if self._side_effect is not None:
            raise self._side_effect
        result = MagicMock()
        result.external_message_id = self._external_message_id
        return result

    def select_channel(self, channel_priority):
        return channel_priority[0] if channel_priority else "telegram"


# ── Fake DB row ───────────────────────────────────────────────────────────────


def _make_task_row(
    task_id: UUID | None = None,
    *,
    status: str = "pending",
    step_id: UUID | None = None,
    external_message_id: str | None = None,
) -> MagicMock:
    """Return a mock CampaignTaskModel row."""
    row = MagicMock()
    row.id = task_id or uuid4()
    row.tenant_id = TENANT_ID
    row.campaign_id = CAMPAIGN_ID
    row.lead_id = LEAD_ID
    row.step_id = step_id
    row.status = status
    row.external_message_id = external_message_id
    return row


# ── ARQ context + session factories ───────────────────────────────────────────


def _make_session_with_row(row) -> AsyncMock:
    """Return an AsyncMock that satisfies isinstance(session, AsyncSession)."""
    session = AsyncMock(spec=AsyncSession)
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = row
    session.execute = AsyncMock(return_value=result_mock)

    @asynccontextmanager
    async def _begin():
        yield

    session.begin = MagicMock(return_value=_begin())
    return session


def _make_arq_ctx(session: AsyncMock) -> dict:
    """Build minimal ARQ ctx dict with a db_factory pointing to a fake session."""

    @asynccontextmanager
    async def _db_factory():
        yield session

    return {
        "db_factory": _db_factory,
        "redis_cache": AsyncMock(),
    }


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_channel_registry():
    """Ensure channel registry is clean between tests."""
    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    yield
    ChannelRouterRegistry().reset()


# ── Shared patch context manager ──────────────────────────────────────────────


def _patch_repos(
    task_repo_mock: AsyncMock | None = None,
    step_repo_mock: AsyncMock | None = None,
    audit_svc_mock: AsyncMock | None = None,
):
    """Return a context manager that patches all four inner imports."""
    patches = [
        patch(_TASK_REPO_PATH, return_value=task_repo_mock or AsyncMock()),
        patch(_STEP_REPO_PATH, return_value=step_repo_mock or AsyncMock()),
        patch(_AUDIT_SVC_PATH, return_value=audit_svc_mock or AsyncMock()),
        patch(_AUDIT_REPO_PATH, return_value=AsyncMock()),
    ]

    class _MultiPatch:
        def __enter__(self):
            self._active = [p.__enter__() for p in patches]
            return self._active

        def __exit__(self, *args):
            for p in reversed(patches):
                p.__exit__(*args)

    return _MultiPatch()


# ── Tests: happy path ─────────────────────────────────────────────────────────


async def test_happy_path_marks_sent_and_returns_sent_status() -> None:
    """Task pending + send success → status='sent', external_id returned."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter(external_message_id="TG999")
    row = _make_task_row(task_id, status="pending")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    task_repo_mock = AsyncMock()
    with _patch_repos(task_repo_mock=task_repo_mock):
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "sent"
    assert result["external_id"] == "TG999"
    assert result["id"] == str(task_id)
    task_repo_mock.mark_sent.assert_awaited_once()


async def test_happy_path_scheduled_status_also_processed() -> None:
    """Task with status='scheduled' is also processed (not just 'pending')."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter(external_message_id="TGSCHED")
    row = _make_task_row(task_id, status="scheduled")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    task_repo_mock = AsyncMock()
    with _patch_repos(task_repo_mock=task_repo_mock):
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "sent"
    task_repo_mock.mark_sent.assert_awaited_once()


# ── Tests: circuit breaker open ───────────────────────────────────────────────


async def test_circuit_open_marks_failed_no_reraised() -> None:
    """CircuitBreakerOpenError → mark_failed, status='failed', no ARQ re-raise."""
    task_id = uuid4()
    exc = CircuitBreakerOpenError(channel="telegram", tenant_id=TENANT_ID, retry_after_seconds=30.0)
    fake_router = _FakeChannelRouter(side_effect=exc)
    row = _make_task_row(task_id, status="pending")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    task_repo_mock = AsyncMock()
    with _patch_repos(task_repo_mock=task_repo_mock):
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        # Must NOT raise — worker catches CircuitBreakerOpenError
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "failed"
    task_repo_mock.mark_failed.assert_awaited_once()
    call_kwargs = task_repo_mock.mark_failed.call_args
    assert call_kwargs.kwargs.get("error_code") == "circuit_open"


# ── Tests: rate limited (ARQ retries) ─────────────────────────────────────────


async def test_rate_limited_error_is_reraised_for_arq_retry() -> None:
    """ChannelRateLimitedError re-raises so ARQ applies exponential backoff."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter(side_effect=ChannelRateLimitedError("429"))
    row = _make_task_row(task_id, status="pending")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    with _patch_repos():
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        with pytest.raises(ChannelRateLimitedError):
            await run_campaign_execution_task(ctx, str(task_id))


async def test_retryable_error_is_reraised_for_arq_retry() -> None:
    """ChannelRetryableError re-raises so ARQ applies exponential backoff."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter(side_effect=ChannelRetryableError("5xx"))
    row = _make_task_row(task_id, status="pending")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    with _patch_repos():
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        with pytest.raises(ChannelRetryableError):
            await run_campaign_execution_task(ctx, str(task_id))


# ── Tests: compliance blocked ─────────────────────────────────────────────────


async def test_compliance_blocked_marks_skipped_no_reraised() -> None:
    """ChannelComplianceBlocked → mark_skipped, status='skipped', no re-raise."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter(side_effect=ChannelComplianceBlocked("opt-out"))
    row = _make_task_row(task_id, status="pending")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    task_repo_mock = AsyncMock()
    with _patch_repos(task_repo_mock=task_repo_mock):
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "skipped"
    task_repo_mock.mark_skipped.assert_awaited_once()


# ── Tests: tenant rate exceeded ────────────────────────────────────────────────


async def test_tenant_rate_exceeded_marks_failed_no_cb_reraised() -> None:
    """ChannelTenantRateExceeded → mark_failed (tenant gate), status='pending', no re-raise."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter(side_effect=ChannelTenantRateExceeded("rate exceeded"))
    row = _make_task_row(task_id, status="pending")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    task_repo_mock = AsyncMock()
    with _patch_repos(task_repo_mock=task_repo_mock):
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "pending"
    task_repo_mock.mark_failed.assert_awaited_once()


# ── Tests: fatal error ────────────────────────────────────────────────────────


async def test_fatal_error_marks_failed_no_reraised() -> None:
    """ChannelFatalError → mark_failed, status='failed', no re-raise."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter(side_effect=ChannelFatalError("user blocked bot"))
    row = _make_task_row(task_id, status="pending")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    task_repo_mock = AsyncMock()
    with _patch_repos(task_repo_mock=task_repo_mock):
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "failed"
    task_repo_mock.mark_failed.assert_awaited_once()


# ── Tests: task not found ─────────────────────────────────────────────────────


async def test_task_not_found_returns_not_found_dict() -> None:
    """SELECT returns None → noop {'status': 'not_found'}."""
    task_id = uuid4()

    with _patch_repos():
        session = _make_session_with_row(None)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "not_found"
    assert result["id"] == str(task_id)


# ── Tests: SKIP LOCKED idempotency (already processed) ────────────────────────


@pytest.mark.parametrize(
    "already_status",
    ["sent", "failed", "skipped"],
)
async def test_already_processed_task_is_noop(already_status: str) -> None:
    """If status != pending/scheduled → noop, no send call, status returned unchanged."""
    task_id = uuid4()
    fake_router = _FakeChannelRouter()  # should NOT be called
    row = _make_task_row(task_id, status=already_status, external_message_id="EXT123")

    from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().register("telegram", fake_router)  # type: ignore[arg-type]

    with _patch_repos():
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    # No send called — SKIP LOCKED semantics (second parallel worker noop)
    assert len(fake_router.send_calls) == 0
    # Returns the current status of the row
    assert result["status"] == already_status


# ── Tests: unregistered channel ────────────────────────────────────────────────


async def test_unregistered_channel_marks_failed() -> None:
    """Channel not in registry → mark_failed error_code=unregistered_channel."""
    task_id = uuid4()
    step_id = uuid4()

    step_mock = MagicMock()
    step_mock.channel_priority = ["whatsapp"]  # not registered
    step_mock.step_config = {}

    row = _make_task_row(task_id, status="pending", step_id=step_id)

    step_repo_mock = AsyncMock()
    step_repo_mock.get_by_id = AsyncMock(return_value=step_mock)
    task_repo_mock = AsyncMock()

    with _patch_repos(task_repo_mock=task_repo_mock, step_repo_mock=step_repo_mock):
        session = _make_session_with_row(row)
        ctx = _make_arq_ctx(session)
        result = await run_campaign_execution_task(ctx, str(task_id))

    assert result["status"] == "failed"
    task_repo_mock.mark_failed.assert_awaited_once()
    call_kwargs = task_repo_mock.mark_failed.call_args
    assert call_kwargs.kwargs.get("error_code") == "unregistered_channel"
