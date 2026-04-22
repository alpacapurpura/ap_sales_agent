"""Brand editable-field catalog — single source of truth for the copilot.

# [COPILOT-EDITABLE-FIELDS-SSOT] → docs/domains/copilot/editable-fields.md
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  IMPORTANTE PARA AGENTES / DEVS                                      ║
# ║                                                                      ║
# ║  Esta es la fuente de verdad de los campos de brand que el copilot  ║
# ║  puede proponer editar vía `propose_field_updates`.                  ║
# ║                                                                      ║
# ║  Cuando AGREGUES, ELIMINES, RENOMBRES o MUEVAS un campo en:          ║
# ║  - frontend/src/features/brand-studio/schemas/*.schema.ts            ║
# ║  - el modelo Pydantic correspondiente en                             ║
# ║    backend/src/modules/brand/domain/                                 ║
# ║                                                                      ║
# ║  TAMBIÉN ACTUALIZA ESTE ARCHIVO. Sin esta actualización el LLM       ║
# ║  alucinará ``field_id``s obsoletos o ignorará campos nuevos.         ║
# ║                                                                      ║
# ║  El arch test ``test_editable_fields_ssot.py`` falla si se detecta   ║
# ║  drift obvio contra BrandSettings.                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

Cada entrada refleja el ``path`` que el FE envía al persistir el formulario,
con el ``label`` que ve el usuario. La sección agrupa los campos para la
enumeración compacta del system prompt.
"""

from __future__ import annotations

from src.shared.links.ports.editable_fields import FieldSpec, register_catalog

# ── identity ─────────────────────────────────────────────────────────────
# Form-runtime: brand.identity — frontend/src/features/brand-studio/schemas/identity.schema.ts
_IDENTITY = (
    FieldSpec(
        "identity.brand_name", "Nombre", "identity", "Nombre público con el que los clientes te buscan y recomiendan."
    ),
    FieldSpec("identity.tagline", "Tagline", "identity", "Una línea que resume tu propuesta."),
    FieldSpec("identity.description", "Descripción", "identity", "Qué hace tu marca, para quién y por qué importa."),
    FieldSpec("identity.industry", "Industria", "identity", "Sector en el que opera tu negocio."),
    FieldSpec("identity.website", "Sitio web", "identity"),
    FieldSpec("identity.founding_year", "Año de fundación", "identity"),
    FieldSpec("identity.language", "Idioma", "identity"),
    FieldSpec("identity.timezone", "Zona horaria", "identity"),
)

# ── story ────────────────────────────────────────────────────────────────
# Form-runtime: brand.story
_STORY = (
    FieldSpec("story.origin_story", "Historia de origen", "story"),
    FieldSpec("story.mission", "Misión", "story"),
    FieldSpec("story.vision", "Visión", "story"),
)

# ── positioning ──────────────────────────────────────────────────────────
# Form-runtime: brand.positioning
_POSITIONING = (
    FieldSpec("positioning.unique_value_proposition", "Propuesta de valor única (UVP)", "positioning"),
    FieldSpec("positioning.discriminator", "Discriminador", "positioning"),
    FieldSpec("positioning.brand_essence", "Esencia de marca", "positioning"),
    FieldSpec("positioning.technical_enemy", "Enemigo técnico", "positioning"),
    FieldSpec("positioning.philosophical_enemy", "Enemigo filosófico", "positioning"),
    FieldSpec("positioning.insight_tension", "Insight · tensión", "positioning"),
    FieldSpec("positioning.insight_observation", "Insight · observación", "positioning"),
    FieldSpec("positioning.insight_implication", "Insight · implicación", "positioning"),
)

# ── narrative ────────────────────────────────────────────────────────────
# Form-runtime: brand.narrative (StoryBrand framework)
_NARRATIVE = (
    FieldSpec("narrative.one_liner", "One-liner", "narrative"),
    FieldSpec("narrative.hero_identity", "Identidad del héroe", "narrative"),
    FieldSpec("narrative.hero_desire", "Deseo del héroe", "narrative"),
    FieldSpec("narrative.problem_villain", "Problema · villano", "narrative"),
    FieldSpec("narrative.problem_external", "Problema externo", "narrative"),
    FieldSpec("narrative.problem_internal", "Problema interno", "narrative"),
    FieldSpec("narrative.problem_philosophical", "Problema filosófico", "narrative"),
    FieldSpec("narrative.guide_empathy", "Guía · empatía", "narrative"),
    FieldSpec("narrative.guide_authority", "Guía · autoridad", "narrative"),
    FieldSpec("narrative.cta_direct", "CTA directo", "narrative"),
    FieldSpec("narrative.cta_transitional", "CTA transicional", "narrative"),
    FieldSpec("narrative.outcome_success", "Resultado · éxito", "narrative"),
    FieldSpec("narrative.outcome_failure", "Resultado · fracaso", "narrative"),
)

# ── methodology ──────────────────────────────────────────────────────────
# Form-runtime: brand.methodology
_METHODOLOGY = (
    FieldSpec("strategy.methodology_name", "Nombre de la metodología", "methodology"),
    FieldSpec("strategy.methodology_description", "Descripción de la metodología", "methodology"),
)

