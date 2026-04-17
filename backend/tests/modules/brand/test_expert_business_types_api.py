"""Integration tests for the ``/brand/expert-business-types/catalog`` endpoint.

The catalog is public, tenant-agnostic domain metadata — same pattern as
``/offer/archetypes/catalog``. Clients cache forever, cache-bust on version
change when the catalog evolves.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.brand.api.expert_business_types import router
from src.shared.domain.expert_business_type import ExpertBusinessType


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/brand/expert-business-types")
    return TestClient(app)


class TestExpertBusinessTypesCatalogEndpoint:
    def test_returns_200_without_auth(self) -> None:
        resp = _client().get("/api/v1/brand/expert-business-types/catalog")
        assert resp.status_code == 200

    def test_payload_has_version_and_full_catalog(self) -> None:
        resp = _client().get("/api/v1/brand/expert-business-types/catalog")
        body = resp.json()
        assert "version" in body
        assert body["version"]
        assert "business_types" in body
        returned = {entry["business_type"] for entry in body["business_types"]}
        expected = {t.value for t in ExpertBusinessType}
        assert returned == expected

    def test_entries_have_required_fields(self) -> None:
        resp = _client().get("/api/v1/brand/expert-business-types/catalog")
        required = {
            "business_type",
            "label_es",
            "description_es",
            "sells_es",
            "icon_name",
            "examples_es",
        }
        for entry in resp.json()["business_types"]:
            missing = required - set(entry)
            assert not missing, f"entry {entry['business_type']} missing {missing}"
            assert entry["label_es"]
            assert entry["description_es"]
            assert entry["sells_es"]
            assert entry["icon_name"]
            assert isinstance(entry["examples_es"], list)
            assert entry["examples_es"]

    def test_saas_founder_entry(self) -> None:
        resp = _client().get("/api/v1/brand/expert-business-types/catalog")
        saas = next(
            e for e in resp.json()["business_types"] if e["business_type"] == ExpertBusinessType.SAAS_FOUNDER.value
        )
        assert "software" in saas["description_es"].lower() or "saas" in saas["label_es"].lower()
