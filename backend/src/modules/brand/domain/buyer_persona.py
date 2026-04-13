"""BuyerPersona domain entity — rich buyer persona that replaces lightweight Avatar."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

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
    demographics: dict = {}
    psychographics: dict = {}
    pain_points: list[dict] = []
    desires: list[dict] = []
    objections: list[dict] = []
    preferred_channels: list[dict] = []
    buyer_journey: dict = {}
    purchase_triggers: list[str] = []
    anti_patterns: list[str] = []

    # Metadata
    completeness_score: float = 0.0
    interview_session_id: UUID | None = None

    # Soft delete
    is_active: bool = True
    deleted_at: datetime | None = None
