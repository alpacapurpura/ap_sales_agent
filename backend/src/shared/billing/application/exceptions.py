"""Billing exceptions — raised when budget gates block LLM calls.

PR-6 / PI-1 S2.
"""

from __future__ import annotations

from src.shared.billing.domain.budget_decision import BudgetDecision


class BudgetExceeded(Exception):  # noqa: N818 — intentional: domain exception name from CONTRACT, widely consumed
    """Raised when BudgetGuard.check returns allowed=False.

    Carries the BudgetDecision so the caller (orchestrator/middleware)
    can map to HTTP 402 with structured payload.

    Handling per module:
    - copilot HTTP route → JSONResponse(status_code=402, ...)
    - sales_agent inbound (telegram webhook) → emit BudgetExceededEvent +
      skip OutputManager (no message to lead this turn — graceful degrade)
    - brand ARQ worker → mark job status=skipped_budget_exhausted
    """

    def __init__(self, decision: BudgetDecision) -> None:
        """Store the budget decision for caller inspection."""
        self.decision = decision
        super().__init__(
            f"budget_exceeded pool={decision.pool} "
            f"spent={decision.spent_usd} cap={decision.cap_usd} "
            f"reason={decision.reason}"
        )
