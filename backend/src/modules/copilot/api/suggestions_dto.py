"""DTOs for the copilot suggestions API.

# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SuggestionsRequest(BaseModel):
    """Body para POST /api/v1/copilot/suggestions.

    Tenant scope viene del header X-Tenant-ID (Depends(get_tenant_context)).
    user_id viene de Depends(get_current_user). NO duplicar en body (D-6 PII).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    conversation_id: UUID | None = Field(
        default=None,
        description="ID de la conversación activa. None = pre-conversación (chips vacíos por default).",
    )
    current_route: str | None = Field(
        default=None,
        max_length=200,
        description="Slug de ruta FE: 'brand-studio', 'offer-studio/{uuid}', 'growth-studio', etc.",
    )
    recent_message_ids: list[UUID] = Field(
        default_factory=list,
        max_length=20,
        description="IDs de últimos mensajes del turn (forward-compat providers LLM-driven). Cap=20.",
    )
    incomplete_fields: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Field paths incompletos (ej. 'promise.headline'). Cap=50 evita payloads abusivos.",
    )


class SuggestionDTO(BaseModel):
    """Smart-chip individual expuesta al FE.

    Mirror del Suggestion domain (suggestion.py) MINUS metadata
    (D-6: PII allowlist — provider internals no expuestos al FE).
    source_module SE incluye — necesario para accept event payload (D-6 override final).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str = Field(max_length=60, description="Texto visible (Spanish neutro LatAm).")
    prompt: str = Field(description="Texto que se inserta en el composer al click.")
    confidence: float = Field(ge=0.0, le=1.0, description="Heurístico 0..1 (D-7).")
    category: str = Field(description="Mirror StrEnum SuggestionCategory: 'followup'|'action'|'clarify'|'nav'.")
    source_module: str = Field(
        max_length=50,
        description=(
            "Provider id (slug interno público: 'offer'|'brand'|'sales_agent'|'copilot'). "
            "Necesario para accept event payload — NO PII (D-6 override final)."
        ),
    )
    # metadata sigue EXCLUIDO (puede contener URLs/IDs internos — D-6)


class SuggestionsResponse(BaseModel):
    """Respuesta de POST /api/v1/copilot/suggestions."""

    model_config = ConfigDict(from_attributes=True)

    suggestions: list[SuggestionDTO] = Field(
        description="Ordenadas desc por confidence. Capped a 5 (engine._DEFAULT_MAX_TOTAL)."
    )
    breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="provider_id -> count (telemetría agregada, NOT per-chip).",
    )
    latency_ms: int = Field(ge=0, description="Engine latency medido (excluye HTTP overhead).")


class SuggestionAcceptRequest(BaseModel):
    """Body para POST /api/v1/copilot/suggestions/accept (fire-and-forget)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    suggestion_id: UUID = Field(description="ID de la chip clickeada.")
    conversation_id: UUID | None = Field(
        default=None,
        description="Conv activa al click. None si user clickeó pre-conversación.",
    )
    current_route: str | None = Field(
        default=None,
        max_length=200,
        description="Ruta al momento del click (telemetría correlación).",
    )
    category: str = Field(
        max_length=20,
        description="Category de la suggestion (echo del SuggestionDTO.category).",
    )
    source_module: str = Field(
        max_length=50,
        description=(
            "Provider id de la suggestion (echo necesario — D-6). FE conoce desde SuggestionDTO.source_module."
        ),
    )
    accepted_at: datetime = Field(description="ISO 8601 UTC. FE genera client-side.")


class SuggestionAcceptResponse(BaseModel):
    """Respuesta de POST /accept (best-effort 202)."""

    model_config = ConfigDict(from_attributes=True)

    ok: bool = Field(description="True si event publicó al bus. False = warning interno; FE ignora.")


__all__ = [
    "SuggestionAcceptRequest",
    "SuggestionAcceptResponse",
    "SuggestionDTO",
    "SuggestionsRequest",
    "SuggestionsResponse",
]
