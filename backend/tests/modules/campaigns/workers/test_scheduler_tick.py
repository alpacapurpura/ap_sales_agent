"""Unit tests for run_campaign_scheduler_tick ARQ worker.

TDD RED → GREEN. No Postgres — uses AsyncMock repos + mock orchestrator.

Cases:
- Phase A picks up campaigns with scheduled_at <= now
- Phase A skips campaigns with scheduled_at > now
- Phase A idempotency: same campaign picked up twice → orchestrator called once per tick
- Phase B claims pending tasks and enqueues them
- Heartbeat written to Redis after success

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from luana_core_campaigns.workers.scheduler_tick import run_campaign_scheduler_tick

pytestmark = pytest.mark.asyncio

# Lazy-import path for CampaignTaskRepositoryImpl (never bound at scheduler_tick module level)
_TASK_REPO_PATH = (
    "luana_core_campaigns.infrastructure.repositories.campaign_task_repository_impl.CampaignTaskRepositoryImpl"
)

TENANT_ID = uuid4()
NOW = dt.datetime.now(tz=dt.timezone.utc)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _campaign_row(*, scheduled_at: dt.datetime, status: str = "scheduled") -> MagicMock:
    """Minimal campaign row mock."""
    row = MagicMock()
    row.id = uuid4()
    row.tenant_id = TENANT_ID
    row.status = status
    row.scheduled_at = scheduled_at
    row.deleted_at = None
    return row


def _task_row() -> MagicMock:
    """Minimal task row mock for Phase B."""
    row = MagicMock()
    row.id = uuid4()
    row.tenant_id = TENANT_ID
    return row


def _make_session_returning(rows) -> AsyncMock:
    """AsyncSession (spec) whose execute() returns the given rows on scalars().all()."""
    session = AsyncMock(spec=AsyncSession)
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = rows
    session.execute = AsyncMock(return_value=result_mock)
    return session


def _make_arq_ctx(session: AsyncMock, *, redis_mock=None) -> dict:
    """Build minimal ARQ ctx."""
    arq_mock = AsyncMock()
    arq_mock.enqueue_job = AsyncMock()

    @asynccontextmanager
    async def _db_factory():
        yield session

    return {
        "db_factory": _db_factory,
        "redis_cache": redis_mock or AsyncMock(),
        "redis": arq_mock,  # used by _phase_b_claim_and_enqueue
        "_arq_pool": arq_mock,  # alias
    }


# ── Tests: Phase A promote ────────────────────────────────────────────────────


async def test_phase_a_picks_up_scheduled_campaigns_at_or_before_now() -> None:
    """Campaigns with scheduled_at <= now are promoted via orchestrator.launch."""
    past = NOW - dt.timedelta(minutes=5)
    campaign = _campaign_row(scheduled_at=past)
    session = _make_session_returning([campaign])

    task_repo_mock = AsyncMock()
    task_repo_mock.claim_pending_for_worker = AsyncMock(return_value=[])
    orchestrator_mock = AsyncMock()
    orchestrator_mock.launch = AsyncMock(return_value=MagicMock(tasks_generated=1, status="running"))

    with (
        patch(
            "luana_core_campaigns.workers.scheduler_tick._build_orchestrator_standalone",
            return_value=orchestrator_mock,
        ),
        patch(
            _TASK_REPO_PATH,
            return_value=task_repo_mock,
        ),
    ):
        ctx = _make_arq_ctx(session)
        result = await run_campaign_scheduler_tick(ctx)

    assert result["promoted"] >= 1


async def test_phase_a_skips_campaigns_scheduled_in_future() -> None:
    """Campaigns with scheduled_at > now are NOT promoted."""
    # The query WHERE clause scheduled_at <= now means future campaigns are not returned
    # → executor returns empty list
    session = _make_session_returning([])

    task_repo_mock = AsyncMock()
    task_repo_mock.claim_pending_for_worker = AsyncMock(return_value=[])
    orchestrator_mock = AsyncMock()
    orchestrator_mock.launch = AsyncMock()

    with (
        patch(
            "luana_core_campaigns.workers.scheduler_tick._build_orchestrator_standalone",
            return_value=orchestrator_mock,
        ),
        patch(
            _TASK_REPO_PATH,
            return_value=task_repo_mock,
        ),
    ):
        ctx = _make_arq_ctx(session)
        result = await run_campaign_scheduler_tick(ctx)

    assert result["promoted"] == 0
    orchestrator_mock.launch.assert_not_awaited()


async def test_phase_a_idempotent_single_tick() -> None:
    """Same tick: orchestrator.launch called once per campaign per tick."""
    past = NOW - dt.timedelta(minutes=10)
    campaign = _campaign_row(scheduled_at=past)
    session = _make_session_returning([campaign])  # single campaign returned

    task_repo_mock = AsyncMock()
    task_repo_mock.claim_pending_for_worker = AsyncMock(return_value=[])
    orchestrator_mock = AsyncMock()
    launch_result = MagicMock()
    launch_result.tasks_generated = 2
    launch_result.status = "running"
    orchestrator_mock.launch = AsyncMock(return_value=launch_result)

    with (
        patch(
            "luana_core_campaigns.workers.scheduler_tick._build_orchestrator_standalone",
            return_value=orchestrator_mock,
        ),
        patch(
            _TASK_REPO_PATH,
            return_value=task_repo_mock,
        ),
    ):
        ctx = _make_arq_ctx(session)
        result = await run_campaign_scheduler_tick(ctx)

    # Exactly one launch per campaign row from the query
    assert orchestrator_mock.launch.await_count == 1
    assert result["promoted"] == 1


# ── Tests: Phase B claim + enqueue ────────────────────────────────────────────


async def test_phase_b_enqueues_claimed_tasks() -> None:
    """Phase B claims pending tasks and enqueues each to ARQ."""
    tasks = [_task_row(), _task_row(), _task_row()]
    session = _make_session_returning([])  # Phase A: no campaigns due

    task_repo_mock = AsyncMock()
    task_repo_mock.claim_pending_for_worker = AsyncMock(return_value=tasks)
    orchestrator_mock = AsyncMock()

    with (
        patch(
            "luana_core_campaigns.workers.scheduler_tick._build_orchestrator_standalone",
            return_value=orchestrator_mock,
        ),
        patch(
            _TASK_REPO_PATH,
            return_value=task_repo_mock,
        ),
    ):
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock()
        arq_mock = AsyncMock()
        arq_mock.enqueue_job = AsyncMock()

        @asynccontextmanager
        async def _db_factory():
            yield session

        ctx = {
            "db_factory": _db_factory,
            "redis_cache": redis_mock,
            "redis": arq_mock,
        }
        result = await run_campaign_scheduler_tick(ctx)

    assert result["tasks_enqueued"] == len(tasks)
    assert arq_mock.enqueue_job.await_count == len(tasks)


async def test_phase_b_no_tasks_returns_zero_enqueued() -> None:
    """Phase B with no pending tasks → tasks_enqueued=0."""
    session = _make_session_returning([])

    task_repo_mock = AsyncMock()
    task_repo_mock.claim_pending_for_worker = AsyncMock(return_value=[])
    orchestrator_mock = AsyncMock()

    with (
        patch(
            "luana_core_campaigns.workers.scheduler_tick._build_orchestrator_standalone",
            return_value=orchestrator_mock,
        ),
        patch(
            _TASK_REPO_PATH,
            return_value=task_repo_mock,
        ),
    ):
        arq_mock = AsyncMock()
        arq_mock.enqueue_job = AsyncMock()
        redis_mock = AsyncMock()

        @asynccontextmanager
        async def _db_factory():
            yield session

        ctx = {
            "db_factory": _db_factory,
            "redis_cache": redis_mock,
            "redis": arq_mock,
        }
        result = await run_campaign_scheduler_tick(ctx)

    assert result["tasks_enqueued"] == 0


# ── Tests: heartbeat ─────────────────────────────────────────────────────────


async def test_heartbeat_written_to_redis_after_success() -> None:
    """Redis heartbeat key is set after successful tick."""
    session = _make_session_returning([])

    task_repo_mock = AsyncMock()
    task_repo_mock.claim_pending_for_worker = AsyncMock(return_value=[])
    orchestrator_mock = AsyncMock()

    with (
        patch(
            "luana_core_campaigns.workers.scheduler_tick._build_orchestrator_standalone",
            return_value=orchestrator_mock,
        ),
        patch(
            _TASK_REPO_PATH,
            return_value=task_repo_mock,
        ),
    ):
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock()
        arq_mock = AsyncMock()
        arq_mock.enqueue_job = AsyncMock()

        @asynccontextmanager
        async def _db_factory():
            yield session

        ctx = {
            "db_factory": _db_factory,
            "redis_cache": redis_mock,
            "redis": arq_mock,
        }
        await run_campaign_scheduler_tick(ctx)

    redis_mock.setex.assert_awaited_once_with("campaigns:scheduler:last_tick", 600, "1")
