"""FileSkillsLoader — load skills from ``.md`` files with YAML frontmatter.

See CONTRACT §12.5.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import frontmatter
import structlog

from src.modules.copilot.domain.skills.skill_definition import SkillDefinition
from src.modules.copilot.domain.skills.skill_metadata import SkillMetadata
from src.modules.copilot.domain.skills.skill_registry import SkillLoadError
from src.modules.copilot.infrastructure.in_memory_skill_registry import (
    InMemorySkillRegistry,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger()


class FileSkillsLoader:
    """Load skill ``.md`` files into an :class:`InMemorySkillRegistry`.

    Strict: every file must have valid frontmatter per ``SkillMetadata``
    schema. One invalid file aborts the load (fail-fast).
    """

    def __init__(self, skills_dir: Path) -> None:
        """Set the directory to scan for ``.md`` skill files."""
        self.skills_dir = skills_dir

    def load_all(self) -> InMemorySkillRegistry:
        """Walk ``skills_dir`` and return a populated registry.

        Raises :class:`SkillLoadError` on any invalid file.
        """
        registry = InMemorySkillRegistry()

        if not self.skills_dir.exists():
            logger.warning(
                "skills_dir_missing",
                path=str(self.skills_dir),
                hint="No system skills will be available.",
            )
            return registry

        for md_path in sorted(self.skills_dir.glob("*.md")):
            try:
                post = frontmatter.load(md_path)
            except Exception as exc:  # surface parser error path + reason
                raise SkillLoadError(str(md_path), f"frontmatter parse failed: {exc}") from exc

            try:
                metadata = SkillMetadata.model_validate(post.metadata)
            except Exception as exc:  # surface validation error path + reason
                raise SkillLoadError(str(md_path), f"metadata validation failed: {exc}") from exc

            definition = SkillDefinition(
                metadata=metadata,
                body_markdown=post.content,
                source_path=md_path,
            )
            registry.add(definition)
            logger.debug("skill_loaded", name=metadata.name, path=str(md_path))

        logger.info("skills_loaded", count=len(registry.all()))
        return registry
