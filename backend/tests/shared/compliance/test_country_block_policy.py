"""Tests for CountryBlockPolicy — domain layer.

PM Q3: lead.country preferred over E.164 prefix heuristic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.shared.compliance.domain.policies.country_block_policy import (
    CountryBlockPolicy,
    _lookup_phone_prefix,
)

pytestmark = pytest.mark.asyncio

_TENANT = uuid4()
_LEAD = uuid4()


def _make_lead_reader(country: str | None) -> AsyncMock:
    reader = AsyncMock()
    reader.get_lead_country = AsyncMock(return_value=country)
    return reader


class TestCountryBlockPolicy:
    async def test_empty_block_list_always_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "")
        policy = CountryBlockPolicy()
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5312345678")
        assert result.allowed is True

    async def test_lead_country_in_block_list_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "CU,KP,IR")
        reader = _make_lead_reader("CU")
        policy = CountryBlockPolicy(lead_country_reader=reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5312345678")
        assert result.allowed is False
        assert result.failed_policy == "country_block"
        assert result.evidence["country_iso"] == "CU"
        assert result.evidence["country_source"] == "lead_field"

    async def test_lead_country_not_in_block_list_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "CU,KP")
        reader = _make_lead_reader("PE")
        policy = CountryBlockPolicy(lead_country_reader=reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5112345678")
        assert result.allowed is True

    async def test_fallback_to_phone_prefix_when_country_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "CU")
        reader = _make_lead_reader(None)  # No country on lead
        policy = CountryBlockPolicy(lead_country_reader=reader)
        # CU prefix = +53
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5312345678")
        assert result.allowed is False
        assert result.evidence["country_iso"] == "CU"
        assert result.evidence["country_source"] == "phone_prefix"

    async def test_phone_prefix_not_for_non_phone_channels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "CU")
        policy = CountryBlockPolicy(lead_country_reader=None)
        # Email channel — no phone prefix lookup
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="email", identifier="user@example.cu")
        assert result.allowed is True  # Unknown country → allow

    async def test_unknown_country_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "CU")
        reader = _make_lead_reader(None)
        policy = CountryBlockPolicy(lead_country_reader=reader)
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+9999999999")
        assert result.allowed is True
        assert result.evidence.get("country_iso") is None

    async def test_lead_reader_error_falls_back_gracefully(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "CU")
        reader = AsyncMock()
        reader.get_lead_country = AsyncMock(side_effect=RuntimeError("DB error"))
        policy = CountryBlockPolicy(lead_country_reader=reader)
        # Falls back to phone prefix
        result = await policy.evaluate(tenant_id=_TENANT, lead_id=_LEAD, channel="whatsapp", identifier="+5212345678")
        # MX (+52) not in block list → pass
        assert result.allowed is True

    async def test_name_attribute(self) -> None:
        policy = CountryBlockPolicy()
        assert policy.name == "country_block"


class TestPhonePrefixLookup:
    def test_cuba_prefix(self) -> None:
        assert _lookup_phone_prefix("+5312345678") == "CU"

    def test_mexico_prefix(self) -> None:
        assert _lookup_phone_prefix("+5212345678") == "MX"

    def test_peru_prefix(self) -> None:
        assert _lookup_phone_prefix("+5112345678") == "PE"

    def test_unknown_prefix_returns_none(self) -> None:
        assert _lookup_phone_prefix("+9999999999") is None

    def test_no_plus_sign_returns_none(self) -> None:
        assert _lookup_phone_prefix("5312345678") is None

    def test_strips_spaces(self) -> None:
        assert _lookup_phone_prefix("+53 1234 5678") == "CU"

    def test_longer_prefix_wins_over_shorter(self) -> None:
        # +850 (KP) vs +85 (no country) — should match +850
        assert _lookup_phone_prefix("+8501234567") == "KP"
