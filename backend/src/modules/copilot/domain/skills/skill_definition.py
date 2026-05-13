"""SkillDefinition — loaded skill artifact (metadata + body + source path)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from luana_core_copilot.domain.skills.skill_metadata import SkillMetadata


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """In-memory representation of a skill ``.md`` file."""

    metadata: SkillMetadata
    body_markdown: str
    source_path: Path
    tenant_id: str | None = None
    jinja2_template_path: Path | None = None
