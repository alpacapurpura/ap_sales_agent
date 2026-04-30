"""OptIn Policy — PM Q2 DB-backed production-grade per-channel consent check.

PASS: lead_opt_ins row exists with opted_in_at NOT NULL AND opted_out_at IS NULL.
FAIL: no row, opted_out, or never opted in.

inferred_message source rows still PASS but evidence flags lower trust.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from src.shared.compliance.domain.check_result import CheckResult
from src.shared.compliance.domain.opt_in_repository import OptInRepository

logger = structlog.get_logger(__name__)


class OptInPolicy:
    """All channels: verify active opt-in via lead_opt_ins table.

    PM Q2: DB-backed. No longer uses messages.role='user' heuristic.
    Migration backfills from messages last 30d with source='inferred_message'.
    """

    name: str = "opt_in"

    def __init__(self, opt_in_repo: OptInRepository) -> None:
        """Bind to OptInRepository implementation."""
        self._opt_in_repo = opt_in_repo

    async def evaluate(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None = None,
    ) -> CheckResult:
        """Evaluate opt-in policy."""
        opt_in = await self._opt_in_repo.get(tenant_id=tenant_id, lead_id=lead_id, channel=channel)

        if opt_in is None:
            return CheckResult(
                allowed=False,
                failed_policy=self.name,
                reason="El contacto no tiene consentimiento de comunicación en este canal",
                evidence={
                    "lead_id": str(lead_id),
                    "channel": channel,
                    "opt_in_found": False,
                },
            )

        if not opt_in.is_active_opt_in:
            return CheckResult(
                allowed=False,
                failed_policy=self.name,
                reason="El contacto canceló el consentimiento de comunicación",
                evidence={
                    "lead_id": str(lead_id),
                    "channel": channel,
                    "opted_out_at": opt_in.opted_out_at.isoformat() if opt_in.opted_out_at else None,
                    "opt_in_source": opt_in.source,
                },
            )

        # PASS — capture source for audit trail
        evidence = {
            "opt_in_id": str(opt_in.id),
            "opt_in_source": opt_in.source,
            "opted_in_at": opt_in.opted_in_at.isoformat() if opt_in.opted_in_at else None,
            "lower_trust": opt_in.source == "inferred_message",
        }

        return CheckResult(allowed=True, evidence=evidence)
