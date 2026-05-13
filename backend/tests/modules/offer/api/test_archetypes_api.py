"""Integration tests for the ``/offer/archetypes/catalog`` endpoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_offer_studio.api.archetypes import router
from luana_core_offer_studio.domain.enums import OfferArchetype


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/offer/archetypes")
    return TestClient(app)


class TestArchetypeCatalogEndpoint:
    def test_returns_200_without_auth(self) -> None:
        """Catalog is public domain metadata — no auth required."""
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        assert resp.status_code == 200

    def test_payload_has_version_and_archetypes(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        data = resp.json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert "archetypes" in data
        assert isinstance(data["archetypes"], list)
        assert len(data["archetypes"]) == len(list(OfferArchetype))

    def test_every_archetype_included_once(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        names = {item["archetype"] for item in resp.json()["archetypes"]}
        expected = {a.value for a in OfferArchetype}
        assert names == expected

    def test_experiencia_has_wizard_copy(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        exp = next(item for item in resp.json()["archetypes"] if item["archetype"] == OfferArchetype.EXPERIENCIA.value)
        assert exp["supports_editions"] is True
        assert exp["editions_wizard_copy"] is not None
        assert "salidas" in exp["editions_wizard_copy"]["title"].lower()
        assert exp["edition_noun_es"] == "salida"

    def test_producto_exposes_sku_variant_structure(self) -> None:
        """Sprint 15.1: PRODUCTO now surfaces variant support (SKU_VARIANT)."""
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        prod = next(item for item in resp.json()["archetypes"] if item["archetype"] == OfferArchetype.PRODUCTO.value)
        assert prod["supports_editions"] is True
        assert prod["default_variant_structure"] == "sku_variant"
        assert "sku_variant" in prod["supported_variant_structures"]
        assert prod["allow_single_variant"] is True
        assert prod["edition_noun_es"] == "variante"
        assert prod["editions_wizard_copy"] is not None

    def test_membresia_exposes_tier_variant_structure(self) -> None:
        """Sprint 15.1: MEMBRESIA now surfaces TIER plans (Gold / Platinum)."""
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        mem = next(item for item in resp.json()["archetypes"] if item["archetype"] == OfferArchetype.MEMBRESIA.value)
        assert mem["supports_editions"] is True
        assert mem["default_variant_structure"] == "tier"
        assert "tier" in mem["supported_variant_structures"]
        assert mem["allow_single_variant"] is True
        assert mem["edition_noun_es"] == "plan"
        assert mem["editions_wizard_copy"] is not None


class TestSectionExposure:
    """Phase A.5 of Sprint 6 — archetype entries include sections, and the
    response carries a global section_catalog so clients don't need a second
    round-trip to render metadata for arbitrary section keys."""

    def test_every_archetype_includes_non_empty_sections_list(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        for item in resp.json()["archetypes"]:
            assert "sections" in item, f"{item['archetype']} missing sections field"
            assert isinstance(item["sections"], list)
            assert len(item["sections"]) > 0, f"{item['archetype']} has empty sections"

    def test_section_entries_carry_full_metadata(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        producto = next(
            item for item in resp.json()["archetypes"] if item["archetype"] == OfferArchetype.PRODUCTO.value
        )
        required_fields = (
            "key",
            "label_es",
            "subtitle_es",
            "help_text_es",
            "icon_name",
            "scope",
            "completion_weight",
            "required_to_publish",
        )
        for section in producto["sections"]:
            for required in required_fields:
                assert required in section, f"section missing {required}: {section}"
            assert section["scope"] in {"offer_level", "edition_level", "mixed"}
            assert isinstance(section["completion_weight"], (int, float))
            assert isinstance(section["required_to_publish"], bool)
            assert section["help_text_es"]

    def test_experiencia_surfaces_event_details_as_edition_level(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        exp = next(item for item in resp.json()["archetypes"] if item["archetype"] == OfferArchetype.EXPERIENCIA.value)
        keys = [s["key"] for s in exp["sections"]]
        assert "event_details" in keys
        event_details = next(s for s in exp["sections"] if s["key"] == "event_details")
        assert event_details["scope"] == "edition_level"

    def test_producto_has_no_edition_level_sections(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        prod = next(item for item in resp.json()["archetypes"] if item["archetype"] == OfferArchetype.PRODUCTO.value)
        scopes = {s["scope"] for s in prod["sections"]}
        assert "edition_level" not in scopes

    def test_response_includes_global_section_catalog(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        data = resp.json()
        assert "section_catalog" in data
        assert isinstance(data["section_catalog"], list)
        assert len(data["section_catalog"]) >= 10
        required_fields = (
            "key",
            "label_es",
            "subtitle_es",
            "help_text_es",
            "icon_name",
            "scope",
            "completion_weight",
            "required_to_publish",
        )
        for entry in data["section_catalog"]:
            for required in required_fields:
                assert required in entry, f"global catalog entry missing {required}: {entry}"

    def test_global_section_catalog_keys_are_unique(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        keys = [entry["key"] for entry in resp.json()["section_catalog"]]
        assert len(keys) == len(set(keys)), "global section_catalog has duplicate keys"

    def test_archetype_sections_are_subset_of_global_catalog(self) -> None:
        """Every key an archetype points at must be resolvable via the global catalog."""
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        data = resp.json()
        global_keys = {entry["key"] for entry in data["section_catalog"]}
        for item in data["archetypes"]:
            per_archetype_keys = {s["key"] for s in item["sections"]}
            missing = per_archetype_keys - global_keys
            assert missing == set(), f"{item['archetype']} references keys not in global catalog: {missing}"

    def test_version_bumped_for_sections_rollout(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        version = resp.json()["version"]
        # Phase A.5 requires a date strictly >= 2026-04-18 (the sections rollout).
        # Bump again on every material change per api/archetypes.py docstring.
        assert version >= "2026-04-18", f"version {version} must be bumped to reflect the sections rollout"
