"""Integration tests for the ``/offer/formats/catalog`` endpoint.

The endpoint supports two optional query params:

- ``archetype``: narrow results to one archetype.
- ``business_types``: comma-separated list of ``ExpertBusinessType`` to
  filter + rank by fit (score-descending).

Both are optional. Calling with neither returns the full catalog in its
declared order — useful during Brand Studio onboarding when the tenant
has not yet picked business types.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.offer.api.formats import router
from src.modules.offer.domain.enums import OfferArchetype
from src.shared.domain.expert_business_type import ExpertBusinessType


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/offer/formats")
    return TestClient(app)


class TestFormatCatalogEndpoint:
    def test_returns_200_without_auth(self) -> None:
        resp = _client().get("/api/v1/offer/formats/catalog")
        assert resp.status_code == 200

    def test_default_payload_has_version_and_all_formats(self) -> None:
        resp = _client().get("/api/v1/offer/formats/catalog")
        body = resp.json()
        assert body["version"]
        assert "formats" in body
        assert len(body["formats"]) >= 25  # 5 per archetype minimum

    def test_each_entry_has_required_fields(self) -> None:
        resp = _client().get("/api/v1/offer/formats/catalog")
        required = {
            "format_id",
            "archetype",
            "label_es",
            "description_es",
            "icon_name",
            "format_hint",
            "delivery_model",
            "suitable_for",
            "tags",
        }
        for entry in resp.json()["formats"]:
            missing = required - set(entry)
            assert not missing, f"entry {entry['format_id']} missing {missing}"
            assert isinstance(entry["suitable_for"], dict)
            assert isinstance(entry["tags"], list)

    def test_archetype_filter_narrows_results(self) -> None:
        resp = _client().get(
            "/api/v1/offer/formats/catalog",
            params={"archetype": OfferArchetype.PROGRAMA.value},
        )
        for entry in resp.json()["formats"]:
            assert entry["archetype"] == OfferArchetype.PROGRAMA.value

    def test_unknown_archetype_returns_422(self) -> None:
        resp = _client().get("/api/v1/offer/formats/catalog", params={"archetype": "fake"})
        assert resp.status_code == 422

    def test_business_types_filter_ranks_by_score(self) -> None:
        coach = ExpertBusinessType.COACH_MENTOR.value
        educator = ExpertBusinessType.EDUCADOR_INFOPRODUCTOR.value
        resp = _client().get(
            "/api/v1/offer/formats/catalog",
            params={"business_types": f"{coach},{educator}"},
        )
        formats = resp.json()["formats"]
        # Every entry should have positive score for at least one requested type.
        for entry in formats:
            scores = entry["suitable_for"]
            assert (
                scores.get(ExpertBusinessType.COACH_MENTOR.value, 0) > 0
                or scores.get(ExpertBusinessType.EDUCADOR_INFOPRODUCTOR.value, 0) > 0
            )

    def test_business_types_excludes_irrelevant_formats(self) -> None:
        """A SaaS founder should not see ``experiencia_retiro`` by default."""
        resp = _client().get(
            "/api/v1/offer/formats/catalog",
            params={"business_types": ExpertBusinessType.SAAS_FOUNDER.value},
        )
        format_ids = {entry["format_id"] for entry in resp.json()["formats"]}
        assert "experiencia_retiro" not in format_ids
        # But the custom escape-hatches remain visible for every type.
        assert "experiencia_custom" in format_ids

    def test_unknown_business_type_returns_422(self) -> None:
        resp = _client().get(
            "/api/v1/offer/formats/catalog",
            params={"business_types": "not_a_type"},
        )
        assert resp.status_code == 422
