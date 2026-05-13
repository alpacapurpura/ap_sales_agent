"""CRM contacts filter parameters — forward-compat schema.

PR-10 PI-1 S4: FilterParams declara TODOS los filtros PI-3 desde día 1.
UI lite consume subset; PI-3 expande UI sin tocar BE.

INVARIANTE arch-test (forward_compat): este schema MUST contener TODOS los
filtros listados en CANONICAL_FILTER_FIELDS del arch test.
Ratchet shrink-only — futuro adds OK; remove FAIL test.
"""

from __future__ import annotations

from datetime import datetime

from luana_core_platform.domain.enums import LifecycleStage
from pydantic import BaseModel, ConfigDict, Field


class ContactFilterParams(BaseModel):
    """Forward-compat filter schema. UI lite consume subset; PI-3 expande UI sin tocar BE.

    INVARIANTE arch-test (forward_compat): este schema MUST contener TODOS los
    filtros listados en CANONICAL_FILTER_FIELDS abajo. Ratchet shrink-only —
    futuro adds OK; remove FAIL test.
    """

    model_config = ConfigDict(extra="forbid")

    # ── Lifecycle / scoring ───────────────────────────────────────────────────
    lifecycle_stage_in: list[LifecycleStage] | None = Field(
        default=None,
        description="Filtra por uno o más lifecycle stages.",
    )
    score_min: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="lead_score mínimo (CustomerProfile).",
    )
    score_max: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="lead_score máximo (CustomerProfile).",
    )

    # ── Source / acquisition ──────────────────────────────────────────────────
    source_in: list[str] | None = Field(
        default=None,
        description="Filtra por lead_source string.",
    )

    # ── Identity presence ─────────────────────────────────────────────────────
    has_email: bool | None = Field(
        default=None,
        description="Solo contactos con primary_email no nulo.",
    )
    has_phone: bool | None = Field(
        default=None,
        description="Solo contactos con primary_phone no nulo.",
    )
    has_telegram_id: bool | None = Field(
        default=None,
        description="Solo contactos con Lead.telegram_id no nulo.",
    )
    has_whatsapp_id: bool | None = Field(
        default=None,
        description="Solo contactos con Lead.whatsapp_id no nulo.",
    )
    has_instagram_id: bool | None = Field(
        default=None,
        description="Solo contactos con Lead.instagram_id no nulo.",
    )
    has_tiktok_id: bool | None = Field(
        default=None,
        description="Solo contactos con Lead.tiktok_id no nulo.",
    )

    # ── Activity / temporal ───────────────────────────────────────────────────
    created_after: datetime | None = Field(
        default=None,
        description="Filtra contactos creados después de esta fecha (inclusive).",
    )
    created_before: datetime | None = Field(
        default=None,
        description="Filtra contactos creados antes de esta fecha (inclusive).",
    )
    last_activity_after: datetime | None = Field(
        default=None,
        description="Filtra contactos con última actividad después de esta fecha.",
    )
    last_activity_before: datetime | None = Field(
        default=None,
        description="Filtra contactos con última actividad antes de esta fecha.",
    )
    is_inactive: bool | None = Field(
        default=None,
        description="CustomerProfile.is_inactive flag.",
    )

    # ── Engagement (cross-module via CampaignsLookupPort) ─────────────────────
    has_campaign_engagement: bool | None = Field(
        default=None,
        description="True si lead recibió >=1 CampaignTask SENT en últimos 90 días.",
    )

    # ── Geographic ────────────────────────────────────────────────────────────
    country_in: list[str] | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 lowercase (ej. 'mx', 'pe', 'co').",
    )

    # ── Search ────────────────────────────────────────────────────────────────
    q: str | None = Field(
        default=None,
        max_length=120,
        description="Búsqueda por full_name, primary_email o primary_phone (ILIKE).",
    )
