"""Architecture fitness tests for offer/domain/extraction_section_map.py.

Enforces that the SSoT map stays aligned with the FE section catalog and
the Offer domain entity — preventing silent drift between backend grouping
logic and what the FE actually renders.
"""

from __future__ import annotations

import pytest

# Reference: 21 FE section slugs from section-catalog.ts
FE_CATALOG_SLUGS: frozenset[str] = frozenset(
    {
        "identity",
        "strategy",
        "psychology",
        "promise",
        "program_details",
        "service_details",
        "event_details",
        "product_details",
        "subscription_details",
        "platform_details",
        "location",
        "instructors",
        "value_stack",
        "pricing",
        "testimonials",
        "portfolio",
        "faq",
        "gallery",
        "resources",
        "closing",
        "knowledge",
    }
)

# Fields that appear in Offer*Update models (from offer.py) and ARE expected
# to be covered by the map. Fields excluded from mapping intentionally
# (status, archived_at, deleted_at, metadata_info, landing_page_config,
# has_editions, is_lead_magnet, format_hint, preset_id, archetype,
# shows_as_lead_magnet, access_duration, access_duration_text,
# support_duration_days) are listed separately.
EXPECTED_MAPPED_FIELDS: frozenset[str] = frozenset(
    {
        # identity
        "public_name",
        "internal_sku",
        "headline_promise",
        "primary_outcome",
        "time_to_value",
        # promise
        "requires_application",
        "min_financial_capacity",
        "prerequisites",
        # strategy
        "value_level",
        "delivery_model",
        "target_avatar_match",
        "anti_avatar_keywords",
        # psychology
        "marketing_pain_points",
        "marketing_desires",
        "objections",
        # value_stack
        "deliverables",
        "includes_offers",
        # pricing
        "pricing_options",
        "price_pay_in_full",
        "currency",
        # instructors
        "instructors",
        # closing
        "guarantee_type",
        "guarantee_terms",
        "checkout_page_url",
        "calendar_type_id",
        "onboarding_action",
        "onboarding_url",
        "downsell_offer_id",
        "upsell_offer_id",
        "vsl_link",
    }
)


class TestFeSectionSlugIntegrity:
    """Verify every slug in the map is a valid FE section slug."""

    def test_map_keys_are_valid_fe_slugs(self) -> None:
        """Every key in OFFER_FIELDS_BY_FE_SECTION is a valid FE catalog slug."""
        from src.modules.offer.domain.extraction_section_map import (
            OFFER_FIELDS_BY_FE_SECTION,
        )

        invalid = set(OFFER_FIELDS_BY_FE_SECTION.keys()) - FE_CATALOG_SLUGS
        assert not invalid, (
            f"OFFER_FIELDS_BY_FE_SECTION has keys that are NOT in the FE section catalog: {invalid}. "
            "Update FE_SECTION_SLUGS or fix the map key."
        )

    def test_fe_section_slugs_constant_matches_catalog(self) -> None:
        """FE_SECTION_SLUGS constant in the module matches the FE catalog."""
        from src.modules.offer.domain.extraction_section_map import FE_SECTION_SLUGS

        assert FE_SECTION_SLUGS == FE_CATALOG_SLUGS, (
            "FE_SECTION_SLUGS constant drifted from FE catalog. "
            f"Missing: {FE_CATALOG_SLUGS - FE_SECTION_SLUGS}. "
            f"Extra: {FE_SECTION_SLUGS - FE_CATALOG_SLUGS}."
        )


class TestFieldCoverage:
    """Verify extractable Offer fields are covered in the map."""

    def test_all_expected_fields_appear_in_map(self) -> None:
        """Every field listed in EXPECTED_MAPPED_FIELDS appears in some section."""
        from src.modules.offer.domain.extraction_section_map import (
            OFFER_FIELDS_BY_FE_SECTION,
        )

        all_mapped: set[str] = set()
        for fields in OFFER_FIELDS_BY_FE_SECTION.values():
            all_mapped.update(fields)

        missing = EXPECTED_MAPPED_FIELDS - all_mapped
        assert not missing, (
            f"These Offer fields are NOT covered in OFFER_FIELDS_BY_FE_SECTION: {missing}. "
            "Add them to the appropriate section."
        )

    def test_no_duplicate_fields_across_sections(self) -> None:
        """No field appears in more than one section (would cause double-grouping)."""
        from src.modules.offer.domain.extraction_section_map import (
            OFFER_FIELDS_BY_FE_SECTION,
        )

        seen: dict[str, str] = {}
        duplicates: list[str] = []
        for slug, fields in OFFER_FIELDS_BY_FE_SECTION.items():
            for field in fields:
                if field in seen:
                    duplicates.append(f"{field} (in both '{seen[field]}' and '{slug}')")
                else:
                    seen[field] = slug

        assert not duplicates, f"Fields appear in multiple sections: {duplicates}"


