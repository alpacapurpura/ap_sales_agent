"""Copilot skills plugin domain types."""

from luana_core_copilot.domain.skills.skill_definition import SkillDefinition
from luana_core_copilot.domain.skills.skill_metadata import (
    SkillMetadata,
    SkillOutputFormat,
)
from luana_core_copilot.domain.skills.skill_registry import (
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
