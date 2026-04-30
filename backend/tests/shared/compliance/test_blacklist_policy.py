"""Tests for BlacklistPolicy — domain layer.

Tests use in-memory SQLite via SQLABlacklistRepository.
"""

from __future__ import annotations

import datetime as dt
import uuid as uuid_mod
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.shared.compliance.domain.blacklist_entry import ChannelBlacklistEntry
from src.shared.compliance.domain.policies.blacklist_policy import BlacklistPolicy
from src.shared.compliance.infrastructure.blacklist_repository_impl import SQLABlacklistRepository
from src.shared.compliance.infrastructure.models.channel_blacklist_model import ChannelBlacklistModel
from src.shared.compliance.infrastructure.models.lead_opt_in_model import LeadOptInModel
from src.shared.domain.base_entity import Base

pytestmark = pytest.mark.asyncio

_TENANT: UUID = uuid4()
_LEAD: UUID = uuid4()


@pytest.fixture
async def async_session():
    """In-memory async SQLite session for blacklist repo tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
    await engine.dispose()


def _entry(**overrides) -> ChannelBlacklistEntry:
    defaults: dict = {
        "id": uuid4(),
        "tenant_id": _TENANT,
        "channel": "whatsapp",
        "identifier": "+5112345678",
        "reason": "test",
        "created_by_user_id": None,
        "created_at": dt.datetime.now(dt.timezone.utc),
        "deleted_at": None,
    }
    defaults.update(overrides)
    return ChannelBlacklistEntry(**defaults)


class TestBlacklistPolicy:
    async def test_not_blacklisted_passes(self, async_session: AsyncSession) -> None:
        repo = SQLABlacklistRepository(async_session)
        policy = BlacklistPolicy(blacklist_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is True

    async def test_blacklisted_identifier_fails(self, async_session: AsyncSession) -> None:
        repo = SQLABlacklistRepository(async_session)
        await repo.upsert(_entry())
        policy = BlacklistPolicy(blacklist_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False
        assert result.failed_policy == "blacklist"
        assert "identifier" in result.evidence

    async def test_soft_deleted_entry_passes(self, async_session: AsyncSession) -> None:
        repo = SQLABlacklistRepository(async_session)
        entry = await repo.upsert(_entry())
        await repo.soft_delete(tenant_id=_TENANT, entry_id=entry.id)
        policy = BlacklistPolicy(blacklist_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is True

    async def test_different_channel_not_blocked(self, async_session: AsyncSession) -> None:
        repo = SQLABlacklistRepository(async_session)
        await repo.upsert(_entry(channel="whatsapp"))
        policy = BlacklistPolicy(blacklist_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="telegram", identifier="+5112345678")
        assert result.allowed is True

    async def test_different_identifier_not_blocked(self, async_session: AsyncSession) -> None:
        repo = SQLABlacklistRepository(async_session)
        await repo.upsert(_entry(identifier="+5112345678"))
        policy = BlacklistPolicy(blacklist_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5199999999")
        assert result.allowed is True

    async def test_cross_tenant_isolation(self, async_session: AsyncSession) -> None:
        """Blacklist entry of another tenant does not affect our tenant."""
        other_tenant = uuid4()
        repo = SQLABlacklistRepository(async_session)
        await repo.upsert(_entry(tenant_id=other_tenant))
        policy = BlacklistPolicy(blacklist_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is True

    async def test_identifier_partially_masked_in_evidence(self, async_session: AsyncSession) -> None:
        repo = SQLABlacklistRepository(async_session)
        await repo.upsert(_entry())
        policy = BlacklistPolicy(blacklist_repo=repo)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False
        evidence_id = result.evidence.get("identifier", "")
        assert "***" in evidence_id  # masked for PII

    async def test_name_attribute(self) -> None:
        from unittest.mock import AsyncMock

        policy = BlacklistPolicy(blacklist_repo=AsyncMock())
        assert policy.name == "blacklist"
