"""Tests for WABA24hPolicy — domain layer.

RED first (TDD-mandatory). Pure unit tests — no DB.
"""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from luana_core_compliance.domain.policies.waba_24h_policy import WABA24hPolicy

pytestmark = pytest.mark.asyncio

_TENANT = uuid4()
_LEAD = uuid4()


def _make_messages_reader(last_inbound_at: dt.datetime | None) -> AsyncMock:
    reader = AsyncMock()
    reader.get_last_inbound_at = AsyncMock(return_value=last_inbound_at)
    return reader


class TestWABA24hPolicy:
    async def test_non_whatsapp_channel_always_passes(self) -> None:
        reader = _make_messages_reader(None)
        policy = WABA24hPolicy(reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="telegram", identifier="+5112345678")
        assert result.allowed is True
        reader.get_last_inbound_at.assert_not_called()

    async def test_whatsapp_no_inbound_ever_fails(self) -> None:
        reader = _make_messages_reader(None)
        policy = WABA24hPolicy(reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False
        assert result.failed_policy == "waba_24h"
        assert result.evidence["last_inbound_at"] is None

    async def test_whatsapp_inbound_within_24h_passes(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        recent = now - dt.timedelta(hours=10)
        reader = _make_messages_reader(recent)
        policy = WABA24hPolicy(reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is True
        assert "hours_since_inbound" in result.evidence
        assert result.evidence["hours_since_inbound"] < 24

    async def test_whatsapp_inbound_over_24h_fails(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        old = now - dt.timedelta(hours=25)
        reader = _make_messages_reader(old)
        policy = WABA24hPolicy(reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False
        assert result.failed_policy == "waba_24h"
        assert result.evidence["hours_since_inbound"] > 24

    async def test_whatsapp_inbound_exactly_24h_fails(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        exactly = now - dt.timedelta(hours=24, seconds=1)
        reader = _make_messages_reader(exactly)
        policy = WABA24hPolicy(reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is False

    async def test_naive_datetime_treated_as_utc(self) -> None:
        """Naive datetime from DB should be treated as UTC (not crash)."""
        naive = dt.datetime.utcnow() - dt.timedelta(hours=5)  # noqa: DTZ003 — intentional test
        reader = _make_messages_reader(naive)
        policy = WABA24hPolicy(reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is True  # 5h ago < 24h

    async def test_name_attribute(self) -> None:
        policy = WABA24hPolicy(AsyncMock())
        assert policy.name == "waba_24h"
