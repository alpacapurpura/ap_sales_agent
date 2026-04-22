"""ToolDescriptor — plugin-registered tool metadata.

See CONTRACT §18.1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ToolCategory = Literal["builtin", "procedure", "provider", "skill"]


class ToolDescriptor(BaseModel):
    """Plugin-registered tool metadata.

    Thin superset of the LangChain ``@tool`` contract. The actual callable
    lives under ``handler``; the descriptor is wire-visible and used for
    route/category-based tool selection and introspection.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=1, max_length=400)
    category: ToolCategory
    routes: tuple[str, ...] = Field(default_factory=tuple)
    required_scopes: tuple[str, ...] = Field(default_factory=tuple)
    procedure_ids: tuple[str, ...] = Field(default_factory=tuple)
    skill_names: tuple[str, ...] = Field(default_factory=tuple)
    provider: str | None = None
    dangerous: bool = False
    ui_action_types: tuple[str, ...] = Field(default_factory=tuple)
    handler: object = None

    @field_validator("routes", "procedure_ids", "skill_names", "required_scopes")
    @classmethod
    def _no_wildcards(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        """Reject glob/wildcard entries in any tuple-of-strings field."""
        for entry in v:
            if entry == "*" or "*" in entry:
                msg = f"wildcards are not permitted: {entry!r}"
                raise ValueError(msg)
        return v
