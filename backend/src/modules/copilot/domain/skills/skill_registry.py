"""SkillRegistry — protocol for the in-memory skill index.

See CONTRACT §12.4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from luana_core_copilot.domain.skills.skill_definition import SkillDefinition


class SkillLoadError(Exception):
    """Raised when a skill ``.md`` file fails frontmatter validation."""

    def __init__(self, path: str, reason: str) -> None:
        """Store path + underlying reason for debugging."""
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


@runtime_checkable
class SkillRegistry(Protocol):
    """Port for the in-memory skill index (tenant-aware)."""

    def get(
        self,
        name: str,
        *,
        tenant_id: str | None = None,
    ) -> SkillDefinition | None:
        """Return a skill definition by kebab-case name (or None if absent)."""
        ...

    def by_slash_command(
        self,
        slug: str,
        *,
        tenant_id: str | None = None,
    ) -> SkillDefinition | None:
        """Return the skill bound to a slash command slug (or None)."""
        ...

    def search_by_keyword(
        self,
        text: str,
        *,
        tenant_id: str | None = None,
    ) -> list[SkillDefinition]:
        """Rank skills whose trigger keywords overlap ``text`` and return them."""
        ...

    def all(self, *, tenant_id: str | None = None) -> list[SkillDefinition]:
        """Return every loaded skill (system + tenant overrides when applicable)."""
        ...

    def for_slash_autocomplete(
        self,
        *,
        tenant_id: str | None = None,
    ) -> list[SkillDefinition]:
        """Return skills suitable for the slash-command autocomplete dropdown."""
        ...
