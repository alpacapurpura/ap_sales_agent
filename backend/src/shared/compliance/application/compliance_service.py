"""ComplianceService — policy chain orchestrator.

Order: WABA24h → OptIn → Blacklist → CountryBlock.
Short-circuits on first FAIL.
Sub-100ms p95 target (Redis-cached lookups + indexed queries).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

import structlog
from luana_core_compliance.domain.check_result import CheckResult

logger = structlog.get_logger(__name__)


@runtime_checkable
class CompliancePolicy(Protocol):
    """Policy protocol. Each policy returns CheckResult."""

    name: str

    async def evaluate(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None,
    ) -> CheckResult:
        """Evaluate this policy for the given contact."""
        ...


class ComplianceService:
    """Policy chain orchestrator.

    Runs policies in injection order. Short-circuits on first allowed=False.
    Logs each policy result for audit trail (S2 persists compliance_check_log).
    """

    def __init__(self, policies: list[CompliancePolicy]) -> None:
        """Inject ordered list of policies.

        Default order: WABA24h → OptIn → Blacklist → CountryBlock.
        Composition root decides order at wiring time.
        """
        self._policies = policies

    async def check(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None = None,
    ) -> CheckResult:
        """Run policy chain. Return first FAIL or final PASS.

        Short-circuit semantics: first policy returning allowed=False
        terminates the chain. This is intentional for performance and
        to avoid leaking evidence from multiple policies on a single request.
        """
        for policy in self._policies:
            result = await policy.evaluate(
                tenant_id=tenant_id,
                lead_id=lead_id,
                channel=channel,
                identifier=identifier,
                campaign_id=campaign_id,
            )
            if not result.allowed:
                logger.info(
                    "compliance_check_failed",
                    tenant_id=str(tenant_id),
                    lead_id=str(lead_id),
                    channel=channel,
                    policy=policy.name,
                    failed_policy=result.failed_policy,
                    reason=result.reason,
                )
                return result

            logger.debug(
                "compliance_check_policy_pass",
                tenant_id=str(tenant_id),
                policy=policy.name,
            )

        return CheckResult(allowed=True)
