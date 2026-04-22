"""FileRulesLoader — load behavioral rules from ``.md`` files with YAML frontmatter.

See CONTRACT §13.4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import frontmatter
import structlog

from src.modules.copilot.domain.rules.rule_definition import RuleDefinition
from src.modules.copilot.domain.rules.rule_metadata import RuleMetadata
from src.modules.copilot.domain.skills.skill_registry import SkillLoadError
from src.modules.copilot.infrastructure.in_memory_rule_registry import (
    InMemoryRuleRegistry,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger()


class RuleLoadError(SkillLoadError):
    """Raised when a rule ``.md`` file fails frontmatter validation."""


class FileRulesLoader:
    """Load rule ``.md`` files into an :class:`InMemoryRuleRegistry`.

    Strict: every file must validate against :class:`RuleMetadata`.
    One invalid file aborts the load (fail-fast).
    """

    def __init__(self, rules_dir: Path) -> None:
        """Set the directory to scan for ``.md`` rule files."""
        self.rules_dir = rules_dir

    def load_all(self) -> InMemoryRuleRegistry:
        """Walk ``rules_dir`` and return a populated registry.

        Raises :class:`RuleLoadError` on any invalid file.
        """
        registry = InMemoryRuleRegistry()

        if not self.rules_dir.exists():
            logger.warning(
                "rules_dir_missing",
                path=str(self.rules_dir),
                hint="No system rules will be applied.",
            )
            return registry

        for md_path in sorted(self.rules_dir.glob("*.md")):
            try:
                post = frontmatter.load(md_path)
            except Exception as exc:
                raise RuleLoadError(str(md_path), f"frontmatter parse failed: {exc}") from exc

            try:
                metadata = RuleMetadata.model_validate(post.metadata)
            except Exception as exc:
                raise RuleLoadError(str(md_path), f"metadata validation failed: {exc}") from exc

            definition = RuleDefinition(
                metadata=metadata,
                body_markdown=post.content,
                source_path=md_path,
            )
            registry.add(definition)
            logger.debug("rule_loaded", name=metadata.name, scope=metadata.scope)

        logger.info("rules_loaded", count=len(registry.all()))
        return registry
