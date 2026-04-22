"""RuleRegistry — protocol for the in-memory rule index.

See CONTRACT §13.3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.modules.copilot.domain.rules.rule_definition import RuleDefinition


class RuleLoadError(Exception):
    """Raised when a rule ``.md`` file fails frontmatter validation."""

    def __init__(self, path: str, reason: str) -> None:
        """Store path + underlying reason for debugging."""
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


@runtime_checkable
class RuleRegistry(Protocol):
    """Port for the in-memory rule index."""

    def global_rules(self) -> list[RuleDefinition]:
        """Return all rules with ``scope == global`` sorted by priority asc."""
        ...

    def for_route(self, route: str | None) -> list[RuleDefinition]:
        """Return rules whose ``scope == route:<prefix>`` match ``route``."""
        ...

    def for_skill(self, skill_name: str) -> list[RuleDefinition]:
        """Return rules whose ``scope == skill:<name>`` match ``skill_name``."""
        ...

    def all(self) -> list[RuleDefinition]:
        """Return every loaded rule."""
        ...

    def get_by_name(self, name: str) -> RuleDefinition | None:
        """Return a rule by its kebab-case ``name`` (or None)."""
        ...
