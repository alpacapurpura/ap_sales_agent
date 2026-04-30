"""Tests for AuditLogRepositoryImpl.

TDD RED → GREEN: audit log repo SQLA 2.0 async.
Covers: INSERT + tenant-scoped query + purge older-than.

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.modules.campaigns.domain.audit_log import AuditEventType, AuditLogEvent
from src.modules.campaigns.infrastructure.repositories.audit_log_repo_impl import (
    AuditLogRepositoryImpl,
)
from src.shared.domain.base_entity import Base

# ── Async SQLite in-memory engine ─────────────────────────────────────────────


@pytest.fixture(scope="module")
async def async_engine():
    """Async SQLite in-memory engine with all campaign models registered."""
    # Ensure CampaignAuditModel is registered
    from src.modules.campaigns.infrastructure.models.campaign_audit_model import CampaignAuditModel

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Async session with rollback isolation."""
    factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_event(
    tenant_id=None,
    campaign_id=None,
    campaign_task_id=None,
    event_type=AuditEventType.CAMPAIGN_LAUNCHED,
    actor="orchestrator",
    payload=None,
    created_at=None,
) -> AuditLogEvent:
    return AuditLogEvent(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        campaign_id=campaign_id,
        campaign_task_id=campaign_task_id,
        event_type=event_type,
        actor=actor,
        payload=payload or {},
        created_at=created_at or dt.datetime.now(dt.timezone.utc),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_append_and_list_by_campaign(async_session: AsyncSession) -> None:
    """append() persists; list_by_campaign() returns tenant-scoped events."""
    repo = AuditLogRepositoryImpl()
    tenant_id = uuid4()
    campaign_id = uuid4()
    other_tenant_campaign_id = uuid4()

    evt1 = _make_event(tenant_id=tenant_id, campaign_id=campaign_id, event_type=AuditEventType.CAMPAIGN_LAUNCHED)
    evt2 = _make_event(tenant_id=tenant_id, campaign_id=campaign_id, event_type=AuditEventType.TASKS_GENERATED)
    # Different tenant — MUST NOT appear in results
    evt_other = _make_event(tenant_id=uuid4(), campaign_id=other_tenant_campaign_id)

    await repo.append(evt1, session=async_session)
    await repo.append(evt2, session=async_session)
    await repo.append(evt_other, session=async_session)
    await async_session.flush()

    results = await repo.list_by_campaign(campaign_id, tenant_id, session=async_session)
    assert len(results) == 2
    result_ids = {r.id for r in results}
    assert evt1.id in result_ids
    assert evt2.id in result_ids
    assert evt_other.id not in result_ids


@pytest.mark.asyncio
async def test_list_by_campaign_tenant_isolation(async_session: AsyncSession) -> None:
    """list_by_campaign must filter by both campaign_id and tenant_id."""
    repo = AuditLogRepositoryImpl()
    campaign_id = uuid4()
    tenant_a = uuid4()
    tenant_b = uuid4()

    evt_a = _make_event(tenant_id=tenant_a, campaign_id=campaign_id)
    evt_b = _make_event(tenant_id=tenant_b, campaign_id=campaign_id)

    await repo.append(evt_a, session=async_session)
    await repo.append(evt_b, session=async_session)
    await async_session.flush()

    results_a = await repo.list_by_campaign(campaign_id, tenant_a, session=async_session)
    assert len(results_a) == 1
    assert results_a[0].id == evt_a.id

    results_b = await repo.list_by_campaign(campaign_id, tenant_b, session=async_session)
    assert len(results_b) == 1
    assert results_b[0].id == evt_b.id


@pytest.mark.asyncio
async def test_purge_older_than_removes_stale_rows(async_session: AsyncSession) -> None:
    """purge_older_than removes rows with created_at < cutoff."""
    repo = AuditLogRepositoryImpl()
    tenant_id = uuid4()
    campaign_id = uuid4()

    old_ts = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=100)
    fresh_ts = dt.datetime.now(dt.timezone.utc)

    old_evt = _make_event(tenant_id=tenant_id, campaign_id=campaign_id, created_at=old_ts)
    fresh_evt = _make_event(tenant_id=tenant_id, campaign_id=campaign_id, created_at=fresh_ts)

    await repo.append(old_evt, session=async_session)
    await repo.append(fresh_evt, session=async_session)
    await async_session.flush()

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)
    deleted = await repo.purge_older_than(cutoff=cutoff, batch_size=100, session=async_session)
    await async_session.flush()

    assert deleted == 1

    results = await repo.list_by_campaign(campaign_id, tenant_id, session=async_session)
    assert len(results) == 1
    assert results[0].id == fresh_evt.id


@pytest.mark.asyncio
async def test_purge_older_than_idempotent(async_session: AsyncSession) -> None:
    """Running purge_older_than twice on already-purged rows returns 0."""
    repo = AuditLogRepositoryImpl()
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)

    deleted_second_run = await repo.purge_older_than(cutoff=cutoff, batch_size=100, session=async_session)
    assert deleted_second_run == 0


@pytest.mark.asyncio
async def test_append_sanitizes_pii_in_payload(async_session: AsyncSession) -> None:
    """append() applies sanitize_payload before persisting (PII redaction)."""
    repo = AuditLogRepositoryImpl()
    tenant_id = uuid4()
    campaign_id = uuid4()

    # Payload containing a PII email
    pii_payload = {"message": "Contact user@example.com for details", "lead_id": str(uuid4())}
    evt = _make_event(tenant_id=tenant_id, campaign_id=campaign_id, payload=pii_payload)

    await repo.append(evt, session=async_session)
    await async_session.flush()

    results = await repo.list_by_campaign(campaign_id, tenant_id, session=async_session)
    assert len(results) == 1
    # Email should be redacted in stored payload
    stored_message = results[0].payload.get("message", "")
    assert "user@example.com" not in stored_message
