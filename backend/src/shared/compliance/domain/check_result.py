"""CheckResult value object — compliance domain.

Immutable result of a compliance policy evaluation.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Result of a compliance check.

    Attributes:
    ----------
    allowed : bool
        Whether the operation is permitted.
    failed_policy : str | None
        Name of the first policy that failed, or None on PASS.
        Values: "waba_24h" | "opt_in" | "blacklist" | "country_block" | None.
    reason : str | None
        Human-readable reason for denial.
    evidence : dict[str, Any]
        Structured audit data (last_inbound_at, opt_in_source, country_iso, etc.).
        Defaults to empty dict. Never None.
    """

    allowed: bool
    failed_policy: str | None = None
    reason: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
