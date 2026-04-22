"""RuleMetadata — strict YAML frontmatter schema for rule ``.md`` files.

See CONTRACT §13.2.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RuleMetadata(BaseModel):
    """Strict YAML frontmatter schema for a rule ``.md`` file.

    Scope grammar:
      - ``global`` — always loaded.
      - ``route:<prefix>`` — loaded when current route matches prefix.
      - ``skill:<name>`` — loaded only when skill ``<name>`` is active.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9-]*$",
    )
    description: str = Field(min_length=1, max_length=200)
    scope: str = Field(
        pattern=r"^(global|route:[a-z0-9/-]+|skill:[a-z0-9-]+)$",
    )
    priority: int = Field(ge=0, le=100)
    enforceable: bool = False
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
