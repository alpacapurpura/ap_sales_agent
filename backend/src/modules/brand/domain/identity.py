"""Brand identity value objects."""

from typing import Any

from pydantic import ConfigDict, Field, field_validator

from src.shared.domain.base_entity import BaseEntity
from src.shared.domain.expert_business_type import ExpertBusinessType

# Legacy → canonical business_types remapping. The enum evolved during
# Sprint 11 (pre-Latam) and Sprint 12 (post-expansion). Tenants whose
# config_json was saved under the legacy vocabulary must still load
# without raising — the validator maps old values, drops unknowns.
#
# When this table converges to empty + a data migration clears the DB,
# remove the entire normalization block. Keeping it longer than one
# release cycle is acceptable as a defence-in-depth against unseen
# snapshots.
_LEGACY_BUSINESS_TYPE_ALIASES: dict[str, str] = {
    "consultor_asesor": ExpertBusinessType.CONSULTOR_PROFESIONAL.value,
    "educador_infoproductor": ExpertBusinessType.ACADEMIA_INFOPRODUCTOR.value,
    "creador_contenido": ExpertBusinessType.ACADEMIA_INFOPRODUCTOR.value,
    # Add future renames here. Unknown values fall through to the `None`
    # branch in the validator and are dropped silently.
}


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
    """

    # --- Identity ---
    brand_name: str | None = Field(None, description="The name of the brand.")
    industry: str | None = Field(
        None,
        description="Free-text sub-niche (e.g. 'yoga', 'finanzas personales'). "
        "Complements ``business_types`` — does not replace it.",
    )
    business_types: list[ExpertBusinessType] = Field(
        default_factory=list,
        description=(
            "Multi-select: the kinds of expert business this tenant runs. "
            "Captured in Brand Studio onboarding, editable in general settings. "
            "Drives format suitability in the Offer Studio wizard."
        ),
    )

    @field_validator("business_types", mode="before")
    @classmethod
    def _normalise_business_types(cls, value: object) -> list[str] | object:
        """Remap legacy strings and drop unknowns on read.

        Tenants whose ``config_json`` was saved with the pre-Sprint-11
        vocabulary (``consultor_asesor``, ``educador_infoproductor``,
        ``creador_contenido``) would otherwise fail enum validation and
        break every brand-settings read. We translate known legacy values
        to their current canonical form and silently drop anything else
        so the onboarding dialog can still load + let the tenant re-save
        a clean list.

        Values that are already canonical pass through untouched.
        """
        if not isinstance(value, list):
            return value
        valid = {member.value for member in ExpertBusinessType}
        cleaned: list[str] = []
        for raw in value:
            if not isinstance(raw, str):
                continue
            if raw in valid:
                cleaned.append(raw)
                continue
            aliased = _LEGACY_BUSINESS_TYPE_ALIASES.get(raw)
            if aliased is not None and aliased not in cleaned:
                cleaned.append(aliased)
            # Silent drop for unknowns — we prefer a partial load to a
            # crashed onboarding flow.
        return cleaned

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
