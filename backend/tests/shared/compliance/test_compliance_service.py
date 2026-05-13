"""Tests for ComplianceService — application layer.

Verifies short-circuit behavior: first FAIL terminates chain.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, call
from uuid import uuid4

import pytest

from luana_core_compliance.application.compliance_service import ComplianceService
from luana_core_compliance.domain.check_result import CheckResult

pytestmark = pytest.mark.asyncio

_TENANT = uuid4()
_LEAD = uuid4()
_CHANNEL = "whatsapp"
_IDENTIFIER = "+5112345678"


def _pass_policy(name: str) -> AsyncMock:
    policy = AsyncMock()
    policy.name = name
    policy.evaluate = AsyncMock(return_value=CheckResult(allowed=True))
    return policy


def _fail_policy(name: str, reason: str = "blocked") -> AsyncMock:
    policy = AsyncMock()
    policy.name = name
    policy.evaluate = AsyncMock(
        return_value=CheckResult(
            allowed=False,
            failed_policy=name,
            reason=reason,
        )
    )
    return policy


async def _run(service: ComplianceService) -> CheckResult:
    return await service.check(
        tenant_id=_TENANT,
        lead_id=_LEAD,
        channel=_CHANNEL,
        identifier=_IDENTIFIER,
    )


class TestComplianceService:
    async def test_all_pass_returns_allowed(self) -> None:
        policies = [_pass_policy("p1"), _pass_policy("p2"), _pass_policy("p3")]
        service = ComplianceService(policies)
        result = await _run(service)
        assert result.allowed is True

    async def test_first_fail_short_circuits(self) -> None:
        p1 = _fail_policy("waba_24h")
        p2 = _pass_policy("opt_in")
        p3 = _pass_policy("blacklist")
        service = ComplianceService([p1, p2, p3])
        result = await _run(service)
        assert result.allowed is False
        assert result.failed_policy == "waba_24h"
        # p2 and p3 MUST NOT have been called
        p2.evaluate.assert_not_called()
        p3.evaluate.assert_not_called()

    async def test_middle_fail_short_circuits(self) -> None:
        p1 = _pass_policy("waba_24h")
        p2 = _fail_policy("opt_in", reason="no consentimiento")
        p3 = _pass_policy("blacklist")
        service = ComplianceService([p1, p2, p3])
        result = await _run(service)
        assert result.allowed is False
        assert result.failed_policy == "opt_in"
        p1.evaluate.assert_called_once()
        p2.evaluate.assert_called_once()
        p3.evaluate.assert_not_called()

    async def test_last_policy_fail(self) -> None:
        p1 = _pass_policy("waba_24h")
        p2 = _pass_policy("opt_in")
        p3 = _fail_policy("country_block", reason="país bloqueado")
        service = ComplianceService([p1, p2, p3])
        result = await _run(service)
        assert result.allowed is False
        assert result.failed_policy == "country_block"
        for p in [p1, p2, p3]:
            p.evaluate.assert_called_once()

    async def test_empty_policy_chain_passes(self) -> None:
        service = ComplianceService(policies=[])
        result = await _run(service)
        assert result.allowed is True

    async def test_single_pass_policy(self) -> None:
        service = ComplianceService(policies=[_pass_policy("only")])
        result = await _run(service)
        assert result.allowed is True

    async def test_policies_receive_correct_args(self) -> None:
        p1 = _pass_policy("test")
        service = ComplianceService(policies=[p1])
        campaign_id = uuid4()
        await service.check(
            tenant_id=_TENANT,
            lead_id=_LEAD,
            channel=_CHANNEL,
            identifier=_IDENTIFIER,
            campaign_id=campaign_id,
        )
        p1.evaluate.assert_called_once_with(
            tenant_id=_TENANT,
            lead_id=_LEAD,
            channel=_CHANNEL,
            identifier=_IDENTIFIER,
            campaign_id=campaign_id,
        )
