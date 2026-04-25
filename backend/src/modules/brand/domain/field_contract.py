"""Brand FieldContract — declarative section map + overrides.

Post field-contract-platform refactor (Fase 06), this module declares
the semantic metadata Pydantic cannot express (section, copilot meta,
lifecycle, filters) for the Brand domain and delegates derivation to
``src.shared.domain.field_contract``.

The derived :data:`BRAND_FIELD_CONTRACTS` is the single source of
truth for every Brand consumer that needs to iterate fields:

- ``brand/domain/copilot_editable_fields.py`` (proyección)
- (futuro) sales-agent / landing builders consumiendo brand vars

Adding a new BrandSettings nested field requires:

1. Add ``"some.path": "section_slug"`` to :data:`BRAND_SECTION_MAP`.
2. (Optional) Add ``Override(...)`` in :data:`BRAND_FIELD_OVERRIDES`
   con ``human_question_es``, ``label_es``, ``priority``, ``can_propose``.

Buyer-persona vive como dominio independiente (registrado bajo la key
``"buyer_persona"``) y migra en Fase 07 — no se incluye aquí.

See ``docs/refactors/field-contract-platform/DESIGN.md``.
"""

from __future__ import annotations

from src.modules.brand.domain.aggregates import BrandSettings
from src.shared.domain.field_contract import FieldContractOverride as Override
from src.shared.domain.field_contract import (
    FieldStatus,
    derive_contracts_from_pydantic,
    register_module_contracts,
)

# ---------------------------------------------------------------------------
# Composable handles — top-level Pydantic sub-models walked 1 level deep
# ---------------------------------------------------------------------------

BRAND_COMPOSABLE_FIELDS: tuple[str, ...] = (
    "identity",
    "strategy",
    "story",
    "contact",
    "visuals",
    "positioning",
    "narrative",
    "communication_assets",
    "brand_personality",
)

# ---------------------------------------------------------------------------
# Ignore paths — system fields not user-facing
#
# BrandSettings extends BaseEntity which only sets Pydantic ConfigDict, so
# there are no audit columns to skip. Top-level lists (team, testimonials,
# authority_vault) ARE walked and emitted as LIST-typed contracts so the
# section_catalog COLLECTION pages have a contract entry to anchor.
# ---------------------------------------------------------------------------

BRAND_IGNORE_PATHS: frozenset[str] = frozenset()


# ---------------------------------------------------------------------------
# Section map — path → FE section slug
#
# Covers every BrandSettings Pydantic path user-facing. Sections align
# with the existing copilot catalog grouping (identity, story, positioning,
# narrative, methodology, personality, visuals, contact, legal) plus the
# COLLECTION sections from section_catalog (team, testimonials, authority,
# communication-assets).
#
# NB: ``brand_personality.*`` maps to ``personality`` (matching the
# legacy copilot catalog), not ``estilo`` (the section_catalog key for the
# editor block). Section unification is a future concern.
# ---------------------------------------------------------------------------

