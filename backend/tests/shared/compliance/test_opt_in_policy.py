"""Tests for OptInPolicy — domain layer.

Tests use in-memory SQLite via SQLAOptInRepository (PM Q2 DB-backed).
"""

from __future__ import annotations

import datetime as dt
import uuid as uuid_mod
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from luana_core_compliance.domain.policies.opt_in_policy import OptInPolicy
from luana_core_compliance.infrastructure.models.channel_blacklist_model import ChannelBlacklistModel
from luana_core_compliance.infrastructure.models.lead_opt_in_model import LeadOptInModel
from luana_core_compliance.infrastructure.opt_in_repository_impl import SQLAOptInRepository
from luana_core_platform.domain.base_entity import Base

pytestmark = pytest.mark.asyncio

_TENANT: UUID = uuid4()
_LEAD: UUID = uuid4()


@pytest.fixture
async def async_session():
    """In-memory async SQLite session for opt-in repo tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
    await engine.dispose()


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class TestOptInPolicy:
    async def test_no_opt_in_row_fails(self, async_session: AsyncSession) -> None:
        repo = SQLAOptInRepository(async_session)
        policy = OptInPolicy(opt_in_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False
        assert result.failed_policy == "opt_in"
        assert result.evidence["opt_in_found"] is False

    async def test_active_opt_in_passes(self, async_session: AsyncSession) -> None:
        repo = SQLAOptInRepository(async_session)
        await repo.upsert(
            tenant_id=_TENANT,
            lead_id=_LEAD,
            channel="whatsapp",
            opted_in_at=_now() - dt.timedelta(days=5),
            opted_out_at=None,
            source="manual",
            evidence={},
        )
        policy = OptInPolicy(opt_in_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is True

    async def test_opted_out_fails(self, async_session: AsyncSession) -> None:
        repo = SQLAOptInRepository(async_session)
        await repo.upsert(
            tenant_id=_TENANT,
            lead_id=_LEAD,
            channel="whatsapp",
            opted_in_at=_now() - dt.timedelta(days=10),
            opted_out_at=_now() - dt.timedelta(days=1),
            source="webhook",
            evidence={},
        )
        policy = OptInPolicy(opt_in_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False
        assert result.failed_policy == "opt_in"
        assert result.evidence["opted_out_at"] is not None

    async def test_inferred_message_source_passes_with_lower_trust_flag(self, async_session: AsyncSession) -> None:
        repo = SQLAOptInRepository(async_session)
        await repo.upsert(
            tenant_id=_TENANT,
            lead_id=_LEAD,
            channel="telegram",
            opted_in_at=_now() - dt.timedelta(days=1),
            opted_out_at=None,
            source="inferred_message",
            evidence={"message_id": "abc123"},
        )
        policy = OptInPolicy(opt_in_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="telegram", identifier="@user")
        assert result.allowed is True
        assert result.evidence["lower_trust"] is True

    async def test_tenant_isolation_cross_tenant_lead(self, async_session: AsyncSession) -> None:
        """Opt-in of another tenant does not pass for our tenant."""
        other_tenant = uuid4()
        repo = SQLAOptInRepository(async_session)
        await repo.upsert(
            tenant_id=other_tenant,
            lead_id=_LEAD,
            channel="whatsapp",
            opted_in_at=_now(),
            opted_out_at=None,
            source="manual",
            evidence={},
        )
        policy = OptInPolicy(opt_in_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False  # Our tenant has no opt-in

    async def test_name_attribute(self) -> None:
        from unittest.mock import AsyncMock

        policy = OptInPolicy(opt_in_repo=AsyncMock())
        assert policy.name == "opt_in"
