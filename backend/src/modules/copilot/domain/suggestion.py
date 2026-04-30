"""Domain value objects for copilot suggestion engine.

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class SuggestionCategory(StrEnum):
    """Mirrors FE locked TS union: "followup" | "action" | "clarify" | "nav".

    SSoT — ``frontend/src/features/copilot/types/suggestions.ts:Suggestion.category``.
    """

    FOLLOWUP = "followup"
    ACTION = "action"
    CLARIFY = "clarify"
    NAV = "nav"


@dataclass(frozen=True, slots=True)
class SuggestionContext:
    """Runtime input the engine dispatches to providers.

    Tenant-scoped. ``current_route`` is the FE route slug (``brand-studio``,
    ``offer-studio/{id}``, …). ``recent_message_ids`` enables future LLM-driven
    providers (PI-2 S2+) without breaking interface; heuristic providers ignore.
    """

    tenant_id: UUID
    user_id: UUID | None
    conversation_id: UUID | None
    current_route: str | None
    recent_message_ids: tuple[UUID, ...] = ()
    incomplete_fields: tuple[str, ...] = ()
    locale: str = "es"


@dataclass(frozen=True, slots=True)
class Suggestion:
    """Smart-chip surfaced under chat input.

    Shape MIRRORS FE locked contract (``frontend/.../types/suggestions.ts``):
      - id (UUID, stable within turn)
      - label (≤60 chars, español neutro LatAm)
      - prompt (filled into input on click)
      - confidence ∈ [0,1] (heuristic score; renamed to ``confidence`` in API DTO)
      - category (SuggestionCategory)

    Domain extension fields (NOT exposed in API to FE):
      - source_module (which provider produced it; for telemetry)
      - metadata (provider-private payload; sanitized before persistence)
    """

    id: UUID = field(default_factory=uuid4)
    label: str = ""
    prompt: str = ""
    confidence: float = 0.0
    category: SuggestionCategory = SuggestionCategory.ACTION
    source_module: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Domain invariants — fail fast if provider produces garbage."""
        if not (0.0 <= self.confidence <= 1.0):
            msg = f"confidence must be in [0,1], got {self.confidence}"
            raise ValueError(msg)
        if len(self.label) > 60:
            msg = f"label exceeds 60 chars: {self.label[:60]}…"
            raise ValueError(msg)
        if not self.label.strip() or not self.prompt.strip():
            msg = "label and prompt are required"
            raise ValueError(msg)


__all__ = [
    "Suggestion",
    "SuggestionCategory",
    "SuggestionContext",
]
