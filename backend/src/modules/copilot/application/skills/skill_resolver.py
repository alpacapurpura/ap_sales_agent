"""SkillResolver — picks which skills to inject for a given turn.

Precedence (per CONTRACT §12.6):

  1. Explicit ``/slash-command`` → that skill, score 1.0.
  2. Otherwise, keyword overlap on ``trigger_keywords``.
  3. Result ranked + deduped, capped at ``limit``.

Semantic (Qdrant) matching is deferred to phase 2 (CONTRACT §12.6).
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.copilot.domain.skills.skill_definition import SkillDefinition
    from src.modules.copilot.domain.skills.skill_registry import SkillRegistry


_SLASH_RE = re.compile(r"^(?P<slug>/[a-z][a-z0-9-]*)\b", re.IGNORECASE)


def _fold(text: str) -> str:
    """Lowercase + strip accents for accent-insensitive matching."""
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


class SkillResolver:
    """Runtime skill picker."""

    def __init__(self, registry: SkillRegistry) -> None:
        """Store the registry reference."""
        self._registry = registry

    def resolve(
        self,
        user_message: str,
        slash_command: str | None = None,
        route: str | None = None,
        *,
        tenant_id: str | None = None,
        limit: int = 3,
    ) -> list[SkillDefinition]:
        """Return ranked skills for this turn (max ``limit``, deduped)."""
        explicit_slug = slash_command
        if explicit_slug is None:
            match = _SLASH_RE.match(user_message.strip())
            if match:
                explicit_slug = match.group("slug")

        if explicit_slug:
            skill = self._registry.by_slash_command(
                explicit_slug,
                tenant_id=tenant_id,
            )
            if skill is not None and self._route_allows(skill, route):
                return [skill]
            # Explicit slash with no match → caller sees empty list, orchestrator
            # can tell the user.
            return []

        # Keyword search fallback.
        folded = _fold(user_message)
        candidates = self._registry.search_by_keyword(
            folded,
            tenant_id=tenant_id,
        )

        seen: set[str] = set()
        results: list[SkillDefinition] = []
        for skill in candidates:
            if skill.metadata.name in seen:
                continue
            if not self._route_allows(skill, route):
                continue
            seen.add(skill.metadata.name)
            results.append(skill)
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _route_allows(skill: SkillDefinition, route: str | None) -> bool:
        """Future-proof hook: allow if skill has no route_scope constraint.

        ``SkillMetadata`` currently has no ``allowed_routes`` field — reserved
        for CONTRACT §14.1 when landed. Until then this is a permissive no-op.
        """
        # Placeholder for future allowed_routes metadata (CONTRACT §14.1).
        _ = (skill, route)
        return True
