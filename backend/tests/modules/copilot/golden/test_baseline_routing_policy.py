"""Golden snapshot: default routing policy rules + tiers.

[COPILOT-REDESIGN-2026-04 F0.5]

The 4-tier model router is explicitly NOT touched by the redesign §3, but
F8 (routing + cost optimisation) refines it. F0 captures the rule set so
F8 can show its diff explicitly instead of silently shifting tier
assignment under shipping traffic.
"""

from __future__ import annotations

from src.modules.copilot.domain.routing_policy import DEFAULT_ROUTING_POLICY
from tests.modules.copilot.golden.conftest import assert_matches_golden


def test_routing_policy_shape_matches_baseline() -> None:
    snapshot = {
        "default_tier": DEFAULT_ROUTING_POLICY.default_tier.value,
        "rule_count": len(DEFAULT_ROUTING_POLICY.rules),
        "rules": [
            {
                # Use only stable, public attributes — internal fields stay free
                # to evolve without forcing the snapshot to churn.
                "name": getattr(rule, "name", None),
                "target_tier": getattr(rule, "target_tier", None).value
                if getattr(rule, "target_tier", None) is not None
                else None,
                "intent_kinds": sorted(getattr(rule, "intent_kinds", ()) or ()),
                "route_prefixes": sorted(getattr(rule, "route_prefixes", ()) or ()),
            }
            for rule in DEFAULT_ROUTING_POLICY.rules
        ],
    }
    assert_matches_golden("routing_policy_shape", snapshot)