# ── personality ──────────────────────────────────────────────────────────
# Form-runtime: brand.personality — editable via PersonalityProfile flow
# (archetype/core_values/personality_traits are FE inputs that map to the
# active personality profile, not scalar columns on BrandPersonality —
# edits happen through the personality compiler flow).
_PERSONALITY = (
    FieldSpec("brand_personality.archetype", "Arquetipo", "personality"),
    FieldSpec("brand_personality.core_values", "Valores centrales", "personality"),
    FieldSpec("brand_personality.personality_traits", "Rasgos de personalidad", "personality"),
)

# ── visuals ──────────────────────────────────────────────────────────────
# Form-runtime: brand.visuals (only persisted scalar fields; logo_picker,
# visuals_wizard and theme_injector are UI controls, not persisted values).
_VISUALS = (
    FieldSpec("visuals.primary_color", "Color primario", "visuals"),
    FieldSpec("visuals.text_secondary_color", "Color de texto secundario", "visuals"),
    FieldSpec("visuals.photography_style", "Estilo fotográfico", "visuals"),
    FieldSpec("visuals.visual_references", "Referencias visuales", "visuals"),
    FieldSpec("visuals.logo_url", "URL del logo principal", "visuals"),
    FieldSpec("visuals.favicon_url", "URL del favicon", "visuals"),
)

# ── contact ──────────────────────────────────────────────────────────────
# Form-runtime: brand.contact
_CONTACT = (
    FieldSpec("contact.support_email", "Email de soporte", "contact"),
    FieldSpec("contact.sales_email", "Email de ventas", "contact"),
    FieldSpec("contact.phone", "Teléfono", "contact"),
    FieldSpec("contact.whatsapp", "WhatsApp", "contact"),
    FieldSpec("contact.address", "Dirección", "contact"),
    FieldSpec("contact.social_instagram", "Instagram", "contact"),
    FieldSpec("contact.social_linkedin", "LinkedIn", "contact"),
    FieldSpec("contact.social_youtube", "YouTube", "contact"),
    FieldSpec("contact.social_tiktok", "TikTok", "contact"),
    FieldSpec("contact.social_facebook", "Facebook", "contact"),
    FieldSpec("contact.social_twitter", "X / Twitter", "contact"),
    FieldSpec("contact.testimonials_url", "URL página de testimonios", "contact"),
)

# ── legal ────────────────────────────────────────────────────────────────
# Form-runtime: brand.legal
_LEGAL = (
    FieldSpec("contact.legal_name", "Razón social", "legal"),
    FieldSpec("contact.legal_entity_type", "Tipo de entidad legal", "legal"),
    FieldSpec("contact.tax_id", "ID fiscal", "legal"),
    FieldSpec("contact.tax_regime", "Régimen fiscal", "legal"),
    FieldSpec("contact.country_of_registration", "País de registro", "legal"),
    FieldSpec("contact.commercial_registry_number", "Número de registro comercial", "legal"),
    FieldSpec("contact.fiscal_address", "Dirección fiscal", "legal"),
    FieldSpec("contact.legal_representative", "Representante legal", "legal"),
    FieldSpec("contact.legal_email", "Email legal", "legal"),
    FieldSpec("contact.dpo_email", "Email DPO", "legal"),
    FieldSpec("contact.terms_url", "URL de términos", "legal"),
    FieldSpec("contact.privacy_url", "URL de privacidad", "legal"),
    FieldSpec("contact.cookies_url", "URL de cookies", "legal"),
    FieldSpec("contact.refund_policy_url", "URL política de reembolsos", "legal"),
    FieldSpec("contact.acceptable_use_url", "URL uso aceptable", "legal"),
    FieldSpec("contact.regulated_profession_body", "Organismo profesional regulado", "legal"),
    FieldSpec("contact.professional_license_number", "Número de licencia profesional", "legal"),
    FieldSpec("contact.professional_license_holder", "Titular de la licencia", "legal"),
    FieldSpec("contact.operating_authorization", "Autorización de operación", "legal"),
    FieldSpec("contact.liability_insurance_carrier", "Aseguradora de responsabilidad", "legal"),
    FieldSpec("contact.sales_agent_disclaimer", "Disclaimer del sales agent", "legal"),
    FieldSpec("contact.sales_agent_out_of_scope", "Casos fuera de alcance", "legal"),
    FieldSpec("contact.escalation_contact", "Contacto de escalación", "legal"),
)


BRAND_EDITABLE_FIELDS: tuple[FieldSpec, ...] = (
    *_IDENTITY,
    *_STORY,
    *_POSITIONING,
    *_NARRATIVE,
    *_METHODOLOGY,
    *_PERSONALITY,
    *_VISUALS,
    *_CONTACT,
    *_LEGAL,
)


# Register at import time so the copilot sees the catalog via the port
# without importing this module directly.
register_catalog("brand", BRAND_EDITABLE_FIELDS)


__all__ = ["BRAND_EDITABLE_FIELDS"]
