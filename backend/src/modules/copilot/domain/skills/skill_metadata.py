"""SkillMetadata — strict YAML frontmatter schema for skill ``.md`` files.

See CONTRACT §12.2.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.modules.copilot.domain.model_tier import ModelTier

SkillOutputFormat = Literal["free", "structured", "procedure"]


class SkillMetadata(BaseModel):
    """Strict YAML frontmatter schema for a skill ``.md`` file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9-]*$",
    )
    description: str = Field(min_length=1, max_length=200)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    trigger_keywords: tuple[str, ...] = Field(default_factory=tuple)
    slash_command: str | None = Field(
        default=None,
        pattern=r"^/[a-z][a-z0-9-]*$",
        max_length=48,
    )
    allowed_tools: tuple[str, ...] = Field(default_factory=tuple)
    preferred_tier: ModelTier = ModelTier.MINI
    required_context: tuple[str, ...] = Field(default_factory=tuple)
    output_format: SkillOutputFormat = "free"
    procedure_id: str | None = None
    author: str = "nicolify"
    tenant_editable: bool = False
    requires_plan: bool = False

    @field_validator("allowed_tools")
    @classmethod
    def _no_wildcards(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        """``allowed_tools`` may never contain a wildcard or glob entry."""
        for entry in v:
            if entry == "*" or "*" in entry:
                msg = "allowed_tools may not contain wildcards"
                raise ValueError(msg)
        return v