class TestArchetypeMapping:
    """Verify every OfferArchetype maps to a valid FE slug."""

    def test_every_archetype_has_details_slug(self) -> None:
        """Every OfferArchetype value has an entry in _DETAILS_BY_ARCHETYPE."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import (
            _DETAILS_BY_ARCHETYPE,
        )

        missing = [a for a in OfferArchetype if a not in _DETAILS_BY_ARCHETYPE]
        assert not missing, (
            f"These archetypes are missing from _DETAILS_BY_ARCHETYPE: {missing}. "
            "Every archetype must map to a polymorphic details FE slug."
        )

    def test_every_archetype_details_slug_is_valid_fe_slug(self) -> None:
        """Every value in _DETAILS_BY_ARCHETYPE is a valid FE catalog slug."""
        from src.modules.offer.domain.extraction_section_map import (
            _DETAILS_BY_ARCHETYPE,
        )

        invalid = {archetype: slug for archetype, slug in _DETAILS_BY_ARCHETYPE.items() if slug not in FE_CATALOG_SLUGS}
        assert not invalid, f"Invalid FE slugs in _DETAILS_BY_ARCHETYPE: {invalid}"

    def test_resolve_details_section_returns_none_for_none(self) -> None:
        """resolve_details_section(None) returns None gracefully."""
        from src.modules.offer.domain.extraction_section_map import (
            resolve_details_section,
        )

        assert resolve_details_section(None) is None

    def test_resolve_details_section_returns_correct_slugs(self) -> None:
        """resolve_details_section returns the expected FE slug per archetype."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import (
            resolve_details_section,
        )

        expected = {
            OfferArchetype.PROGRAMA: "program_details",
            OfferArchetype.SERVICIO: "service_details",
            OfferArchetype.EXPERIENCIA: "event_details",
            OfferArchetype.PRODUCTO: "product_details",
            OfferArchetype.MEMBRESIA: "subscription_details",
        }
        for archetype, slug in expected.items():
            assert resolve_details_section(archetype) == slug, (
                f"resolve_details_section({archetype}) returned "
                f"{resolve_details_section(archetype)!r}, expected {slug!r}"
            )


class TestFieldsToFeSections:
    """Verify fields_to_fe_sections is deterministic and correct."""

    def test_identity_fields_grouped_correctly(self) -> None:
        """headline_promise + public_name → identity."""
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["headline_promise", "public_name", "primary_outcome"],
        )
        assert "identity" in result
        assert "headline_promise" in result["identity"]
        assert "public_name" in result["identity"]

    def test_strategy_fields_grouped_correctly(self) -> None:
        """value_level + delivery_model → strategy."""
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["value_level", "delivery_model"],
        )
        assert "strategy" in result
        assert set(result["strategy"]) == {"value_level", "delivery_model"}

    def test_specific_details_routed_by_archetype(self) -> None:
        """specific_details.* → program_details for PROGRAMA archetype."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=OfferArchetype.PROGRAMA,
            filled_paths=["specific_details", "specific_details.duration_weeks"],
        )
        assert "program_details" in result
        assert "identity" not in result

    def test_specific_details_routed_to_product_for_producto(self) -> None:
        """specific_details.* → product_details for PRODUCTO archetype."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=OfferArchetype.PRODUCTO,
            filled_paths=["specific_details.format"],
        )
        assert "product_details" in result

    def test_unknown_fields_silently_ignored(self) -> None:
        """Fields not in the map (status, deleted_at) produce no output."""
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["status", "deleted_at", "archived_at", "metadata_info"],
        )
        assert result == {}

    def test_idempotent_same_input_same_output(self) -> None:
        """Calling twice with the same args produces the same result."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        paths = ["headline_promise", "value_level", "deliverables", "guarantee_type"]
        result1 = fields_to_fe_sections(archetype=OfferArchetype.PROGRAMA, filled_paths=paths)
        result2 = fields_to_fe_sections(archetype=OfferArchetype.PROGRAMA, filled_paths=paths)
        assert result1 == result2

    def test_no_duplicate_paths_in_output(self) -> None:
        """Passing a path twice doesn't produce duplicates in the output."""
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["headline_promise", "headline_promise"],
        )
        assert result["identity"].count("headline_promise") == 1

    def test_empty_input_produces_empty_output(self) -> None:
        """Empty filled_paths produces an empty dict."""
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(archetype=None, filled_paths=[])
        assert result == {}

    def test_pricing_fields_grouped_to_pricing(self) -> None:
        """pricing_options + currency → pricing."""
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["pricing_options", "price_pay_in_full", "currency"],
        )
        assert "pricing" in result

    def test_closing_fields_grouped_to_closing(self) -> None:
        """guarantee_type + checkout_page_url → closing."""
        from src.modules.offer.domain.extraction_section_map import (
            fields_to_fe_sections,
        )

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["guarantee_type", "checkout_page_url", "vsl_link"],
        )
        assert "closing" in result
        assert set(result["closing"]) == {"guarantee_type", "checkout_page_url", "vsl_link"}
