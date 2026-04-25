"""Golden baseline for brand catalog — locks in pre-Fase-06 shape.

Captures the state of ``BRAND_EDITABLE_FIELDS`` BEFORE the
field-contract-platform Fase 06 brand migration. Used to:

1. Detect drift between catalog paths and what the
   ``schema_introspection.validate_field_path`` validator actually
   accepts (Drift A/B in PRE_INVESTIGATION.md).
2. Lock in the **working** subset that future refactors must preserve
   (UX byte-identical — INVARIANT 4).
3. Document the **broken** subset that Fase 06 will drop (paths the
   copilot could "see" in catalog but never persist successfully).

Post-Fase-06 the test will be updated (see ACCEPTANCE 06.D) to assert
that:
- Every WORKING path remains in the projected catalog.
- No BROKEN path reappears.
- Catalog grew (drift C closed via Pydantic derivation).

refs: docs/refactors/field-contract-platform/phases/06-brand-migration/PRE_INVESTIGATION.md
"""

from __future__ import annotations

from src.modules.brand.domain.copilot_editable_fields import BRAND_EDITABLE_FIELDS
from src.modules.copilot.domain.schema_introspection import validate_field_path

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


class TestBrandCatalogBaseline:
    """Pre-Fase-06 snapshot of ``BRAND_EDITABLE_FIELDS``."""

    def test_catalog_size_matches_baseline(self) -> None:
        """Catalog has exactly WORKING + BROKEN entries (78 today)."""
        assert len(BRAND_EDITABLE_FIELDS) == len(WORKING_PATHS_BASELINE) + len(BROKEN_PATHS_BASELINE)

    def test_catalog_paths_partition_into_working_plus_broken(self) -> None:
        """Every catalog path is either WORKING or BROKEN — no surprises."""
        catalog_paths = {f.path for f in BRAND_EDITABLE_FIELDS}
        baseline = WORKING_PATHS_BASELINE | BROKEN_PATHS_BASELINE
        unknown = catalog_paths - baseline
        missing = baseline - catalog_paths
        assert not unknown, f"Catalog paths missing from baseline classification: {sorted(unknown)}"
        assert not missing, f"Baseline paths missing from catalog: {sorted(missing)}"


class TestBrandCatalogValidatorAgreement:
    """Empirically verify the WORKING/BROKEN classification.

    Uses ``validate_field_path("brand", path)`` to confirm which paths
    resolve in the live BrandSettings introspection. Drift A/B paths
    return False — proof that the broken catalog entries cannot drive
    ``propose_field_updates``.
    """

    def test_working_paths_validate(self) -> None:
        """Every WORKING path passes ``validate_field_path("brand", path)``."""
        invalid = sorted(p for p in WORKING_PATHS_BASELINE if not validate_field_path("brand", p))
        assert not invalid, (
            f"Paths classified WORKING but rejected by validator: {invalid}. Re-classify or fix the validator."
        )

    def test_broken_paths_do_not_validate(self) -> None:
        """Every BROKEN path FAILS ``validate_field_path("brand", path)``.

        Confirms the catalog drift is silently dead — those paths cannot
        drive a successful copilot proposal today, so Fase 06 dropping
        them is UX byte-identical (INVARIANT 4).
        """
        unexpectedly_valid = sorted(p for p in BROKEN_PATHS_BASELINE if validate_field_path("brand", p))
        assert not unexpectedly_valid, (
            f"Paths classified BROKEN but accepted by validator: {unexpectedly_valid}. "
            f"Re-classify — they would be UX-affecting if dropped."
        )
