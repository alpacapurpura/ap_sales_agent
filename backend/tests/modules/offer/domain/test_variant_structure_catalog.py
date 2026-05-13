"""Domain tests for the VariantStructure catalog (6th SSoT axis).

Guards the per-structure semantic invariants — what each ``VariantStructure``
means and how its flags combine. Architecture tests in
``tests/architecture/`` guard enum ↔ catalog alignment and module purity;
these tests guard the meaning of individual entries.

Related:
    - ``src/modules/offer/domain/variant_structure_catalog.py``
    - ``tests/architecture/test_variant_structure_catalog_completeness.py``
    - ``tests/architecture/test_variant_structure_catalog_purity.py``
"""

from __future__ import annotations

import pytest

from luana_core_offer_studio.domain.enums import VariantStructure
from luana_core_offer_studio.domain.variant_structure_catalog import (
    VARIANT_STRUCTURE_CATALOG,
    CloneCopyPolicy,
    VariantCardinality,
    VariantStructureMetadata,
    get_variant_structure_metadata,
)


class TestCatalogAccess:
    """Direct catalog lookup and helper function behaviour."""

    def test_get_metadata_returns_frozen_record(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.TIER)
        assert isinstance(metadata, VariantStructureMetadata)
        with pytest.raises(AttributeError):
            metadata.label_es = "mutated"  # type: ignore[misc]

    def test_get_metadata_returns_matching_key(self) -> None:
        for structure in VariantStructure:
            metadata = get_variant_structure_metadata(structure)
            assert metadata.key is structure

    def test_direct_catalog_and_helper_agree(self) -> None:
        for structure in VariantStructure:
            assert VARIANT_STRUCTURE_CATALOG[structure] is get_variant_structure_metadata(structure)


class TestTemporalSemantics:
    """Temporal structures are anchored in time; everything else is not."""

    @pytest.mark.parametrize(
        "structure",
        [
            VariantStructure.TEMPORAL_COHORT,
            VariantStructure.TEMPORAL_SINGLE_DATE,
            VariantStructure.RECURRING_INTAKE,
        ],
    )
    def test_temporal_structures_require_temporal_anchor(self, structure: VariantStructure) -> None:
        metadata = get_variant_structure_metadata(structure)
        assert metadata.requires_temporal_anchor is True
        assert "start_date" not in metadata.forbidden_base_fields
        assert "end_date" not in metadata.forbidden_base_fields

    @pytest.mark.parametrize(
        "structure",
        [
            VariantStructure.TIER,
            VariantStructure.SKU_VARIANT,
            VariantStructure.REGIONAL,
        ],
    )
    def test_non_temporal_structures_forbid_date_columns(self, structure: VariantStructure) -> None:
        metadata = get_variant_structure_metadata(structure)
        assert metadata.requires_temporal_anchor is False
        for forbidden in ("start_date", "end_date", "registration_start", "registration_end"):
            assert forbidden in metadata.forbidden_base_fields, (
                f"{structure} must forbid {forbidden!r} on the LaunchEdition base columns."
            )


class TestSingleDateSemantics:
    """``TEMPORAL_SINGLE_DATE`` is the only structure that requires a location."""

    def test_single_date_requires_location(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.TEMPORAL_SINGLE_DATE)
        assert metadata.requires_location is True

    @pytest.mark.parametrize(
        "structure",
        [s for s in VariantStructure if s is not VariantStructure.TEMPORAL_SINGLE_DATE],
    )
    def test_other_structures_do_not_require_location(self, structure: VariantStructure) -> None:
        metadata = get_variant_structure_metadata(structure)
        assert metadata.requires_location is False


class TestOrderableStructures:
    """Non-temporal variants expose ``sort_rank``; temporal ones do not.

    Rationale: TEMPORAL_* structures order naturally by their anchor date,
    while TIER / SKU / REGIONAL / MODALITY / LANGUAGE need explicit
    ordering to surface planes / variantes in the intended layout.
    """

    @pytest.mark.parametrize(
        "structure",
        [
            VariantStructure.TIER,
            VariantStructure.SKU_VARIANT,
            VariantStructure.REGIONAL,
            VariantStructure.MODALITY,
            VariantStructure.LANGUAGE,
        ],
    )
    def test_non_temporal_structures_support_sort_rank(self, structure: VariantStructure) -> None:
        metadata = get_variant_structure_metadata(structure)
        assert metadata.supports_sort_rank is True

    @pytest.mark.parametrize(
        "structure",
        [
            VariantStructure.TEMPORAL_COHORT,
            VariantStructure.TEMPORAL_SINGLE_DATE,
            VariantStructure.RECURRING_INTAKE,
        ],
    )
    def test_temporal_structures_order_by_date_not_rank(self, structure: VariantStructure) -> None:
        metadata = get_variant_structure_metadata(structure)
        assert metadata.supports_sort_rank is False


