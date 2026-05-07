"""ActorProfile — Strands ActorProfile pattern (AWS Evals).

Decisión D7 (spec): Story B entrega CLASE COMPLETA + 1 hardcoded fixture
(creado en T-9). Story C extiende a YAML multi-persona loader.

Public — exported via simulator/__init__.py per H9 (T-9 finaliza el surface).

Schema versioning H1 (forward-compat):
- `schema_version: int = 1` field obligatorio
- bumps requieren entry en SCHEMA_MIGRATIONS registry
  (`_internal/schema_migrations.py`)

Voice constraints:
- `dialect_code` BCP-47 — `es-AR` permite voseo (escape rule magic comment
  para pre-commit hook); resto neutro tuteo.
- `communication_style` libre — voseo permitido SOLO si dialect_code='es-AR'.

# voseo-allowed: actor persona dialect injection (este módulo cita ejemplos
# del glosario para tests + fixtures regional argentine personas)
"""

# NO `from __future__ import annotations` — explicit cement (story-wide,
# referenced en sales-agent-expert §3 + spec D4).

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ActorProfile(BaseModel):
    """User persona profile — `traits + context + actor_goal` per AWS Strands pattern.

    Story B: 1 hardcoded fixture (created in T-9). Pydantic class complete + minimal
    YAML loader stub (T-9). Story C extends to multi-persona YAML loader bajo
    `docs/specs/personas/*.yaml`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = 1
    """Forward-compat versioning per H1 — bumps register migrator in SCHEMA_MIGRATIONS."""

    id: str = Field(min_length=1)
    """Stable hash for `simulation_id` derivation (UUID5 namespace seed)."""

    name: str = Field(min_length=1)
    """Display name (used by customer prompt + transcript metadata)."""

    actor_goal: str = Field(min_length=1)
    """Hidden goal — NUNCA revelar directamente al agent (defense H10)."""

    dialect_code: str = "es-419"
    """BCP-47 dialect — `es-AR` enables voseo in `communication_style` strings."""

    traits: list[str] = Field(default_factory=list)
    """Persona traits libre-form (`impaciente`, `analítica`, `casual`, etc.)."""

    pain_points: list[str] = Field(default_factory=list)
    """Customer pain bullets driving conversation."""

    objections: list[str] = Field(default_factory=list)
    """Likely objections customer voices to agent."""

    budget_hint: str = ""
    """Free-form hint (`limitado` | `medio` | `alto` | empty for inference)."""

    urgency: Literal["low", "medium", "high"] = "medium"
    """Urgency tier driving customer decision pace."""

    communication_style: str = ""
    """Style description — voseo permitted only if `dialect_code == 'es-AR'`."""

    initial_message: str = Field(min_length=1)
    """Verbatim turn-0 customer message (NO LLM call for opening)."""

    persona_kind: Literal["happy", "edge", "negative", "adversarial"] = "happy"
    """Scenario classification per spec — drives default fixtures + scenario routing."""

    metadata: dict[str, str] = Field(default_factory=dict)
    """Free-form key/value tags (provenance, source, version notes)."""


__all__ = ["ActorProfile"]
