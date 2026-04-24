"""Architecture fitness tests for offer/domain/extraction_section_map.py.

Post field-contract-platform refactor (Fase 04): the legacy
``OFFER_FIELDS_BY_FE_SECTION`` dict was removed. Tests now validate the
runtime behavior of ``fields_to_fe_sections()`` and the FE slug mapping
preserved via ``_DETAILS_BY_ARCHETYPE``.
"""

from __future__ import annotations

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


class TestFeSectionSlugIntegrity:
    """Verify the FE_SECTION_SLUGS constant matches the canonical FE catalog."""

    def test_fe_section_slugs_constant_matches_catalog(self) -> None:
        """FE_SECTION_SLUGS constant in the module matches the FE catalog."""
        from src.modules.offer.domain.extraction_section_map import FE_SECTION_SLUGS

        assert FE_SECTION_SLUGS == FE_CATALOG_SLUGS, (
            "FE_SECTION_SLUGS constant drifted from FE catalog. "
            f"Missing: {FE_CATALOG_SLUGS - FE_SECTION_SLUGS}. "
            f"Extra: {FE_SECTION_SLUGS - FE_CATALOG_SLUGS}."
        )

    def test_field_contract_sections_subset_of_fe_catalog(self) -> None:
        """Every section slug used in OFFER_FIELD_CONTRACTS is a valid FE catalog slug."""
        from src.modules.offer.domain.field_contract import OFFER_FIELD_CONTRACTS

        sections = {c.section for c in OFFER_FIELD_CONTRACTS}
        invalid = sections - FE_CATALOG_SLUGS
        assert not invalid, (
            f"OFFER_FIELD_CONTRACTS uses sections NOT in the FE catalog: {invalid}. "
            "Either add a new FE section or fix the section in OFFER_SECTION_MAP / OFFER_FIELD_OVERRIDES."
        )


class TestArchetypeMapping:
    """Verify every OfferArchetype maps to a valid FE slug."""

    def test_every_archetype_has_details_slug(self) -> None:
        """Every OfferArchetype value has an entry in _DETAILS_BY_ARCHETYPE."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import _DETAILS_BY_ARCHETYPE

        missing = [a for a in OfferArchetype if a not in _DETAILS_BY_ARCHETYPE]
        assert not missing, (
            f"These archetypes are missing from _DETAILS_BY_ARCHETYPE: {missing}. "
            "Every archetype must map to a polymorphic details FE slug."
        )

    def test_every_archetype_details_slug_is_valid_fe_slug(self) -> None:
        """Every value in _DETAILS_BY_ARCHETYPE is a valid FE catalog slug."""
        from src.modules.offer.domain.extraction_section_map import _DETAILS_BY_ARCHETYPE

        invalid = {archetype: slug for archetype, slug in _DETAILS_BY_ARCHETYPE.items() if slug not in FE_CATALOG_SLUGS}
        assert not invalid, f"Invalid FE slugs in _DETAILS_BY_ARCHETYPE: {invalid}"

    def test_resolve_details_section_returns_none_for_none(self) -> None:
        """resolve_details_section(None) returns None gracefully."""
        from src.modules.offer.domain.extraction_section_map import resolve_details_section

        assert resolve_details_section(None) is None

    def test_resolve_details_section_returns_correct_slugs(self) -> None:
        """resolve_details_section returns the expected FE slug per archetype."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import resolve_details_section

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
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["headline_promise", "public_name", "primary_outcome"],
        )
        assert "identity" in result
        assert "headline_promise" in result["identity"]
        assert "public_name" in result["identity"]

    def test_strategy_fields_grouped_correctly(self) -> None:
        """value_level + delivery_model → strategy."""
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["value_level", "delivery_model"],
        )
        assert "strategy" in result
        assert set(result["strategy"]) == {"value_level", "delivery_model"}

    def test_specific_details_routed_by_archetype(self) -> None:
        """specific_details.* → program_details for PROGRAMA archetype."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=OfferArchetype.PROGRAMA,
            filled_paths=["specific_details", "specific_details.duration_weeks"],
        )
        assert "program_details" in result
        assert "identity" not in result

    def test_specific_details_routed_to_product_for_producto(self) -> None:
        """specific_details.* → product_details for PRODUCTO archetype."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=OfferArchetype.PRODUCTO,
            filled_paths=["specific_details.format"],
        )
        assert "product_details" in result

    def test_unknown_fields_silently_ignored(self) -> None:
        """System fields (status, deleted_at, archived_at, metadata_info) produce no output."""
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["status", "deleted_at", "archived_at", "metadata_info"],
        )
        assert result == {}

    def test_idempotent_same_input_same_output(self) -> None:
        """Calling twice with the same args produces the same result."""
        from src.modules.offer.domain.enums import OfferArchetype
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        paths = ["headline_promise", "value_level", "deliverables", "guarantee_type"]
        result1 = fields_to_fe_sections(archetype=OfferArchetype.PROGRAMA, filled_paths=paths)
        result2 = fields_to_fe_sections(archetype=OfferArchetype.PROGRAMA, filled_paths=paths)
        assert result1 == result2

    def test_no_duplicate_paths_in_output(self) -> None:
        """Passing a path twice doesn't produce duplicates in the output."""
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["headline_promise", "headline_promise"],
        )
        assert result["identity"].count("headline_promise") == 1

    def test_empty_input_produces_empty_output(self) -> None:
        """Empty filled_paths produces an empty dict."""
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(archetype=None, filled_paths=[])
        assert result == {}

    def test_pricing_fields_grouped_to_pricing(self) -> None:
        """pricing_options + currency → pricing."""
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["pricing_options", "price_pay_in_full", "currency"],
        )
        assert "pricing" in result

    def test_closing_fields_grouped_to_closing(self) -> None:
        """guarantee_type + checkout_page_url → closing."""
        from src.modules.offer.domain.extraction_section_map import fields_to_fe_sections

        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["guarantee_type", "checkout_page_url", "vsl_link"],
        )
        assert "closing" in result
        assert set(result["closing"]) == {"guarantee_type", "checkout_page_url", "vsl_link"}


