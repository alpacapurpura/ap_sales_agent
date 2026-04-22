"""Routing policy data types and default routing rules.

This module is pure data — no SQLAlchemy, no FastAPI, no HTTP.
The RuleClassifier evaluator lives in application/router/.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.modules.copilot.domain.model_tier import ModelTier


class ClassifierType(StrEnum):
    """Which classifier produced a routing decision."""

    RULE = "rule"
    LLM = "llm"
    DEFAULT = "default"


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Result of a routing classification."""

    tier: ModelTier
    reason: str
    confidence: float
    classifier_used: ClassifierType
    fallback_tier: ModelTier


@dataclass(frozen=True, slots=True)
class RoutingRule:
    """Data-only rule evaluated by RuleClassifier.

    Rules are matched in ascending priority order; first match wins.
    """

    pattern: str
    tier: ModelTier
    reason: str
    priority: int
    min_msg_length: int | None = None
    max_msg_length: int | None = None
    max_tools: int | None = None
    required_keywords: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """Immutable routing policy — a tuple of rules plus a default tier."""

    rules: tuple[RoutingRule, ...]
    default_tier: ModelTier = ModelTier.MINI


# Default policy — rules ordered by priority ascending; first regex match
# that also passes length/tool guards wins.
DEFAULT_ROUTING_POLICY: RoutingPolicy = RoutingPolicy(
    default_tier=ModelTier.MINI,
    rules=(
        # ── HEAVY (priority 10-19) ─────────────────────────────────────
        RoutingRule(
            priority=10,
            pattern=r"\b(audita|auditar|diagn[oó]stic[oa]|analiza a fondo)\b",
            tier=ModelTier.HEAVY,
            reason="keyword_audit_diagnostic",
        ),
        RoutingRule(
            priority=11,
            pattern=r"\bplan estrat[eé]gico\b|\bestrategia de\b",
            tier=ModelTier.HEAVY,
            reason="keyword_strategic_plan",
        ),
        RoutingRule(
            priority=12,
            pattern=r"\bad[oó]nde va mi\b|\bc[oó]mo mejorar (mi|la) (marca|oferta|funnel)\b",
            tier=ModelTier.HEAVY,
            reason="keyword_cross_module_improve",
        ),
        # ── REASONING (priority 20-29) ─────────────────────────────────
        RoutingRule(
            priority=20,
            pattern=r"\bpor qu[eé]\b|\bdame razones\b|\bexplica por qu[eé]\b",
            tier=ModelTier.REASONING,
            reason="keyword_causal_why",
        ),
        RoutingRule(
            priority=21,
            pattern=r"\bcomp[aá]rame\b|\boptimiza\b|\brazon[aá]\b|\bpiensa paso a paso\b",
            tier=ModelTier.REASONING,
            reason="keyword_compare_reason",
        ),
        RoutingRule(
            priority=22,
            pattern=r"\bc[oó]mo (puedo|podr[ií]a)\b",
            tier=ModelTier.REASONING,
            reason="keyword_how_can_i",
        ),
        # ── NANO (priority 30-39) short & toolless ─────────────────────
        RoutingRule(
            priority=30,
            pattern=r".*",
            tier=ModelTier.NANO,
            reason="short_msg_no_tools",
            max_msg_length=40,
            max_tools=0,
        ),
        # default falls through to policy.default_tier (MINI)
    ),
)
