"""Integration tests for the ``/offer/ladder-hints/catalog`` endpoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.offer.api.offer_ladder_hints import router
from src.modules.offer.domain.enums import OfferValueLevel
from src.shared.domain.expert_business_type import ExpertBusinessType


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/offer/ladder-hints")
    return TestClient(app)


class TestOfferLadderHintsEndpoint:
    def test_returns_200_without_auth(self) -> None:
        resp = _client().get("/api/v1/offer/ladder-hints/catalog")
        assert resp.status_code == 200

    def test_payload_has_version_and_all_fortyfive_entries(self) -> None:
        resp = _client().get("/api/v1/offer/ladder-hints/catalog")
        body = resp.json()
        assert body["version"]
        expected = len(ExpertBusinessType) * len(OfferValueLevel)
        assert len(body["hints"]) == expected

    def test_entries_have_required_fields(self) -> None:
        resp = _client().get("/api/v1/offer/ladder-hints/catalog")
        required = {
            "business_type",
            "value_level",
            "examples_es",
            "typical_offer_type_es",
            "typical_price_min_usd",
            "typical_price_max_usd",
        }
        for entry in resp.json()["hints"]:
            missing = required - set(entry)
            assert not missing, f"hint ({entry['business_type']}, {entry['value_level']}) missing {missing}"
            assert entry["typical_offer_type_es"]
            assert isinstance(entry["examples_es"], list)
            assert entry["examples_es"]

    def test_every_pair_is_returned_exactly_once(self) -> None:
        resp = _client().get("/api/v1/offer/ladder-hints/catalog")
        pairs = [(e["business_type"], e["value_level"]) for e in resp.json()["hints"]]
        assert len(pairs) == len(set(pairs)), "duplicate (EBT, VL) pairs in response"

    def test_lead_magnet_entries_have_null_prices(self) -> None:
        resp = _client().get("/api/v1/offer/ladder-hints/catalog")
        lm_entries = [e for e in resp.json()["hints"] if e["value_level"] == OfferValueLevel.LEAD_MAGNET.value]
        assert len(lm_entries) == len(ExpertBusinessType)
        for entry in lm_entries:
            assert entry["typical_price_min_usd"] is None
            assert entry["typical_price_max_usd"] is None

    def test_profesional_salud_activacion_has_latam_pricing(self) -> None:
        """Smoke test that the Latam recalibration landed: first consultation
        for a healthcare professional is not $297+."""
        resp = _client().get("/api/v1/offer/ladder-hints/catalog")
        salud_act = next(
            e
            for e in resp.json()["hints"]
            if e["business_type"] == ExpertBusinessType.PROFESIONAL_SALUD.value
            and e["value_level"] == OfferValueLevel.ACTIVACION.value
        )
        assert salud_act["typical_price_min_usd"] is not None
        assert salud_act["typical_price_min_usd"] < 50
        assert "consulta" in salud_act["typical_offer_type_es"].lower()
