"""BudgetDecision value object — result of BudgetGuard.check().

Immutable decision: allowed/blocked + pool info + soft warn signal.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    """Result of BudgetGuard.check().

    Attributes:
    ----------
    allowed : bool
        Whether the LLM call may proceed.
    pool : str
        Which bucket was consulted: "sales_agent" | "others".
    spent_usd : Decimal
        Cycle-to-date spend for the bucket.
    cap_usd : Decimal
        Effective cap for the bucket (may include 105% soft-cap factor).
    soft_warn : bool
        True when ≥80% of the pool is consumed but call is still allowed.
    reason : str | None
        "cycle_budget_exhausted" | "mv_stale_soft_cap" | None.
    decision_id : str | None
        UUID for trace correlation (optional).
    """

    allowed: bool
    pool: str
    spent_usd: Decimal
    cap_usd: Decimal
    soft_warn: bool = False
    reason: str | None = None
    decision_id: str | None = None
