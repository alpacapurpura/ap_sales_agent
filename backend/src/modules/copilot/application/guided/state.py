"""Guided setup state — persisted inside conversation.procedure_state["guided"].

Lightweight dataclass + JSON (de)serialisation. No ORM, no migration — the
state lives inside a JSONB column we already own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

GUIDED_STATE_KEY = "guided"


@dataclass(slots=True)
class GuidedState:
    """Active guided-setup run for a copilot conversation."""

    domain: str
    entity_id: str | None
    current_block_id: str
    completed_blocks: list[str] = field(default_factory=list)
    started_at: str = ""

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> GuidedState | None:
        """Return a ``GuidedState`` from a JSON dict, or ``None`` if malformed."""
        if not data or not isinstance(data, dict):
            return None
        domain = data.get("domain")
        current = data.get("current_block_id")
        if not domain or not current:
            return None
        return cls(
            domain=str(domain),
            entity_id=(str(data["entity_id"]) if data.get("entity_id") else None),
            current_block_id=str(current),
            completed_blocks=[str(b) for b in data.get("completed_blocks", [])],
            started_at=str(data.get("started_at", "")),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "domain": self.domain,
            "entity_id": self.entity_id,
            "current_block_id": self.current_block_id,
            "completed_blocks": list(self.completed_blocks),
            "started_at": self.started_at,
        }


def load_guided_state(procedure_state: dict[str, Any] | None) -> GuidedState | None:
    """Extract the guided state from the raw ``procedure_state`` JSONB payload."""
    if not procedure_state or not isinstance(procedure_state, dict):
        return None
    return GuidedState.from_json(procedure_state.get(GUIDED_STATE_KEY))


def merge_guided_state(
    procedure_state: dict[str, Any] | None,
    state: GuidedState | None,
) -> dict[str, Any]:
    """Return a new ``procedure_state`` dict with ``guided`` set or removed.

    Preserves any sibling keys (e.g. the legacy procedures' state) so the two
    subsystems can coexist during the transition.
    """
    current = dict(procedure_state) if procedure_state else {}
    if state is None:
        current.pop(GUIDED_STATE_KEY, None)
    else:
        current[GUIDED_STATE_KEY] = state.to_json()
    return current
