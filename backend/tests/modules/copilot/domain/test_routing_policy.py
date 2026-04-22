"""Tests for DEFAULT_ROUTING_POLICY — all rules present, tiers valid."""

from __future__ import annotations

import pytest

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.routing_policy import (
    DEFAULT_ROUTING_POLICY,
    ClassifierType,
    RoutingPolicy,
    RoutingRule,
)


class TestClassifierType:
    """ClassifierType enum covers the 3 sources."""

    def test_values_present(self) -> None:
        assert ClassifierType.RULE == "rule"
        assert ClassifierType.LLM == "llm"
        assert ClassifierType.DEFAULT == "default"


class TestRoutingRule:
    """RoutingRule frozen dataclass."""

    def test_frozen(self) -> None:
        """RoutingRule cannot be mutated after creation."""
        rule = RoutingRule(
            pattern=r".*",
            tier=ModelTier.NANO,
            reason="test",
            priority=99,
        )
        with pytest.raises((AttributeError, TypeError)):
            rule.reason = "mutated"  # type: ignore[misc]

    def test_defaults_are_none_or_empty(self) -> None:
        """Optional fields default to None/empty."""
        rule = RoutingRule(pattern=r".*", tier=ModelTier.MINI, reason="x", priority=50)
        assert rule.min_msg_length is None
        assert rule.max_msg_length is None
        assert rule.max_tools is None
        assert rule.required_keywords == ()


class TestDefaultRoutingPolicy:
    """DEFAULT_ROUTING_POLICY is a well-formed RoutingPolicy."""

    def test_default_tier_is_mini(self) -> None:
        """Default tier (no rule matches) is MINI per CONTRACT §2.2."""
        assert DEFAULT_ROUTING_POLICY.default_tier == ModelTier.MINI

    def test_all_rule_tiers_are_valid(self) -> None:
        """Every rule references a real ModelTier."""
        valid_tiers = set(ModelTier)
        for rule in DEFAULT_ROUTING_POLICY.rules:
            assert rule.tier in valid_tiers, f"Rule tier {rule.tier!r} not in ModelTier"

    def test_rules_sorted_by_priority(self) -> None:
        """Rules are sorted ascending by priority."""
        priorities = [r.priority for r in DEFAULT_ROUTING_POLICY.rules]
        assert priorities == sorted(priorities), "Rules not sorted by priority"

    def test_has_heavy_rules(self) -> None:
        """At least one rule targets HEAVY tier."""
        heavy_rules = [r for r in DEFAULT_ROUTING_POLICY.rules if r.tier == ModelTier.HEAVY]
        assert len(heavy_rules) >= 1

    def test_has_reasoning_rules(self) -> None:
        """At least one rule targets REASONING tier."""
        reasoning_rules = [r for r in DEFAULT_ROUTING_POLICY.rules if r.tier == ModelTier.REASONING]
        assert len(reasoning_rules) >= 1

    def test_has_nano_rule(self) -> None:
        """At least one rule targets NANO tier."""
        nano_rules = [r for r in DEFAULT_ROUTING_POLICY.rules if r.tier == ModelTier.NANO]
        assert len(nano_rules) >= 1

    def test_short_msg_no_tools_nano_rule_exists(self) -> None:
        """The short_msg_no_tools nano rule exists with max_msg_length and max_tools."""
        nano_short = [
            r for r in DEFAULT_ROUTING_POLICY.rules if r.tier == ModelTier.NANO and r.max_msg_length is not None
        ]
        assert len(nano_short) >= 1
        rule = nano_short[0]
        assert rule.max_tools == 0
        assert rule.max_msg_length == 40

    def test_rules_are_tuple(self) -> None:
        """Rules is a tuple (frozen)."""
        assert isinstance(DEFAULT_ROUTING_POLICY.rules, tuple)

    def test_all_rules_have_non_empty_reason(self) -> None:
        """Every rule has a non-empty reason string for telemetry."""
        for rule in DEFAULT_ROUTING_POLICY.rules:
            assert rule.reason, f"Empty reason for rule priority={rule.priority}"

    def test_all_rules_have_non_empty_pattern(self) -> None:
        """Every rule has a non-empty pattern string."""
        for rule in DEFAULT_ROUTING_POLICY.rules:
            assert rule.pattern, f"Empty pattern for rule priority={rule.priority}"

    def test_policy_is_a_routing_policy_instance(self) -> None:
        """DEFAULT_ROUTING_POLICY is a RoutingPolicy instance."""
        assert isinstance(DEFAULT_ROUTING_POLICY, RoutingPolicy)
