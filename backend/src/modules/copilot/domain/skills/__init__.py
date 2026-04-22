"""Copilot skills plugin domain types."""

from src.modules.copilot.domain.skills.skill_definition import SkillDefinition
from src.modules.copilot.domain.skills.skill_metadata import (
    SkillMetadata,
    SkillOutputFormat,
)
from src.modules.copilot.domain.skills.skill_registry import (
    SkillLoadError,
    SkillRegistry,
)

__all__ = [
    "SkillDefinition",
    "SkillLoadError",
    "SkillMetadata",
    "SkillOutputFormat",
    "SkillRegistry",
]