class TestLegacyDictRemoved:
    """Anti-regression: OFFER_FIELDS_BY_FE_SECTION must NOT reappear."""

    def test_offer_fields_by_fe_section_does_not_exist(self) -> None:
        """Importing the legacy constant must fail.

        Re-introducing OFFER_FIELDS_BY_FE_SECTION as a parallel manual dict
        defeats the purpose of the field-contract-platform refactor (Fase 04).
        Use ``fields_to_fe_sections()`` or
        ``shared.domain.field_contract.fields_by_section()`` instead.
        """
        import src.modules.offer.domain.extraction_section_map as mod

        assert not hasattr(mod, "OFFER_FIELDS_BY_FE_SECTION"), (
            "OFFER_FIELDS_BY_FE_SECTION reappeared in extraction_section_map.py. "
            "This dict was removed in Fase 04 of the field-contract-platform refactor. "
            "Derive from OFFER_FIELD_CONTRACTS (offer/domain/field_contract.py) "
            "or use shared.domain.field_contract.fields_by_section() instead."
        )

    def test_no_module_redefines_offer_fields_by_fe_section(self) -> None:
        """Grep-based regression: no Python file in src/ redefines the constant."""
        from pathlib import Path

        backend_src = Path(__file__).parent.parent.parent / "src"
        offenders: list[str] = []
        for py_file in backend_src.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            # Lines like `OFFER_FIELDS_BY_FE_SECTION = ...` or
            # `OFFER_FIELDS_BY_FE_SECTION: dict = ...`. Mentions in
            # comments / docstrings are fine.
            for line in content.splitlines():
                stripped = line.lstrip()
                if stripped.startswith(("#", '"', "'")):
                    continue
                if "OFFER_FIELDS_BY_FE_SECTION" in stripped and ("=" in stripped and not stripped.startswith("from ")):
                    # Allow imports that may reference it from tests
                    if "import OFFER_FIELDS_BY_FE_SECTION" in stripped:
                        continue
                    offenders.append(f"{py_file.relative_to(backend_src.parent)}: {stripped}")
        assert not offenders, (
            "OFFER_FIELDS_BY_FE_SECTION was redefined in src/. The legacy dict was "
            "removed in Fase 04. Found in:\n  " + "\n  ".join(offenders)
        )
