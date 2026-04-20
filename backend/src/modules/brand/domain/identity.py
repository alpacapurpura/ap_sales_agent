"""Brand identity value objects.

``business_types`` was removed from this model in Sprint 2026-04-20 and
migrated to the ``tenant_profile`` bounded context (``TenantProfile`` aggregate,
``tenant_profiles`` table). Consumers that previously read
``BrandIdentity.business_types`` must switch to the port at
``shared/links/ports/tenant_profile.py``.

Migration 052 backfills the data; migration 053 strips the stale JSONB key.
"""

from typing import Any

from pydantic import ConfigDict, Field

from src.shared.domain.base_entity import BaseEntity


class BrandVisuals(BaseEntity):
    """Represent brand visuals data."""

    # === COLORES (core) ===
    primary_color: str | None = None
    secondary_color: str | None = None  # 2nd brand color (sections, headers)
    accent_color: str | None = None
    background_color: str | None = None
    surface_color: str | None = None  # Card/modal background
    text_primary_color: str | None = None
    text_secondary_color: str | None = None  # Subtitles, captions
    text_on_primary: str | None = None
    text_on_secondary: str | None = None  # Text on secondary color

    # === COLORES (extended) ===
    color_palette: list[str] = Field(default_factory=list)
    neutral_colors: list[str] = Field(default_factory=list)
    semantic_colors: dict[str, str | None] | None = None  # {success, error, warning, info}
    gradient_definitions: list[str] = Field(
        default_factory=list,
    )  # CSS gradient strings
    color_usage_rules: str | None = None  # 60-30-10 distribution rules

    # === TYPOGRAPHY ===
    font_heading: str | None = None
    font_body: str | None = None
    font_accent: str | None = None  # Decorative/display font
    font_weights: dict[str, Any] | None = None  # {heading: [700,600], body: [400]}
    typography_scale: dict[str, str] | None = None  # {h1: "48px", body: "16px"}

    # === DESIGN SYSTEM ===
    border_radius_style: str | None = None  # "rounded", "sharp", "pill", "mixed"
    border_radius_values: dict[str, str] | None = None  # {sm: "4px", md: "8px"}
    shadow_style: str | None = None  # none|subtle|moderate|prominent
    spacing_base: str | None = None  # "8px"
    visual_density: str | None = None  # compact|comfortable|spacious

    # === VISUAL PERSONALITY ===
    brand_mood: dict[str, Any] | None = None  # {adjectives: [...], energy: "high"}
    visual_references: str | None = None  # "Similar a Apple + Stripe"
    photography_style: str | None = None  # lifestyle|product|abstract|minimal
    icon_style: str | None = None  # outlined|filled|duotone

    # === STYLE ===
    style_preset: str | None = None
    design_style: str | None = None
    usage_guidelines: list[str] = Field(default_factory=list)

    # === ASSETS ===
    logo_url: str | None = None
    favicon_url: str | None = None
    images: list[str] = Field(default_factory=list)
    logos: dict[str, str | None] | None = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BrandIdentity(BaseEntity):
    """Represent the core identity of the brand.

    Visual aspects are delegated to BrandVisuals.

    Note: ``business_types`` is NOT part of this model (removed Sprint 2026-04-20).
    It lives in ``TenantProfile`` (``tenant_profiles`` table). Read it via
    ``shared/links/ports/tenant_profile.get_tenant_business_types()``.
    """

    # --- Identity ---
    brand_name: str | None = Field(None, description="The name of the brand.")
    industry: str | None = Field(
        None,
        description=(
            "Free-text sub-niche (e.g. 'yoga', 'finanzas personales'). "
            "Describes the niche; operational classification lives in TenantProfile."
        ),
    )
    tagline: str | None = Field(None, description="Brand tagline or slogan.")
    description: str | None = Field(
        None,
        description="Positioning statement (2-3 sentences).",
    )
    founding_year: str | None = Field(None, description="Year the brand was founded.")
    website: str | None = Field(None, description="Canonical website URL.")
    language: str | None = Field(
        None,
        description="Primary language code (e.g. 'es', 'en').",
    )
    timezone: str | None = Field(
        None,
        description="Operational timezone (e.g. 'America/Mexico_City').",
    )
    voice_tone: str | None = Field(
        None,
        description="Voice tone descriptors (e.g. 'conversacional, aspiracional').",
    )
    legal_name: str | None = Field(None, description="Legal entity name.")
    tax_id: str | None = Field(None, description="Tax ID (RFC, NIF, CUIT, EIN).")
    fiscal_address: str | None = Field(None, description="Fiscal address.")
    legal_representative: str | None = Field(
        None,
        description="Legal representative name.",
    )
    terms_url: str | None = Field(None, description="Terms and conditions URL.")
    privacy_url: str | None = Field(None, description="Privacy policy URL.")

    model_config = ConfigDict(extra="allow")