class TestStructureSpecificPayloads:
    """``required_structure_data_fields`` names the JSONB keys each structure expects."""

    def test_tier_requires_pricing_payload(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.TIER)
        assert "features" in metadata.required_structure_data_fields
        assert "price_amount" in metadata.required_structure_data_fields
        assert "price_currency" in metadata.required_structure_data_fields

    def test_sku_variant_requires_attributes_and_code(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.SKU_VARIANT)
        assert "attributes" in metadata.required_structure_data_fields
        assert "sku_code" in metadata.required_structure_data_fields

    def test_regional_requires_country_and_currency(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.REGIONAL)
        assert "country_codes" in metadata.required_structure_data_fields
        assert "currency" in metadata.required_structure_data_fields

    def test_modality_requires_mode(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.MODALITY)
        assert "mode" in metadata.required_structure_data_fields

    def test_language_requires_locale(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.LANGUAGE)
        assert "locale" in metadata.required_structure_data_fields

    def test_temporal_structures_have_no_required_payload(self) -> None:
        for structure in (
            VariantStructure.TEMPORAL_COHORT,
            VariantStructure.TEMPORAL_SINGLE_DATE,
            VariantStructure.RECURRING_INTAKE,
        ):
            metadata = get_variant_structure_metadata(structure)
            assert metadata.required_structure_data_fields == ()


class TestClonePolicy:
    """Every structure declares a clone policy aligned with its nature."""

    @pytest.mark.parametrize(
        ("structure", "policy"),
        [
            (VariantStructure.TEMPORAL_COHORT, CloneCopyPolicy.TEMPORAL_SHIFT),
            (VariantStructure.TEMPORAL_SINGLE_DATE, CloneCopyPolicy.TEMPORAL_SHIFT),
            (VariantStructure.RECURRING_INTAKE, CloneCopyPolicy.TEMPORAL_SHIFT),
            (VariantStructure.TIER, CloneCopyPolicy.PRESERVE_WITH_SUFFIX),
            (VariantStructure.SKU_VARIANT, CloneCopyPolicy.RESET_IDENTIFIERS),
            (VariantStructure.REGIONAL, CloneCopyPolicy.PRESERVE_WITH_SUFFIX),
            (VariantStructure.MODALITY, CloneCopyPolicy.PRESERVE_WITH_SUFFIX),
            (VariantStructure.LANGUAGE, CloneCopyPolicy.PRESERVE_WITH_SUFFIX),
        ],
    )
    def test_clone_policy_assignment(self, structure: VariantStructure, policy: CloneCopyPolicy) -> None:
        assert get_variant_structure_metadata(structure).clone_policy is policy


class TestCardinality:
    """Cardinality informs wizard copy — must reflect real-world usage."""

    def test_single_date_is_singular(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.TEMPORAL_SINGLE_DATE)
        assert metadata.cardinality is VariantCardinality.SINGULAR

    def test_sku_variant_allows_many(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.SKU_VARIANT)
        assert metadata.cardinality is VariantCardinality.MANY

    def test_tier_is_few(self) -> None:
        metadata = get_variant_structure_metadata(VariantStructure.TIER)
        assert metadata.cardinality is VariantCardinality.FEW


class TestWizardSurfacing:
    """Every structure exposes a wizard prompt — required to surface in Sprint 8+."""

    def test_every_structure_has_a_wizard_prompt(self) -> None:
        for structure, metadata in VARIANT_STRUCTURE_CATALOG.items():
            assert metadata.wizard_prompt_es is not None, (
                f"{structure} is missing ``wizard_prompt_es`` — the wizard step needs every structure to be choosable."
            )
            assert metadata.wizard_prompt_es.strip(), f"{structure} has an empty wizard_prompt_es."
