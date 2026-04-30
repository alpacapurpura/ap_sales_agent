"""RuleClassifier — regex + length + tool guards over a RoutingPolicy.

See CONTRACT §7.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from src.core.enums import ModelRole
from src.modules.copilot.domain.routing_policy import (
    ClassifierType,
    RoutingDecision,
    RoutingPolicy,
    RoutingRule,
)

if TYPE_CHECKING:
    from src.modules.copilot.application.router.model_router import RoutingRequest


class RuleClassifier:
    """Evaluate ordered ``RoutingRule`` entries; first match wins."""

    def __init__(self, policy: RoutingPolicy) -> None:
        """Pre-compile all rule regexes (case-insensitive) sorted by priority asc."""
        self._policy = policy
        sorted_rules = sorted(policy.rules, key=lambda r: r.priority)
        self._compiled: tuple[tuple[RoutingRule, re.Pattern[str]], ...] = tuple(
            (rule, re.compile(rule.pattern, re.IGNORECASE)) for rule in sorted_rules
        )

    def classify(self, req: RoutingRequest) -> RoutingDecision | None:
        """Return decision for the first matching rule, or ``None``."""
        msg = req.user_msg
        msg_len = len(msg)
        for rule, pattern in self._compiled:
            if not pattern.search(msg):
                continue
            if rule.min_msg_length is not None and msg_len < rule.min_msg_length:
                continue
            if rule.max_msg_length is not None and msg_len > rule.max_msg_length:
                continue
            if rule.max_tools is not None and req.available_tool_count > rule.max_tools:
                continue
            if rule.required_keywords and not all(kw.lower() in msg.lower() for kw in rule.required_keywords):
                continue
            return RoutingDecision(
                role=rule.role,
                reason=rule.reason,
                confidence=1.0,
                classifier_used=ClassifierType.RULE,
                fallback_role=ModelRole.FAST,
            )
        return None
