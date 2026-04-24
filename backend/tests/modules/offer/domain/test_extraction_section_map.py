"""Unit tests for offer/domain/extraction_section_map.py.

Verifies the core grouping logic used by the offer extraction worker
to translate Offer entity field paths into FE section slugs.
"""

from __future__ import annotations

import pytest

from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.extraction_section_map import (
    _DETAILS_BY_ARCHETYPE,
    BACKEND_WAVE_TO_FE_SLUGS,
    FE_SECTION_SLUGS,
    OFFER_FIELDS_BY_FE_SECTION,
    fields_to_fe_sections,
    resolve_details_section,
)


class TestResolveDeatilsSection:
    """Unit tests for resolve_details_section."""

    @pytest.mark.parametrize(
        ("archetype", "expected"),
        [
            (OfferArchetype.PROGRAMA, "program_details"),
            (OfferArchetype.SERVICIO, "service_details"),
            (OfferArchetype.EXPERIENCIA, "event_details"),
            (OfferArchetype.PRODUCTO, "product_details"),
            (OfferArchetype.MEMBRESIA, "subscription_details"),
        ],
    )
    def test_returns_correct_slug(self, archetype: OfferArchetype, expected: str) -> None:
        """Each archetype resolves to the expected FE details section slug."""
        assert resolve_details_section(archetype) == expected

    def test_none_archetype_returns_none(self) -> None:
        """resolve_details_section(None) must return None, not raise."""
        assert resolve_details_section(None) is None


class TestFieldsToFeSections:
    """Detailed unit tests for fields_to_fe_sections()."""

    def test_maps_identity_fields(self) -> None:
        """public_name, internal_sku, headline_promise, primary_outcome, time_to_value → identity."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["public_name", "internal_sku", "headline_promise", "primary_outcome", "time_to_value"],
        )
        assert set(result.get("identity", [])) == {
            "public_name",
            "internal_sku",
            "headline_promise",
            "primary_outcome",
            "time_to_value",
        }

    def test_maps_strategy_fields(self) -> None:
        """value_level, delivery_model, target_avatar_match, anti_avatar_keywords → strategy."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["value_level", "delivery_model", "target_avatar_match", "anti_avatar_keywords"],
        )
        assert set(result.get("strategy", [])) == {
            "value_level",
            "delivery_model",
            "target_avatar_match",
            "anti_avatar_keywords",
        }

    def test_maps_psychology_fields(self) -> None:
        """marketing_pain_points, marketing_desires, objections → psychology."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["marketing_pain_points", "marketing_desires", "objections"],
        )
        assert "psychology" in result
        assert len(result["psychology"]) == 3

    def test_maps_value_stack_fields(self) -> None:
        """deliverables, includes_offers → value_stack."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["deliverables", "includes_offers"],
        )
        assert set(result.get("value_stack", [])) == {"deliverables", "includes_offers"}

    def test_maps_pricing_fields(self) -> None:
        """pricing_options, price_pay_in_full, currency → pricing."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["pricing_options", "price_pay_in_full", "currency"],
        )
        assert "pricing" in result
        assert len(result["pricing"]) == 3

    def test_maps_instructors_field(self) -> None:
        """instructors → instructors."""
        result = fields_to_fe_sections(archetype=None, filled_paths=["instructors"])
        assert result.get("instructors") == ["instructors"]

    def test_maps_closing_fields(self) -> None:
        """guarantee_type, checkout_page_url, vsl_link → closing."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["guarantee_type", "checkout_page_url", "vsl_link"],
        )
        assert "closing" in result
        assert "guarantee_type" in result["closing"]

    def test_specific_details_no_archetype_produces_nothing(self) -> None:
        """specific_details.* with archetype=None produces no output (no slug to route to)."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["specific_details.duration_weeks"],
        )
        assert result == {}

    def test_specific_details_programa_routes_to_program_details(self) -> None:
        """specific_details.* with PROGRAMA → program_details."""
        result = fields_to_fe_sections(
            archetype=OfferArchetype.PROGRAMA,
            filled_paths=["specific_details.duration_weeks", "specific_details.cohort_size"],
        )
        assert "program_details" in result
        assert len(result["program_details"]) == 2

    def test_specific_details_bare_key_routes_correctly(self) -> None:
        """'specific_details' (no sub-key) routes to the archetype details section."""
        result = fields_to_fe_sections(
            archetype=OfferArchetype.SERVICIO,
            filled_paths=["specific_details"],
        )
        assert "service_details" in result

    def test_mixed_paths_produce_multiple_sections(self) -> None:
        """Multiple fields from different sections produce multiple section entries."""
        result = fields_to_fe_sections(
            archetype=OfferArchetype.PROGRAMA,
            filled_paths=["headline_promise", "value_level", "deliverables", "guarantee_type"],
        )
        assert "identity" in result
        assert "strategy" in result
        assert "value_stack" in result
        assert "closing" in result

    def test_system_fields_not_in_output(self) -> None:
        """System fields (status, timestamps, metadata) produce no output.

        Post field-contract-platform refactor (Fase 04), these paths are in
        ``OFFER_IGNORE_PATHS`` so they don't appear in any FieldContract.
        ``format_hint`` IS in the registry (identity section) — distinct
        from system fields. Behavior fix vs legacy drift.
        """
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["status", "deleted_at", "archived_at", "metadata_info"],
        )
        assert result == {}

    def test_idempotent(self) -> None:
        """Same inputs always produce the same dict — no hidden state."""
        paths = ["headline_promise", "value_level", "guarantee_type", "specific_details.duration"]
        r1 = fields_to_fe_sections(archetype=OfferArchetype.PROGRAMA, filled_paths=paths)
        r2 = fields_to_fe_sections(archetype=OfferArchetype.PROGRAMA, filled_paths=paths)
        assert r1 == r2

    def test_no_duplicates_in_output(self) -> None:
        """Passing a path twice does not produce duplicate entries in the section list."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["headline_promise", "headline_promise", "value_level"],
        )
        assert result["identity"].count("headline_promise") == 1


class TestBackendWaveToFeSlugsMap:
    """Verify BACKEND_WAVE_TO_FE_SLUGS is internally consistent."""

    def test_all_fe_slugs_in_wave_map_are_valid(self) -> None:
        """Every FE slug referenced in BACKEND_WAVE_TO_FE_SLUGS is in FE_SECTION_SLUGS."""
        invalid: list[str] = []
        for wave, fe_slugs in BACKEND_WAVE_TO_FE_SLUGS.items():
            if wave == "details":
                continue  # resolved dynamically
            for slug in fe_slugs:
                if slug not in FE_SECTION_SLUGS:
                    invalid.append(f"{wave} → {slug}")
        assert not invalid, f"Invalid FE slugs in BACKEND_WAVE_TO_FE_SLUGS: {invalid}"

    def test_promise_wave_maps_to_identity_and_promise(self) -> None:
        """The 'promise' backend wave covers both 'identity' and 'promise' FE sections."""
        fe_slugs = BACKEND_WAVE_TO_FE_SLUGS.get("promise", ())
        assert "identity" in fe_slugs
        assert "promise" in fe_slugs
