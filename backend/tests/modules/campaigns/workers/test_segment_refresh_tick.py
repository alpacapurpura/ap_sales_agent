"""Unit tests for run_segment_refresh_tick ARQ worker.

TDD RED → GREEN. No Postgres — mocked segment service + fake DB factory.

Cases:
- STATIC segment linked to RUNNING campaign: snapshot called
- DYNAMIC segment: not in stale-query results (filtered at SQL level); no snapshot
- Recent segment (last_calculated_at fresh): not in stale-query results; no snapshot
- Single segment failure does not block others
- Returns correct refreshed/errors counts

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

import pytest

from src.modules.campaigns.workers.segment_refresh_tick import run_segment_refresh_tick

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid4()
NOW = dt.datetime.now(tz=dt.timezone.utc)


# ── Helpers ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def _null_session():
    """Fake db_factory context manager yielding an AsyncMock session."""
    yield AsyncMock(spec=AsyncSession)


def _make_arq_ctx(stale_segments: list[tuple]) -> dict:
    """Build ARQ ctx with db_factory yielding an in-memory session."""
    call_count = 0

    @asynccontextmanager
    async def _db_factory():
        nonlocal call_count
        call_count += 1
        yield AsyncMock(spec=AsyncSession)

    ctx = {"db_factory": _db_factory}
    ctx["_stale_segments"] = stale_segments  # stored for assertion convenience
    return ctx


# ── Tests: STATIC segment in RUNNING campaign → refresh ───────────────────────


async def test_static_segment_running_campaign_gets_snapshot() -> None:
    """STATIC segment linked to RUNNING campaign with stale ts → snapshot called."""
    tenant_id = uuid4()
    segment_id = uuid4()

    segment_svc_mock = AsyncMock()
    segment_svc_mock.snapshot = AsyncMock()

    stale_pairs = [(tenant_id, segment_id)]

    with (
        patch(
            "src.modules.campaigns.workers.segment_refresh_tick._query_stale_segments",
            new=AsyncMock(return_value=stale_pairs),
        ),
        patch(
            "src.modules.campaigns.workers.segment_refresh_tick._build_segment_service_standalone",
            return_value=segment_svc_mock,
        ),
    ):

        @asynccontextmanager
        async def _db_factory():
            yield AsyncMock(spec=AsyncSession)

        ctx = {"db_factory": _db_factory}
        result = await run_segment_refresh_tick(ctx)

    assert result["refreshed"] == 1
    assert result["errors"] == 0
    # Verify positional args (tenant_id, segment_id); session= is an AsyncMock, just check call count
    assert segment_svc_mock.snapshot.await_count == 1
    call_args = segment_svc_mock.snapshot.call_args
    assert call_args.args[0] == tenant_id
    assert call_args.args[1] == segment_id


async def test_multiple_static_segments_all_refreshed() -> None:
    """Multiple STATIC segments each get their own snapshot call."""
    pairs = [(uuid4(), uuid4()) for _ in range(3)]
    segment_svc_mock = AsyncMock()
    segment_svc_mock.snapshot = AsyncMock()

    with (
        patch(
            "src.modules.campaigns.workers.segment_refresh_tick._query_stale_segments",
            new=AsyncMock(return_value=pairs),
        ),
        patch(
            "src.modules.campaigns.workers.segment_refresh_tick._build_segment_service_standalone",
            return_value=segment_svc_mock,
        ),
    ):

        @asynccontextmanager
        async def _db_factory():
            yield AsyncMock(spec=AsyncSession)

        ctx = {"db_factory": _db_factory}
        result = await run_segment_refresh_tick(ctx)

    assert result["refreshed"] == 3
    assert result["errors"] == 0
    assert segment_svc_mock.snapshot.await_count == 3


# ── Tests: DYNAMIC segment / recent → not in query results ────────────────────


async def test_no_stale_segments_returns_zero_refreshed() -> None:
    """No stale STATIC+RUNNING combinations → refreshed=0, errors=0."""
    with (
        patch(
            "src.modules.campaigns.workers.segment_refresh_tick._query_stale_segments",
            new=AsyncMock(return_value=[]),  # query returned empty
        ),
    ):

        @asynccontextmanager
        async def _db_factory():
            yield AsyncMock(spec=AsyncSession)

        ctx = {"db_factory": _db_factory}
        result = await run_segment_refresh_tick(ctx)

    assert result["refreshed"] == 0
    assert result["errors"] == 0


# ── Tests: per-segment error isolation ────────────────────────────────────────


async def test_single_segment_error_does_not_block_others() -> None:
    """One segment failing does not prevent others from refreshing."""
    pairs = [(uuid4(), uuid4()) for _ in range(3)]

    call_count = 0

    async def _snapshot_with_error(tenant_id, segment_id, *, session):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            msg = "segment refresh failed"
            raise RuntimeError(msg)

    segment_svc_mock = AsyncMock()
    segment_svc_mock.snapshot = AsyncMock(side_effect=_snapshot_with_error)

    with (
        patch(
            "src.modules.campaigns.workers.segment_refresh_tick._query_stale_segments",
            new=AsyncMock(return_value=pairs),
        ),
        patch(
            "src.modules.campaigns.workers.segment_refresh_tick._build_segment_service_standalone",
            return_value=segment_svc_mock,
        ),
    ):

        @asynccontextmanager
        async def _db_factory():
            yield AsyncMock(spec=AsyncSession)

        ctx = {"db_factory": _db_factory}
        result = await run_segment_refresh_tick(ctx)

    # 2 succeed, 1 fails
    assert result["refreshed"] == 2
    assert result["errors"] == 1


# ── Tests: env tuning ────────────────────────────────────────────────────────


async def test_env_override_changes_refresh_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    """CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS env overrides 60-minute default."""
    monkeypatch.setenv("CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS", "2")

    from src.modules.campaigns.workers.segment_refresh_tick import _refresh_threshold_minutes

    assert _refresh_threshold_minutes() == 120


async def test_env_default_refresh_threshold_is_60_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default refresh interval is 60 minutes (1 hour)."""
    monkeypatch.delenv("CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS", raising=False)

    from src.modules.campaigns.workers.segment_refresh_tick import _refresh_threshold_minutes

    assert _refresh_threshold_minutes() == 60
