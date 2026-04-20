"""Integration tests for the ``/offer/value-levels/catalog`` endpoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.offer.api.value_levels import router
from src.modules.offer.domain.enums import OfferValueLevel


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/offer/value-levels")
    return TestClient(app)


class TestValueLevelCatalogEndpoint:
    def test_returns_200_without_auth(self) -> None:
        resp = _client().get("/api/v1/offer/value-levels/catalog")
        assert resp.status_code == 200

    def test_payload_has_version_and_full_ladder(self) -> None:
        resp = _client().get("/api/v1/offer/value-levels/catalog")
        body = resp.json()
        assert body["version"]
        returned = {entry["value_level"] for entry in body["value_levels"]}
        expected = {v.value for v in OfferValueLevel}
        assert returned == expected

    def test_entries_are_sorted_by_funnel_order(self) -> None:
        resp = _client().get("/api/v1/offer/value-levels/catalog")
        orders = [entry["order"] for entry in resp.json()["value_levels"]]
        assert orders == sorted(orders), "endpoint must return entries in funnel order"

    def test_lead_magnet_is_free(self) -> None:
        resp = _client().get("/api/v1/offer/value-levels/catalog")
        lm = next(e for e in resp.json()["value_levels"] if e["value_level"] == OfferValueLevel.LEAD_MAGNET.value)
        assert lm["is_free"] is True
        assert lm["typical_price_min_usd"] is None
        assert lm["typical_price_max_usd"] is None

    def test_paid_rungs_expose_price_range(self) -> None:
        resp = _client().get("/api/v1/offer/value-levels/catalog")
        for entry in resp.json()["value_levels"]:
            if entry["is_free"]:
                continue
            assert entry["typical_price_min_usd"] is not None
            assert entry["typical_price_max_usd"] is not None
            assert entry["typical_price_min_usd"] < entry["typical_price_max_usd"]