BRAND_SECTION_MAP: dict[str, str] = {
    # ── identity (BrandIdentity user-facing scalars) ────────────────
    "identity.brand_name": "identity",
    "identity.tagline": "identity",
    "identity.description": "identity",
    "identity.industry": "identity",
    "identity.website": "identity",
    "identity.founding_year": "identity",
    "identity.language": "identity",
    "identity.timezone": "identity",
    "identity.voice_tone": "identity",
    # ── legal (BrandIdentity legal/regulated/sales-agent guardrails) ─
    "identity.legal_name": "legal",
    "identity.legal_entity_type": "legal",
    "identity.tax_id": "legal",
    "identity.tax_regime": "legal",
    "identity.country_of_registration": "legal",
    "identity.commercial_registry_number": "legal",
    "identity.fiscal_address": "legal",
    "identity.legal_representative": "legal",
    "identity.legal_email": "legal",
    "identity.dpo_email": "legal",
    "identity.terms_url": "legal",
    "identity.privacy_url": "legal",
    "identity.cookies_url": "legal",
    "identity.refund_policy_url": "legal",
    "identity.acceptable_use_url": "legal",
    "identity.regulated_profession_body": "legal",
    "identity.professional_license_number": "legal",
    "identity.professional_license_holder": "legal",
    "identity.operating_authorization": "legal",
    "identity.liability_insurance_carrier": "legal",
    "identity.sales_agent_disclaimer": "legal",
    "identity.sales_agent_out_of_scope": "legal",
    "identity.escalation_contact": "legal",
    # ── methodology (BrandStrategy) ─────────────────────────────────
    "strategy.methodology_name": "methodology",
    "strategy.methodology_description": "methodology",
    "strategy.methodology_pillars": "methodology",
    # ── story (BrandStory) ──────────────────────────────────────────
    "story.origin_story": "story",
    "story.mission": "story",
    "story.vision": "story",
    "story.milestones": "story",
    "story.milestones_legacy": "story",
    # ── contact (BrandContact) ──────────────────────────────────────
    "contact.support_email": "contact",
    "contact.sales_email": "contact",
    "contact.phone": "contact",
    "contact.whatsapp": "contact",
    "contact.address": "contact",
    "contact.social_instagram": "contact",
    "contact.social_linkedin": "contact",
    "contact.social_youtube": "contact",
    "contact.social_tiktok": "contact",
    "contact.social_facebook": "contact",
    "contact.social_twitter": "contact",
    "contact.testimonials_url": "contact",
    "contact.email": "contact",
    "contact.social": "contact",
    # ── visuals (BrandVisuals — colors, typography, design system) ──
    "visuals.primary_color": "visuals",
    "visuals.secondary_color": "visuals",
    "visuals.accent_color": "visuals",
    "visuals.background_color": "visuals",
    "visuals.surface_color": "visuals",
    "visuals.text_primary_color": "visuals",
    "visuals.text_secondary_color": "visuals",
    "visuals.text_on_primary": "visuals",
    "visuals.text_on_secondary": "visuals",
    "visuals.color_palette": "visuals",
    "visuals.neutral_colors": "visuals",
    "visuals.semantic_colors": "visuals",
    "visuals.gradient_definitions": "visuals",
    "visuals.color_usage_rules": "visuals",
    "visuals.font_heading": "visuals",
    "visuals.font_body": "visuals",
    "visuals.font_accent": "visuals",
    "visuals.font_weights": "visuals",
    "visuals.typography_scale": "visuals",
    "visuals.border_radius_style": "visuals",
    "visuals.border_radius_values": "visuals",
    "visuals.shadow_style": "visuals",
    "visuals.spacing_base": "visuals",
    "visuals.visual_density": "visuals",
    "visuals.brand_mood": "visuals",
    "visuals.visual_references": "visuals",
    "visuals.photography_style": "visuals",
    "visuals.icon_style": "visuals",
    "visuals.style_preset": "visuals",
    "visuals.design_style": "visuals",
    "visuals.usage_guidelines": "visuals",
    "visuals.logo_url": "visuals",
    "visuals.favicon_url": "visuals",
    "visuals.images": "visuals",
    "visuals.logos": "visuals",
    # ── positioning (BrandPositioning) ──────────────────────────────
    "positioning.discriminator": "positioning",
    "positioning.brand_essence": "positioning",
    "positioning.unique_value_proposition": "positioning",
    "positioning.competitive_environment": "positioning",
    "positioning.insight": "positioning",
    "positioning.benefits": "positioning",
    "positioning.values": "positioning",
    "positioning.reasons_to_believe": "positioning",
    # ── narrative (BrandNarrative — StoryBrand) ─────────────────────
    "narrative.one_liner": "narrative",
    "narrative.hero": "narrative",
    "narrative.problem": "narrative",
    "narrative.guide": "narrative",
    "narrative.cta": "narrative",
    "narrative.outcome": "narrative",
    "narrative.plan": "narrative",
    # ── communication_assets (CommunicationAssets) ──────────────────
    "communication_assets.creative_concepts": "communication-assets",
    "communication_assets.assets": "communication-assets",
    "communication_assets.custom_asset_types": "communication-assets",
    # ── personality (BrandPersonality) ──────────────────────────────
    "brand_personality.archetype": "personality",
    "brand_personality.core_values": "personality",
    "brand_personality.personality_traits": "personality",
    # ── COLLECTION top-level lists (anchored for section_catalog) ───
    "team": "team",
    "testimonials": "testimonials",
    "authority_vault": "authority",
}


