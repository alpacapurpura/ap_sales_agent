"""RuleDefinition — loaded rule artifact (metadata + body + source path)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from luana_core_copilot.domain.rules.rule_metadata import RuleMetadata


@dataclass(frozen=True, slots=True)
class RuleDefinition:
    """In-memory representation of a rule ``.md`` file."""

    metadata: RuleMetadata
    body_markdown: str
    source_path: Path
