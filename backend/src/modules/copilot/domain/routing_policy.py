"""Routing policy data types and default routing rules.

This module is pure data — no SQLAlchemy, no FastAPI, no HTTP.
The RuleClassifier evaluator lives in application/router/.

Post S3 PR-1 convergence: ``ModelRole`` is the single SSoT
(see ``docs/domains/llm-routing.md``). Mapping legacy ModelTier→ModelRole:
NANO→NANO, MINI→FAST, REASONING→REASONING, HEAVY→AGENT.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.enums import ModelRole


class ClassifierType(StrEnum):
    """Which classifier produced a routing decision."""

    RULE = "rule"
    LLM = "llm"
    DEFAULT = "default"


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Result of a routing classification."""

    role: ModelRole
    reason: str
    confidence: float
    classifier_used: ClassifierType
    fallback_role: ModelRole


@dataclass(frozen=True, slots=True)
class RoutingRule:
    """Data-only rule evaluated by RuleClassifier.

    Rules are matched in ascending priority order; first match wins.
    """

    pattern: str
    role: ModelRole
    reason: str
    priority: int
    min_msg_length: int | None = None
    max_msg_length: int | None = None
    max_tools: int | None = None
    required_keywords: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """Immutable routing policy — a tuple of rules plus a default role."""

    rules: tuple[RoutingRule, ...]
    default_role: ModelRole = ModelRole.FAST


# Default policy — rules ordered by priority ascending; first regex match
# that also passes length/tool guards wins.
DEFAULT_ROUTING_POLICY: RoutingPolicy = RoutingPolicy(
    default_role=ModelRole.FAST,
    rules=(
        # ── AGENT (priority 10-19) — heavy multi-step / cross-module ───
        RoutingRule(
            priority=10,
            pattern=r"\b(audita|auditar|diagn[oó]stic[oa]|analiza a fondo)\b",
            role=ModelRole.AGENT,
            reason="keyword_audit_diagnostic",
        ),
        RoutingRule(
            priority=11,
            pattern=r"\bplan estrat[eé]gico\b|\bestrategia de\b",
            role=ModelRole.AGENT,
            reason="keyword_strategic_plan",
        ),
        RoutingRule(
            priority=12,
            pattern=r"\bad[oó]nde va mi\b|\bc[oó]mo mejorar (mi|la) (marca|oferta|funnel)\b",
            role=ModelRole.AGENT,
            reason="keyword_cross_module_improve",
        ),
        # ── REASONING (priority 20-29) ─────────────────────────────────
        RoutingRule(
            priority=20,
            pattern=r"\bpor qu[eé]\b|\bdame razones\b|\bexplica por qu[eé]\b",
            role=ModelRole.REASONING,
            reason="keyword_causal_why",
        ),
        RoutingRule(
            priority=21,
            pattern=r"\bcomp[aá]rame\b|\boptimiza\b|\brazon[aá]\b|\bpiensa paso a paso\b",
            role=ModelRole.REASONING,
            reason="keyword_compare_reason",
        ),
        RoutingRule(
            priority=22,
            pattern=r"\bc[oó]mo (puedo|podr[ií]a)\b",
            role=ModelRole.REASONING,
            reason="keyword_how_can_i",
        ),
        # ── NANO (priority 30-39) short turns ──────────────────────────
        # Reason kept as historical telemetry id ``short_msg_no_tools`` but the
        # ``max_tools`` guard was removed: chat overlay always exposes the full
        # tool registry (~26 tools), so guarding by ``available_tool_count == 0``
        # made the rule unreachable. NANO is still the right role — heavier
        # rules (priority 10-22) win first when intent demands more capability.
        RoutingRule(
            priority=30,
            pattern=r".*",
            role=ModelRole.NANO,
            reason="short_msg_no_tools",
            max_msg_length=40,
        ),
        # default falls through to policy.default_role (FAST)
    ),
)