# ---------------------------------------------------------------------------
# Field overrides — semantic metadata Pydantic cannot express
#
# Marks ``can_propose=False`` for fields the copilot ``propose_field_updates``
# cannot meaningfully drive (nested OBJECT containers, lists of objects edited
# via form-runtime CRUD, deprecated legacy aliases, derived design-system
# tokens). Walker-derived defaults handle everything else.
# ---------------------------------------------------------------------------

BRAND_FIELD_OVERRIDES: dict[str, Override] = {
    # ── nested OBJECT containers (form-runtime edits children) ──────
    "positioning.competitive_environment": Override(can_propose=False),
    "positioning.insight": Override(can_propose=False),
    "positioning.benefits": Override(can_propose=False),
    "positioning.values": Override(can_propose=False),
    "narrative.hero": Override(can_propose=False),
    "narrative.problem": Override(can_propose=False),
    "narrative.guide": Override(can_propose=False),
    "narrative.cta": Override(can_propose=False),
    "narrative.outcome": Override(can_propose=False),
    # ── lists of structured objects (form-runtime CRUD) ─────────────
    "strategy.methodology_pillars": Override(can_propose=False),
    "story.milestones": Override(can_propose=False),
    "positioning.reasons_to_believe": Override(can_propose=False),
    "narrative.plan": Override(can_propose=False),
    "communication_assets.creative_concepts": Override(can_propose=False),
    "communication_assets.assets": Override(can_propose=False),
    "team": Override(can_propose=False),
    "testimonials": Override(can_propose=False),
    "authority_vault": Override(can_propose=False),
    # ── deprecated legacy aliases ───────────────────────────────────
    "story.milestones_legacy": Override(
        can_propose=False,
        status=FieldStatus.DEPRECATED,
        deprecated_in="2026-04-24-fase-06",
        replaced_by="story.milestones",
    ),
    "contact.email": Override(
        can_propose=False,
        status=FieldStatus.DEPRECATED,
        deprecated_in="2026-04-24-fase-06",
        replaced_by="contact.support_email",
    ),
    "contact.social": Override(
        can_propose=False,
        status=FieldStatus.DEPRECATED,
        deprecated_in="2026-04-24-fase-06",
        notes="Legacy social dict; use flat social_<provider> fields instead.",
    ),
    "identity.voice_tone": Override(
        can_propose=False,
        status=FieldStatus.DEPRECATED,
        deprecated_in="2026-04-24-fase-06",
        notes="Removed from Brand Studio UI; use brand_personality.* instead.",
    ),
    # ── derived design-system tokens (auto-generated, not LLM-proposed) ─
    "visuals.semantic_colors": Override(can_propose=False),
    "visuals.font_weights": Override(can_propose=False),
    "visuals.typography_scale": Override(can_propose=False),
    "visuals.border_radius_values": Override(can_propose=False),
    "visuals.brand_mood": Override(can_propose=False),
    "visuals.logos": Override(can_propose=False),
    # ── curated Spanish labels for byte-identical catalog UX ────────
    # Preserves the labels the legacy copilot catalog exposed, so the
    # system prompt enumeration reads identically post-Fase-06. Drift
    # B paths (catalog said `contact.legal_*`, Pydantic has `identity.legal_*`)
    # surface their original labels under the corrected path.
    "identity.brand_name": Override(label_es="Nombre"),
    "identity.tagline": Override(label_es="Tagline"),
    "identity.description": Override(label_es="Descripción"),
    "identity.industry": Override(label_es="Industria"),
    "identity.website": Override(label_es="Sitio web"),
    "identity.founding_year": Override(label_es="Año de fundación"),
    "identity.language": Override(label_es="Idioma"),
    "identity.timezone": Override(label_es="Zona horaria"),
    "identity.legal_name": Override(label_es="Razón social"),
    "identity.legal_entity_type": Override(label_es="Tipo de entidad legal"),
    "identity.tax_id": Override(label_es="ID fiscal"),
    "identity.tax_regime": Override(label_es="Régimen fiscal"),
    "identity.country_of_registration": Override(label_es="País de registro"),
    "identity.commercial_registry_number": Override(label_es="Número de registro comercial"),
    "identity.fiscal_address": Override(label_es="Dirección fiscal"),
    "identity.legal_representative": Override(label_es="Representante legal"),
    "identity.legal_email": Override(label_es="Email legal"),
    "identity.dpo_email": Override(label_es="Email DPO"),
    "identity.terms_url": Override(label_es="URL de términos"),
    "identity.privacy_url": Override(label_es="URL de privacidad"),
    "identity.cookies_url": Override(label_es="URL de cookies"),
    "identity.refund_policy_url": Override(label_es="URL política de reembolsos"),
    "identity.acceptable_use_url": Override(label_es="URL uso aceptable"),
    "identity.regulated_profession_body": Override(label_es="Organismo profesional regulado"),
    "identity.professional_license_number": Override(label_es="Número de licencia profesional"),
    "identity.professional_license_holder": Override(label_es="Titular de la licencia"),
    "identity.operating_authorization": Override(label_es="Autorización de operación"),
    "identity.liability_insurance_carrier": Override(label_es="Aseguradora de responsabilidad"),
    "identity.sales_agent_disclaimer": Override(label_es="Disclaimer del sales agent"),
    "identity.sales_agent_out_of_scope": Override(label_es="Casos fuera de alcance"),
    "identity.escalation_contact": Override(label_es="Contacto de escalación"),
    "strategy.methodology_name": Override(label_es="Nombre de la metodología"),
    "strategy.methodology_description": Override(label_es="Descripción de la metodología"),
    "story.origin_story": Override(label_es="Historia de origen"),
    "story.mission": Override(label_es="Misión"),
    "story.vision": Override(label_es="Visión"),
    "contact.support_email": Override(label_es="Email de soporte"),
    "contact.sales_email": Override(label_es="Email de ventas"),
    "contact.phone": Override(label_es="Teléfono"),
    "contact.whatsapp": Override(label_es="WhatsApp"),
    "contact.address": Override(label_es="Dirección"),
    "contact.social_instagram": Override(label_es="Instagram"),
    "contact.social_linkedin": Override(label_es="LinkedIn"),
    "contact.social_youtube": Override(label_es="YouTube"),
    "contact.social_tiktok": Override(label_es="TikTok"),
    "contact.social_facebook": Override(label_es="Facebook"),
    "contact.social_twitter": Override(label_es="X / Twitter"),
    "contact.testimonials_url": Override(label_es="URL página de testimonios"),
    "visuals.primary_color": Override(label_es="Color primario"),
    "visuals.text_secondary_color": Override(label_es="Color de texto secundario"),
    "visuals.photography_style": Override(label_es="Estilo fotográfico"),
    "visuals.visual_references": Override(label_es="Referencias visuales"),
    "visuals.logo_url": Override(label_es="URL del logo principal"),
    "visuals.favicon_url": Override(label_es="URL del favicon"),
    "positioning.discriminator": Override(label_es="Discriminador"),
    "positioning.brand_essence": Override(label_es="Esencia de marca"),
    "positioning.unique_value_proposition": Override(label_es="Propuesta de valor única (UVP)"),
    "narrative.one_liner": Override(label_es="One-liner"),
    "brand_personality.archetype": Override(label_es="Arquetipo"),
    "brand_personality.core_values": Override(label_es="Valores centrales"),
    "brand_personality.personality_traits": Override(label_es="Rasgos de personalidad"),
}


# ---------------------------------------------------------------------------
# Derived registry — the SSoT for the Brand domain
# ---------------------------------------------------------------------------

BRAND_FIELD_CONTRACTS = derive_contracts_from_pydantic(
    model=BrandSettings,
    owner_module="brand",
    section_map=BRAND_SECTION_MAP,
    overrides=BRAND_FIELD_OVERRIDES,
    ignore_paths=BRAND_IGNORE_PATHS,
    composable_fields=BRAND_COMPOSABLE_FIELDS,
)

register_module_contracts("brand", BRAND_FIELD_CONTRACTS)


__all__ = [
    "BRAND_COMPOSABLE_FIELDS",
    "BRAND_FIELD_CONTRACTS",
    "BRAND_FIELD_OVERRIDES",
    "BRAND_IGNORE_PATHS",
    "BRAND_SECTION_MAP",
]
