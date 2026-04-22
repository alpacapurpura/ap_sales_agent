"""InMemoryRuleRegistry — dict-backed RuleRegistry implementation.

See CONTRACT §13.3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.copilot.domain.rules.rule_definition import RuleDefinition


_GLOBAL = "global"
_ROUTE_PREFIX = "route:"
_SKILL_PREFIX = "skill:"


class InMemoryRuleRegistry:
    """Dict-backed rule registry, sorted-on-access by (priority asc, name asc)."""

    def __init__(self) -> None:
        """Start empty."""
        self._rules: list[RuleDefinition] = []

    def add(self, rule: RuleDefinition) -> None:
        """Register a rule. Raises on duplicate name."""
        name = rule.metadata.name
        for existing in self._rules:
            if existing.metadata.name == name:
                msg = f"duplicate rule: {name}"
                raise ValueError(msg)
        self._rules.append(rule)

    def all(self) -> list[RuleDefinition]:
        """Return every loaded rule."""
        return list(self._rules)

    def global_rules(self) -> list[RuleDefinition]:
        """Return global rules sorted by priority asc then name asc."""
        matches = [r for r in self._rules if r.metadata.scope == _GLOBAL]
        return sorted(
            matches,
            key=lambda r: (r.metadata.priority, r.metadata.name),
        )

    def for_route(self, route: str | None) -> list[RuleDefinition]:
        """Return ``route:<prefix>`` rules matching ``route`` (prefix)."""
        if not route:
            return []
        matches: list[RuleDefinition] = []
        for rule in self._rules:
            scope = rule.metadata.scope
            if not scope.startswith(_ROUTE_PREFIX):
                continue
            prefix = scope[len(_ROUTE_PREFIX) :]
            if route.startswith(prefix):
                matches.append(rule)
        return sorted(
            matches,
            key=lambda r: (r.metadata.priority, r.metadata.name),
        )

    def for_skill(self, skill_name: str) -> list[RuleDefinition]:
        """Return ``skill:<name>`` rules matching ``skill_name`` exactly."""
        target = f"{_SKILL_PREFIX}{skill_name}"
        matches = [r for r in self._rules if r.metadata.scope == target]
        return sorted(
            matches,
            key=lambda r: (r.metadata.priority, r.metadata.name),
        )

    def get_by_name(self, name: str) -> RuleDefinition | None:
        """Return rule by name, or None."""
        for rule in self._rules:
            if rule.metadata.name == name:
                return rule
        return None
