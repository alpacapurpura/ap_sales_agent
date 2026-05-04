"""
Tests for LeadQueryServiceImpl — async SQL-side filtering.

CRM-07: list_lead_ids_matching (count + capped list), count_leads_matching, tenant isolation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import ColumnElement, true
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.shared.domain.base_entity import Base
from src.shared.infrastructure.models.crm import LeadModel

TENANT_A = uuid.UUID("00000000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


# ---------------------------------------------------------------------------
# Async DB fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield engine


@pytest.fixture()
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_lead(
    tenant_id: uuid.UUID,
    *,
    whatsapp_id: str | None = None,
    last_interaction_date: datetime | None = None,
    temperature: str = "COLD",
) -> LeadModel:
    kwargs: dict = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "fit_score": 0,
        "intent_score": 0,
        "temperature": temperature,
        "is_blacklisted": False,
        "profile_data": {},
        "key_objections_history": [],
    }
    if whatsapp_id:
        kwargs["whatsapp_id"] = whatsapp_id
    if last_interaction_date:
        kwargs["last_interaction_date"] = last_interaction_date
    return LeadModel(**kwargs)


# ---------------------------------------------------------------------------
# list_lead_ids_matching
# ---------------------------------------------------------------------------


class TestListLeadIdsMatching:
    """Returns (lead_ids, total_count) with SQL-side filtering."""

    @pytest.mark.asyncio
    async def test_returns_ids_and_total_count(self, async_session: AsyncSession):
        """Count reflects all matching; list is capped by limit."""
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        leads = [_make_lead(TENANT_A, whatsapp_id=f"wa-{i}") for i in range(5)]
        async_session.add_all(leads)
        await async_session.flush()

        svc = LeadQueryServiceImpl()
        lead_ids, total = await svc.list_lead_ids_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            limit=3,
            session=async_session,
        )

        assert total == 5
        assert len(lead_ids) == 3

    @pytest.mark.asyncio
    async def test_applies_limit(self, async_session: AsyncSession):
        """Limit=1 returns exactly 1 id even if more match."""
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        leads = [_make_lead(TENANT_A, whatsapp_id=f"wa-{i}") for i in range(10)]
        async_session.add_all(leads)
        await async_session.flush()

        svc = LeadQueryServiceImpl()
        lead_ids, total = await svc.list_lead_ids_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            limit=1,
            session=async_session,
        )

        assert total == 10
        assert len(lead_ids) == 1

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, async_session: AsyncSession):
        """Only leads from the requested tenant are returned."""
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        async_session.add_all([_make_lead(TENANT_A, whatsapp_id="wa-a1"), _make_lead(TENANT_A, whatsapp_id="wa-a2")])
        async_session.add_all(
            [
                _make_lead(TENANT_B, whatsapp_id="wa-b1"),
                _make_lead(TENANT_B, whatsapp_id="wa-b2"),
                _make_lead(TENANT_B, whatsapp_id="wa-b3"),
            ]
        )
        await async_session.flush()

        svc = LeadQueryServiceImpl()
        lead_ids, total = await svc.list_lead_ids_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            limit=10,
            session=async_session,
        )

        assert total == 2
        assert len(lead_ids) == 2

    @pytest.mark.asyncio
    async def test_excludes_deleted_leads(self, async_session: AsyncSession):
        """Leads with deleted_at set are excluded."""
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        now = datetime.now(timezone.utc)
        active = _make_lead(TENANT_A, whatsapp_id="wa-active")
        deleted = _make_lead(TENANT_A, whatsapp_id="wa-deleted")
        deleted.deleted_at = now
        async_session.add_all([active, deleted])
        await async_session.flush()

        svc = LeadQueryServiceImpl()
        lead_ids, total = await svc.list_lead_ids_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            limit=10,
            session=async_session,
        )

        assert total == 1
        assert len(lead_ids) == 1


# ---------------------------------------------------------------------------
# count_leads_matching
# ---------------------------------------------------------------------------


class TestCountLeadsMatching:
    """Returns count of leads matching predicate for the tenant."""

    @pytest.mark.asyncio
    async def test_counts_all_matching(self, async_session: AsyncSession):
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        async_session.add_all([_make_lead(TENANT_A, whatsapp_id=f"wa-{i}") for i in range(7)])
        await async_session.flush()

        svc = LeadQueryServiceImpl()
        count = await svc.count_leads_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            session=async_session,
        )

        assert count == 7

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, async_session: AsyncSession):
        """Only counts leads from the requested tenant."""
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        async_session.add_all([_make_lead(TENANT_A, whatsapp_id="wa-a1"), _make_lead(TENANT_A, whatsapp_id="wa-a2")])
        async_session.add_all([_make_lead(TENANT_B, whatsapp_id="wa-b1")])
        await async_session.flush()

        svc = LeadQueryServiceImpl()
        count = await svc.count_leads_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            session=async_session,
        )

        assert count == 2

    @pytest.mark.asyncio
    async def test_excludes_deleted_leads(self, async_session: AsyncSession):
        """Deleted leads are not counted."""
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        now = datetime.now(timezone.utc)
        active = _make_lead(TENANT_A, whatsapp_id="wa-active")
        deleted = _make_lead(TENANT_A, whatsapp_id="wa-deleted")
        deleted.deleted_at = now
        async_session.add_all([active, deleted])
        await async_session.flush()

        svc = LeadQueryServiceImpl()
        count = await svc.count_leads_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            session=async_session,
        )

        assert count == 1

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_tenant(self, async_session: AsyncSession):
        from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl

        svc = LeadQueryServiceImpl()
        count = await svc.count_leads_matching(
            tenant_id=TENANT_A,
            predicate=true(),
            session=async_session,
        )

        assert count == 0
