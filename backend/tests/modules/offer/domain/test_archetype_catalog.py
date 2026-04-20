"""Tests for the ArchetypeCapabilities catalog (single source of truth).

These tests guard the domain-level contract that every offer archetype has a
well-defined capability record, and that the current product rules hold.
"""

from __future__ import annotations

import pytest

from src.modules.offer.domain.archetype_catalog import (
    ARCHETYPE_CATALOG,
    ArchetypeCapabilities,
    get_capabilities,
)
from src.modules.offer.domain.enums import (
    FulfillmentType,
    OfferArchetype,
    OfferDeliveryModel,
    VariantStructure,
)


class TestCatalogCompleteness:
    def test_every_archetype_has_a_capability_record(self) -> None:
        missing = [a for a in OfferArchetype if a not in ARCHETYPE_CATALOG]
        assert missing == [], f"Missing catalog entries: {missing}"

    def test_get_capabilities_returns_a_frozen_record(self) -> None:
        caps = get_capabilities(OfferArchetype.PROGRAMA)
        assert isinstance(caps, ArchetypeCapabilities)
        with pytest.raises(AttributeError):
            caps.supports_editions = False  # type: ignore[misc]

    def test_catalog_records_reference_their_own_archetype(self) -> None:
        for archetype, caps in ARCHETYPE_CATALOG.items():
            assert caps.archetype is archetype


class TestSupportsEditions:
    """Sprint 15.1: every archetype supports editions via ``VariantStructure``.

    PRODUCTO uses SKU_VARIANT (talla/color/material), MEMBRESIA uses TIER
    (plan Gold/Platinum/Enterprise). The ``allow_single_variant`` flag
    lets the UX collapse one-variant offers into a direct editor.
    """

    @pytest.mark.parametrize(
        ("archetype", "expected"),
        [
            (OfferArchetype.EXPERIENCIA, True),
            (OfferArchetype.PROGRAMA, True),
            (OfferArchetype.SERVICIO, True),
            (OfferArchetype.PRODUCTO, True),
            (OfferArchetype.MEMBRESIA, True),
        ],
    )
    def test_supports_editions_matches_product_rules(
        self,
        archetype: OfferArchetype,
        expected: bool,
    ) -> None:
        assert get_capabilities(archetype).supports_editions is expected

    @pytest.mark.parametrize(
        ("archetype", "expected_default"),
        [
            (OfferArchetype.EXPERIENCIA, VariantStructure.TEMPORAL_SINGLE_DATE),
            (OfferArchetype.PROGRAMA, VariantStructure.TEMPORAL_COHORT),
            (OfferArchetype.SERVICIO, VariantStructure.RECURRING_INTAKE),
            (OfferArchetype.PRODUCTO, VariantStructure.SKU_VARIANT),
            (OfferArchetype.MEMBRESIA, VariantStructure.TIER),
        ],
    )
    def test_default_variant_structure_matches_archetype(
        self,
        archetype: OfferArchetype,
        expected_default: VariantStructure,
    ) -> None:
        assert get_capabilities(archetype).default_variant_structure is expected_default

    @pytest.mark.parametrize(
        ("archetype", "expected_single"),
        [
            (OfferArchetype.EXPERIENCIA, True),
            (OfferArchetype.PROGRAMA, False),  # cohorts are intrinsically plural
            (OfferArchetype.SERVICIO, True),
            (OfferArchetype.PRODUCTO, True),
            (OfferArchetype.MEMBRESIA, True),
        ],
    )
    def test_allow_single_variant_matches_archetype(
        self,
        archetype: OfferArchetype,
        expected_single: bool,
    ) -> None:
        assert get_capabilities(archetype).allow_single_variant is expected_single


class TestEditionsWizardCopy:
    """Copy is present iff archetype supports editions."""

    def test_wizard_copy_present_for_edition_supporting_archetypes(self) -> None:
        for caps in ARCHETYPE_CATALOG.values():
            if caps.supports_editions:
                assert caps.editions_wizard_title_es, caps.archetype
                assert caps.editions_wizard_description_es, caps.archetype
                assert caps.editions_wizard_yes_label_es, caps.archetype
                assert caps.editions_wizard_no_label_es, caps.archetype

    def test_spanish_copy_uses_correct_accents(self) -> None:
        programa = get_capabilities(OfferArchetype.PROGRAMA)
        assert "Sí" in programa.editions_wizard_yes_label_es  # type: ignore[operator]
        experiencia = get_capabilities(OfferArchetype.EXPERIENCIA)
        assert "única" in experiencia.editions_wizard_no_label_es  # type: ignore[operator]


class TestDefaults:
    """Defaults propagated to the Offer entity at creation."""

    @pytest.mark.parametrize(
        ("archetype", "expected_delivery"),
        [
            (OfferArchetype.EXPERIENCIA, OfferDeliveryModel.DWY),
            (OfferArchetype.PROGRAMA, OfferDeliveryModel.DWY),
            (OfferArchetype.SERVICIO, OfferDeliveryModel.DFY),
            (OfferArchetype.PRODUCTO, OfferDeliveryModel.DIY),
            (OfferArchetype.MEMBRESIA, OfferDeliveryModel.DIY),
        ],
    )
    def test_default_delivery_matches_archetype(
        self,
        archetype: OfferArchetype,
        expected_delivery: OfferDeliveryModel,
    ) -> None:
        assert get_capabilities(archetype).default_delivery is expected_delivery

    def test_every_archetype_has_a_default_fulfillment(self) -> None:
        for caps in ARCHETYPE_CATALOG.values():
            assert isinstance(caps.default_fulfillment, FulfillmentType)


class TestPublishingConstraints:
    """Rule: PROGRAMA cohorts must have end date; EXPERIENCIA must have location."""

    def test_programa_requires_end_date_on_publish(self) -> None:
        caps = get_capabilities(OfferArchetype.PROGRAMA)
        assert caps.requires_start_date_on_publish is True
        assert caps.requires_end_date_on_publish is True

    def test_experiencia_requires_location_on_publish(self) -> None:
        caps = get_capabilities(OfferArchetype.EXPERIENCIA)
        assert caps.requires_location_on_publish is True

    def test_tier_and_sku_archetypes_require_nothing_on_publish(self) -> None:
        """PRODUCTO (SKU) and MEMBRESIA (TIER) have no temporal publish gate."""
        for archetype in (OfferArchetype.PRODUCTO, OfferArchetype.MEMBRESIA):
            caps = get_capabilities(archetype)
            assert caps.requires_start_date_on_publish is False
            assert caps.requires_end_date_on_publish is False
            assert caps.requires_location_on_publish is False
