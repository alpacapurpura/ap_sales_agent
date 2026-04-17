"""Tests for the ArchetypeCapabilities catalog (single source of truth).

These tests guard the domain-level contract that every offer archetype has a
well-defined capability record, and that the current product rules hold.
"""

from __future__ import annotations

import pytest

from src.modules.offer.domain.archetype_catalog import (
    ARCHETYPE_CATALOG,
    ArchetypeCapabilities,
    EditionStructure,
    get_capabilities,
)
from src.modules.offer.domain.enums import (
    FulfillmentType,
    OfferArchetype,
    OfferDeliveryModel,
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
    """Rule: PRODUCTO and MEMBRESIA never support editions (evergreen)."""

    @pytest.mark.parametrize(
        ("archetype", "expected"),
        [
            (OfferArchetype.EXPERIENCIA, True),
            (OfferArchetype.PROGRAMA, True),
            (OfferArchetype.SERVICIO, True),
            (OfferArchetype.PRODUCTO, False),
            (OfferArchetype.MEMBRESIA, False),
        ],
    )
    def test_supports_editions_matches_product_rules(
        self,
        archetype: OfferArchetype,
        expected: bool,
    ) -> None:
        assert get_capabilities(archetype).supports_editions is expected

    def test_archetypes_without_editions_have_none_structure(self) -> None:
        for caps in ARCHETYPE_CATALOG.values():
            if not caps.supports_editions:
                assert caps.edition_structure is EditionStructure.NONE
                assert caps.edition_noun_es == ""
                assert caps.edition_noun_plural_es == ""


class TestEditionsWizardCopy:
    """Copy is present iff archetype supports editions."""

    def test_wizard_copy_present_for_edition_supporting_archetypes(self) -> None:
        for caps in ARCHETYPE_CATALOG.values():
            if caps.supports_editions:
                assert caps.editions_wizard_title_es, caps.archetype
                assert caps.editions_wizard_description_es, caps.archetype
                assert caps.editions_wizard_yes_label_es, caps.archetype
                assert caps.editions_wizard_no_label_es, caps.archetype

    def test_no_wizard_copy_for_non_edition_archetypes(self) -> None:
        for caps in ARCHETYPE_CATALOG.values():
            if not caps.supports_editions:
                assert caps.editions_wizard_title_es is None, caps.archetype
                assert caps.editions_wizard_description_es is None, caps.archetype
                assert caps.editions_wizard_yes_label_es is None, caps.archetype
                assert caps.editions_wizard_no_label_es is None, caps.archetype

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

    def test_non_edition_archetypes_require_nothing_on_publish(self) -> None:
        for caps in ARCHETYPE_CATALOG.values():
            if not caps.supports_editions:
                assert caps.requires_start_date_on_publish is False
                assert caps.requires_end_date_on_publish is False
                assert caps.requires_location_on_publish is False
