"""BuyerPersona API DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BuyerPersonaCreateDTO(BaseModel):
    """Create a new buyer persona (shell — just a name)."""

    name: str
    tagline: str | None = None
    scope: str = "GLOBAL"
    offer_id: UUID | None = None


class BuyerPersonaSectionUpdateDTO(BaseModel):
    """PATCH parcial — only sent fields are updated."""

    name: str | None = None
    tagline: str | None = None
    demographics: dict[str, Any] | None = None
    psychographics: dict[str, Any] | None = None
    pain_points: list[dict[str, Any]] | None = None
    desires: list[dict[str, Any]] | None = None
    objections: list[dict[str, Any]] | None = None
    preferred_channels: list[dict[str, Any]] | None = None
    buyer_journey: dict[str, Any] | None = None
    purchase_triggers: list[str] | None = None
    anti_patterns: list[str] | None = None


class BuyerPersonaResponseDTO(BaseModel):
    """Full buyer persona response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    tagline: str | None
    scope: str
    is_primary: bool
    demographics: dict[str, Any]
    psychographics: dict[str, Any]
    pain_points: list[dict[str, Any]]
    desires: list[dict[str, Any]]
    objections: list[dict[str, Any]]
    preferred_channels: list[dict[str, Any]]
    buyer_journey: dict[str, Any]
    purchase_triggers: list[str]
    anti_patterns: list[str]
    completeness_score: float
    interview_session_id: UUID | None
    created_at: datetime
    updated_at: datetime
