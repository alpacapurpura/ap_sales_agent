"""Unit tests for purge_old_campaigns_audit ARQ worker.

TDD RED → GREEN. Uses async SQLite in-memory DB — real AuditLogRepositoryImpl.

Cases:
- Rows older than retention window are hard-deleted
- Rows within retention window are preserved
- Idempotent: second run deletes 0 rows
- Env override changes retention days
- Safety clamp: retention_days < 7 → 7; > 365 → 365

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from luana_core_campaigns.domain.audit_log import AuditEventType, AuditLogEvent
from luana_core_campaigns.infrastructure.repositories.audit_log_repo_impl import (
    AuditLogRepositoryImpl,
)
from luana_core_campaigns.workers.audit_retention_task import (
    CAMPAIGNS_AUDIT_RETENTION_DAYS,
    _retention_days,
    purge_old_campaigns_audit,
)
from luana_core_platform.domain.base_entity import Base

pytestmark = pytest.mark.asyncio


# ── SQLite in-memory engine ───────────────────────────────────────────────────


@pytest.fixture(scope="module")
async def async_engine():
    """Module-scoped async SQLite engine with audit + campaign models registered."""
    # Ensure models are loaded into metadata
    from luana_core_campaigns.infrastructure.models.campaign_audit_model import CampaignAuditModel

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Per-test session with rollback isolation."""
    factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_audit_event(
    *,
    created_at: dt.datetime,
    tenant_id=None,
    campaign_id=None,
) -> AuditLogEvent:
    return AuditLogEvent(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        campaign_id=campaign_id or uuid4(),
        campaign_task_id=None,
        event_type=AuditEventType.CAMPAIGN_LAUNCHED,
        actor="test",
        payload={},
        created_at=created_at,
    )


def _make_arq_ctx(session_factory) -> dict:
    """Build ARQ ctx with a db_factory that yields the given session."""

    @asynccontextmanager
    async def _db_factory():
        async with session_factory() as session:
            yield session

    return {"db_factory": _db_factory}


# ── Tests: deletion ───────────────────────────────────────────────────────────


async def test_rows_older_than_retention_are_deleted(async_engine) -> None:
    """Rows with created_at < cutoff are hard-deleted."""
    factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    repo = AuditLogRepositoryImpl()

    now = dt.datetime.now(tz=dt.timezone.utc)
    old_ts = now - dt.timedelta(days=100)
    fresh_ts = now - dt.timedelta(days=10)

    old_evt = _make_audit_event(created_at=old_ts)
    fresh_evt = _make_audit_event(created_at=fresh_ts)

    # Seed rows
    async with factory() as session:
        await repo.append(old_evt, session=session)
        await repo.append(fresh_evt, session=session)
        await session.commit()

    ctx = _make_arq_ctx(factory)

    with (
        # Force 30-day retention so old_ts (100d ago) is deleted; fresh_ts (10d ago) preserved
        __import__("unittest.mock", fromlist=["patch"]).patch.dict(os.environ, {CAMPAIGNS_AUDIT_RETENTION_DAYS: "30"}),
    ):
        result = await purge_old_campaigns_audit(ctx)

    assert result["deleted"] >= 1

    # Verify fresh row still exists
    from sqlalchemy import select
    from luana_core_campaigns.infrastructure.models.campaign_audit_model import CampaignAuditModel

    async with factory() as session:
        stmt = select(CampaignAuditModel).where(CampaignAuditModel.id == fresh_evt.id)
        res = await session.execute(stmt)
        found = res.scalar_one_or_none()
    assert found is not None


async def test_rows_within_retention_are_preserved(async_engine) -> None:
    """Rows with created_at >= cutoff are NOT deleted."""
    factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    repo = AuditLogRepositoryImpl()

    now = dt.datetime.now(tz=dt.timezone.utc)
    recent_ts = now - dt.timedelta(days=5)  # well within 30d retention

    recent_evt = _make_audit_event(created_at=recent_ts)

    async with factory() as session:
        await repo.append(recent_evt, session=session)
        await session.commit()

    ctx = _make_arq_ctx(factory)

    with (
        __import__("unittest.mock", fromlist=["patch"]).patch.dict(os.environ, {CAMPAIGNS_AUDIT_RETENTION_DAYS: "30"}),
    ):
        await purge_old_campaigns_audit(ctx)

    # recent row still present
    from sqlalchemy import select
    from luana_core_campaigns.infrastructure.models.campaign_audit_model import CampaignAuditModel

    async with factory() as session:
        stmt = select(CampaignAuditModel).where(CampaignAuditModel.id == recent_evt.id)
        res = await session.execute(stmt)
        found = res.scalar_one_or_none()
    assert found is not None


async def test_idempotent_second_run_deletes_zero(async_engine) -> None:
    """Running purge twice: second run deletes 0 rows (no stale rows left)."""
    factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    ctx = _make_arq_ctx(factory)

    # No stale rows inserted — both runs should return 0 deleted
    with (
        __import__("unittest.mock", fromlist=["patch"]).patch.dict(os.environ, {CAMPAIGNS_AUDIT_RETENTION_DAYS: "30"}),
    ):
        await purge_old_campaigns_audit(ctx)
        r2 = await purge_old_campaigns_audit(ctx)

    # idempotent: second run deletes nothing new
    assert r2["deleted"] == 0
    assert r2["batches"] == 0


# ── Tests: env override ───────────────────────────────────────────────────────


def test_retention_days_default_is_90(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default retention days is 90 when env is unset."""
    monkeypatch.delenv(CAMPAIGNS_AUDIT_RETENTION_DAYS, raising=False)
    assert _retention_days() == 90


def test_retention_days_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """CAMPAIGNS_AUDIT_RETENTION_DAYS env overrides default."""
    monkeypatch.setenv(CAMPAIGNS_AUDIT_RETENTION_DAYS, "180")
    assert _retention_days() == 180


def test_retention_days_safety_clamp_min(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retention days < 7 clamped to 7."""
    monkeypatch.setenv(CAMPAIGNS_AUDIT_RETENTION_DAYS, "3")
    assert _retention_days() == 7


def test_retention_days_safety_clamp_max(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retention days > 365 clamped to 365."""
    monkeypatch.setenv(CAMPAIGNS_AUDIT_RETENTION_DAYS, "999")
    assert _retention_days() == 365
