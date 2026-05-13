"""Golden baseline for brand catalog — locks in Fase-06 invariants.

Originally captured the pre-Fase-06 catalog shape so the migration could
be validated. Updated 2026-04-24 (sub-step 06.D) to enforce the
post-migration invariants:

1. Every **WORKING** path (those that validated via
   ``schema_introspection.validate_field_path`` pre-refactor) remains in
   the projected catalog — UX byte-identical (INVARIANT 4).
2. No **BROKEN** path reappears in the catalog (Drift A/B closed by
   construction).
3. Curated Spanish labels for the working paths are preserved (system
   prompt enumeration remains identical).
4. The catalog grew net-positive thanks to Drift C closure (~48 Pydantic
   fields the legacy catalog never exposed are now proposable).

refs: docs/refactors/field-contract-platform/phases/06-brand-migration/PRE_INVESTIGATION.md
"""

from __future__ import annotations

from luana_core_copilot.domain.schema_introspection import validate_field_path
from luana_core_platform.links.ports.editable_fields import get_catalog


def _brand_catalog():
    """Helper — post-Fase-08 the catalog derives from the FieldContract registry."""
    return get_catalog("brand")


# ---------------------------------------------------------------------------
# Baseline sets — frozen pre-Fase-06
# ---------------------------------------------------------------------------

# Paths that resolve via ``schema_introspection.validate_field_path("brand", ...)``
# (i.e. exist as ``section.field`` in BrandSettings sub-models). These MUST
# remain proposable post-refactor — INVARIANT 4 byte-identical.
WORKING_PATHS_BASELINE: frozenset[str] = frozenset(
    {
        # -- identity (BrandIdentity scalar fields) --
        "identity.brand_name",
        "identity.description",
        "identity.founding_year",
        "identity.industry",
        "identity.language",
        "identity.tagline",
        "identity.timezone",
        "identity.website",
        # -- contact (BrandContact real fields) --
        "contact.address",
        "contact.phone",
        "contact.sales_email",
        "contact.social_facebook",
        "contact.social_instagram",
        "contact.social_linkedin",
        "contact.social_tiktok",
        "contact.social_twitter",
        "contact.social_youtube",
        "contact.support_email",
        "contact.testimonials_url",
        "contact.whatsapp",
        # -- story (BrandStory) --
        "story.mission",
        "story.origin_story",
        "story.vision",
        # -- strategy (BrandStrategy methodology fields) --
        "strategy.methodology_description",
        "strategy.methodology_name",
        # -- brand_personality (BrandPersonality) --
        "brand_personality.archetype",
        "brand_personality.core_values",
        "brand_personality.personality_traits",
        # -- visuals (BrandVisuals subset covered by catalog) --
        "visuals.favicon_url",
        "visuals.logo_url",
        "visuals.photography_style",
        "visuals.primary_color",
        "visuals.text_secondary_color",
        "visuals.visual_references",
        # -- narrative (only one_liner is a flat scalar) --
        "narrative.one_liner",
        # -- positioning (only flat scalars; nested objects ignored) --
        "positioning.brand_essence",
        "positioning.discriminator",
        "positioning.unique_value_proposition",
    }
)

