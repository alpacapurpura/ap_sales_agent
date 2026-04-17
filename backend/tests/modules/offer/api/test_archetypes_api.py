"""Integration tests for the ``/offer/archetypes/catalog`` endpoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.offer.api.archetypes import router
from src.modules.offer.domain.enums import OfferArchetype


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

    def test_producto_has_no_wizard_copy(self) -> None:
        resp = _client().get("/api/v1/offer/archetypes/catalog")
        prod = next(item for item in resp.json()["archetypes"] if item["archetype"] == OfferArchetype.PRODUCTO.value)
        assert prod["supports_editions"] is False
        assert prod["editions_wizard_copy"] is None
        assert prod["edition_structure"] == "none"
