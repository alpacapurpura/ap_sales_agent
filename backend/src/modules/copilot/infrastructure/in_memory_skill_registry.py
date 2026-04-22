"""InMemorySkillRegistry — dict-backed SkillRegistry implementation.

See CONTRACT §12.4.
"""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.copilot.domain.skills.skill_definition import SkillDefinition


def _fold(text: str) -> str:
    """Lowercase + strip accents."""
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


class InMemorySkillRegistry:
    """Dict-backed skill registry keyed by (tenant_id, skill_name).

    ``tenant_id=None`` means system skill. Lookups prefer tenant override
    when both exist.
    """

    def __init__(self) -> None:
        """Start empty. Populate via ``add``.

        Storage: ``_by_key`` keyed by ``(tenant_id_or_None, name)`` and
        ``_by_slash`` keyed by slug then ``tenant_id_or_None``.
        """
        self._by_key: dict[tuple[str | None, str], SkillDefinition] = {}
        self._by_slash: dict[str, dict[str | None, SkillDefinition]] = {}

    def add(self, skill: SkillDefinition) -> None:
        """Register a skill. Raises on duplicate (tenant, name) or slash collision."""
        key = (skill.tenant_id, skill.metadata.name)
        if key in self._by_key:
            msg = f"duplicate skill: {skill.metadata.name} (tenant={skill.tenant_id})"
            raise ValueError(msg)
        self._by_key[key] = skill

        slash = skill.metadata.slash_command
        if slash is not None:
            existing = self._by_slash.setdefault(slash, {})
            if skill.tenant_id in existing:
                msg = f"duplicate slash_command {slash!r} for tenant {skill.tenant_id}"
                raise ValueError(msg)
            existing[skill.tenant_id] = skill

    def get(
        self,
        name: str,
        *,
        tenant_id: str | None = None,
    ) -> SkillDefinition | None:
        """Return the skill by name — tenant override first, system fallback."""
        if tenant_id is not None:
            override = self._by_key.get((tenant_id, name))
            if override is not None:
                return override
        return self._by_key.get((None, name))

    def by_slash_command(
        self,
        slug: str,
        *,
        tenant_id: str | None = None,
    ) -> SkillDefinition | None:
        """Return the skill bound to ``slug`` (tenant override first)."""
        bucket = self._by_slash.get(slug)
        if not bucket:
            return None
        if tenant_id is not None and tenant_id in bucket:
            return bucket[tenant_id]
        return bucket.get(None)

    def search_by_keyword(
        self,
        text: str,
        *,
        tenant_id: str | None = None,
    ) -> list[SkillDefinition]:
        """Rank skills whose trigger_keywords overlap ``text``."""
        folded = _fold(text)
        scored: list[tuple[float, SkillDefinition]] = []
        for skill in self._visible(tenant_id=tenant_id):
            hits = 0
            for kw in skill.metadata.trigger_keywords:
                if _fold(kw) in folded:
                    hits += 1
            if hits > 0:
                score = min(1.0, 0.6 + 0.1 * hits)
                scored.append((score, skill))
        scored.sort(key=lambda pair: (-pair[0], pair[1].metadata.name))
        return [s for _, s in scored]

    def all(self, *, tenant_id: str | None = None) -> list[SkillDefinition]:
        """Return every visible skill (system + tenant overrides)."""
        return list(self._visible(tenant_id=tenant_id))

    def for_slash_autocomplete(
        self,
        *,
        tenant_id: str | None = None,
    ) -> list[SkillDefinition]:
        """Return skills that expose a slash command, alpha-sorted by slug."""
        visible = self._visible(tenant_id=tenant_id)
        with_slash = [s for s in visible if s.metadata.slash_command]
        with_slash.sort(key=lambda s: s.metadata.slash_command or "")
        return with_slash

    def _visible(
        self,
        *,
        tenant_id: str | None,
    ) -> list[SkillDefinition]:
        """Compose tenant override + system skills (override wins per name)."""
        out: dict[str, SkillDefinition] = {}
        # System skills first.
        for (t, name), skill in self._by_key.items():
            if t is None:
                out[name] = skill
        # Tenant overrides last (wins).
        if tenant_id is not None:
            for (t, name), skill in self._by_key.items():
                if t == tenant_id:
                    out[name] = skill
        return list(out.values())