# Paths in catalog today that DO NOT resolve via the validator. These are
# Drift A (shorthand to non-existent 2-level paths) and Drift B (wrong
# section: catalog says ``contact.*`` but Pydantic has ``identity.*``).
# Fase 06 will drop these by deriving the catalog from Pydantic structure.
BROKEN_PATHS_BASELINE: frozenset[str] = frozenset(
    {
        # -- Drift A: shorthand 2-level paths (positioning sub-objects) --
        "positioning.insight_implication",
        "positioning.insight_observation",
        "positioning.insight_tension",
        "positioning.philosophical_enemy",
        "positioning.technical_enemy",
        # -- Drift A: shorthand 2-level paths (narrative sub-objects) --
        "narrative.cta_direct",
        "narrative.cta_transitional",
        "narrative.guide_authority",
        "narrative.guide_empathy",
        "narrative.hero_desire",
        "narrative.hero_identity",
        "narrative.outcome_failure",
        "narrative.outcome_success",
        "narrative.problem_external",
        "narrative.problem_internal",
        "narrative.problem_philosophical",
        "narrative.problem_villain",
        # -- Drift B: wrong section, Pydantic has these in BrandIdentity --
        "contact.acceptable_use_url",
        "contact.commercial_registry_number",
        "contact.cookies_url",
        "contact.country_of_registration",
        "contact.dpo_email",
        "contact.escalation_contact",
        "contact.fiscal_address",
        "contact.legal_email",
        "contact.legal_entity_type",
        "contact.legal_name",
        "contact.legal_representative",
        "contact.liability_insurance_carrier",
        "contact.operating_authorization",
        "contact.privacy_url",
        "contact.professional_license_holder",
        "contact.professional_license_number",
        "contact.refund_policy_url",
        "contact.regulated_profession_body",
        "contact.sales_agent_disclaimer",
        "contact.sales_agent_out_of_scope",
        "contact.tax_id",
        "contact.tax_regime",
        "contact.terms_url",
    }
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


# Curated Spanish labels for working paths — system prompt enumeration must
# preserve these verbatim post-Fase-06. Drift B paths (catalog said
# ``contact.legal_*``, Pydantic has ``identity.legal_*``) re-surface their
# original label under the corrected path.
LABEL_PRESERVATION_BASELINE: dict[str, str] = {
    "identity.brand_name": "Nombre",
    "identity.tagline": "Tagline",
    "identity.description": "Descripción",
    "identity.industry": "Industria",
    "identity.website": "Sitio web",
    "identity.founding_year": "Año de fundación",
    "identity.language": "Idioma",
    "identity.timezone": "Zona horaria",
    "contact.address": "Dirección",
    "contact.phone": "Teléfono",
    "contact.sales_email": "Email de ventas",
    "contact.social_facebook": "Facebook",
    "contact.social_instagram": "Instagram",
    "contact.social_linkedin": "LinkedIn",
    "contact.social_tiktok": "TikTok",
    "contact.social_twitter": "X / Twitter",
    "contact.social_youtube": "YouTube",
    "contact.support_email": "Email de soporte",
    "contact.testimonials_url": "URL página de testimonios",
    "contact.whatsapp": "WhatsApp",
    "story.mission": "Misión",
    "story.origin_story": "Historia de origen",
    "story.vision": "Visión",
    "strategy.methodology_description": "Descripción de la metodología",
    "strategy.methodology_name": "Nombre de la metodología",
    "brand_personality.archetype": "Arquetipo",
    "brand_personality.core_values": "Valores centrales",
    "brand_personality.personality_traits": "Rasgos de personalidad",
    "visuals.favicon_url": "URL del favicon",
    "visuals.logo_url": "URL del logo principal",
    "visuals.photography_style": "Estilo fotográfico",
    "visuals.primary_color": "Color primario",
    "visuals.text_secondary_color": "Color de texto secundario",
    "visuals.visual_references": "Referencias visuales",
    "narrative.one_liner": "One-liner",
    "positioning.brand_essence": "Esencia de marca",
    "positioning.discriminator": "Discriminador",
    "positioning.unique_value_proposition": "Propuesta de valor única (UVP)",
    # Drift B paths — original labels preserved under corrected ``identity.*`` path
    "identity.acceptable_use_url": "URL uso aceptable",
    "identity.commercial_registry_number": "Número de registro comercial",
    "identity.cookies_url": "URL de cookies",
    "identity.country_of_registration": "País de registro",
    "identity.dpo_email": "Email DPO",
    "identity.escalation_contact": "Contacto de escalación",
    "identity.fiscal_address": "Dirección fiscal",
    "identity.legal_email": "Email legal",
    "identity.legal_entity_type": "Tipo de entidad legal",
    "identity.legal_name": "Razón social",
    "identity.legal_representative": "Representante legal",
    "identity.liability_insurance_carrier": "Aseguradora de responsabilidad",
    "identity.operating_authorization": "Autorización de operación",
    "identity.privacy_url": "URL de privacidad",
    "identity.professional_license_holder": "Titular de la licencia",
    "identity.professional_license_number": "Número de licencia profesional",
    "identity.refund_policy_url": "URL política de reembolsos",
    "identity.regulated_profession_body": "Organismo profesional regulado",
    "identity.sales_agent_disclaimer": "Disclaimer del sales agent",
    "identity.sales_agent_out_of_scope": "Casos fuera de alcance",
    "identity.tax_id": "ID fiscal",
    "identity.tax_regime": "Régimen fiscal",
    "identity.terms_url": "URL de términos",
}


class TestBrandCatalogPostMigration:
    """Post-Fase-06 invariants for ``_brand_catalog()``.

    Locks in: working paths preserved + broken paths excluded + catalog
    grew (drift C closed) + curated Spanish labels survived the projection.
    """

    def test_working_paths_remain_in_catalog(self) -> None:
        """Every legacy WORKING path remains proposable post-refactor."""
        catalog_paths = {f.path for f in _brand_catalog()}
        missing = sorted(WORKING_PATHS_BASELINE - catalog_paths)
        assert not missing, (
            f"Working paths dropped by Fase 06 projection: {missing}. "
            f"Add to BRAND_SECTION_MAP or unset can_propose=False on the override."
        )

    def test_broken_paths_dropped_from_catalog(self) -> None:
        """No BROKEN shorthand or wrong-section path resurfaces."""
        catalog_paths = {f.path for f in _brand_catalog()}
        resurfaced = sorted(BROKEN_PATHS_BASELINE & catalog_paths)
        assert not resurfaced, (
            f"Broken paths resurfaced in projected catalog: {resurfaced}. "
            f"They should not validate against BrandSettings — investigate."
        )

    def test_catalog_grew_via_drift_c_closure(self) -> None:
        """Catalog is at least as big as the legacy WORKING set + new Pydantic surface."""
        catalog_paths = {f.path for f in _brand_catalog()}
        # WORKING (38) plus at minimum the legal/regulated identity fields
        # (Drift B remap, 23 paths) that the legacy catalog labelled under
        # ``contact.legal_*`` but that now live under ``identity.*``.
        assert len(catalog_paths) >= len(WORKING_PATHS_BASELINE) + 23, (
            f"Catalog has {len(catalog_paths)} paths; expected ≥ {len(WORKING_PATHS_BASELINE) + 23} "
            f"(WORKING preserved + Drift B identity.* surface)."
        )

    def test_curated_labels_preserved(self) -> None:
        """Spanish labels from the legacy catalog survive the projection."""
        catalog_by_path = {f.path: f.label for f in _brand_catalog()}
        mismatches: list[str] = []
        for path, expected_label in LABEL_PRESERVATION_BASELINE.items():
            actual = catalog_by_path.get(path)
            if actual is None:
                mismatches.append(f"{path}: missing from catalog")
            elif actual != expected_label:
                mismatches.append(f"{path}: expected {expected_label!r}, got {actual!r}")
        assert not mismatches, "Label drift in projected catalog:\n  " + "\n  ".join(mismatches)


class TestBrandCatalogValidatorAgreement:
    """Empirically verify the WORKING/BROKEN classification stays accurate.

    Uses ``validate_field_path("brand", path)`` to confirm which paths
    resolve in the live BrandSettings introspection. Drift A/B paths
    return False — proof that the broken catalog entries could not drive
    ``propose_field_updates`` pre-Fase-06.
    """

    def test_working_paths_validate(self) -> None:
        """Every WORKING path passes ``validate_field_path("brand", path)``."""
        invalid = sorted(p for p in WORKING_PATHS_BASELINE if not validate_field_path("brand", p))
        assert not invalid, (
            f"Paths classified WORKING but rejected by validator: {invalid}. Re-classify or fix the validator."
        )

    def test_broken_paths_do_not_validate(self) -> None:
        """Every BROKEN path FAILS ``validate_field_path("brand", path)``.

        Confirms the catalog drift was silently dead pre-Fase-06 — those
        paths could not drive a successful copilot proposal, so dropping
        them in 06.D is UX byte-identical (INVARIANT 4).
        """
        unexpectedly_valid = sorted(p for p in BROKEN_PATHS_BASELINE if validate_field_path("brand", p))
        assert not unexpectedly_valid, (
            f"Paths classified BROKEN but accepted by validator: {unexpectedly_valid}. "
            f"Re-classify — they would be UX-affecting if dropped."
        )
