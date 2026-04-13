"""BuyerPersona domain entity — rich buyer persona that replaces lightweight Avatar."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.shared.domain.base_entity import BaseEntity


class BuyerPersona(BaseEntity):
    """Rich buyer persona entity built via the Interview Engine.

    Replaces the lightweight Avatar with a structured, interview-driven
    persona that captures demographics, psychographics, pain points,
    desires, objections, channel preferences, and the full buyer journey.

    Scope:
        GLOBAL  — applies to the entire brand
        OFFER   — specific to a single offer (linked via offer_id)
        CAMPAIGN — specific to a campaign
    """

    id: UUID
    tenant_id: UUID
    user_id: UUID
    name: str
    tagline: str | None = None
    scope: str = "GLOBAL"
    offer_id: UUID | None = None
    is_primary: bool = False

    # Profile (JSONB — flexible, evolves with interview)
    demographics: dict = Field(default_factory=dict)
    psychographics: dict = Field(default_factory=dict)
    pain_points: list[dict] = Field(default_factory=list)
    desires: list[dict] = Field(default_factory=list)
    objections: list[dict] = Field(default_factory=list)
    preferred_channels: list[dict] = Field(default_factory=list)
    buyer_journey: dict = Field(default_factory=dict)
    purchase_triggers: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)

    # Metadata
    completeness_score: float = 0.0
    interview_session_id: UUID | None = None

    # Soft delete
    is_active: bool = True
    deleted_at: datetime | None = None
