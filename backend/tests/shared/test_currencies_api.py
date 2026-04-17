"""Integration tests for the ``/shared/currencies/catalog`` endpoint.

Public, tenant-agnostic, versioned — same pattern as the archetype and
value-level catalogs. Clients cache by the ``version`` field and evict
when the catalog expands.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.api.currencies import router
from src.shared.domain.currency_catalog import CURRENCY_CATALOG


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/shared/currencies")
    return TestClient(app)


class TestCurrencyCatalogEndpoint:
    def test_returns_200_without_auth(self) -> None:
        resp = _client().get("/api/v1/shared/currencies/catalog")
        assert resp.status_code == 200

    def test_payload_has_version_and_full_catalog(self) -> None:
        resp = _client().get("/api/v1/shared/currencies/catalog")
        body = resp.json()
        assert body["version"]
        codes = {entry["code"] for entry in body["currencies"]}
        assert codes == set(CURRENCY_CATALOG.keys())

    def test_entries_have_required_fields(self) -> None:
        resp = _client().get("/api/v1/shared/currencies/catalog")
        required = {"code", "label_es", "symbol", "countries_es", "decimal_digits"}
        for entry in resp.json()["currencies"]:
            missing = required - set(entry)
            assert not missing, f"entry {entry['code']} missing {missing}"
            assert isinstance(entry["countries_es"], list)
            assert entry["decimal_digits"] in (0, 2)

    def test_clp_is_integer_currency(self) -> None:
        resp = _client().get("/api/v1/shared/currencies/catalog")
        clp = next(e for e in resp.json()["currencies"] if e["code"] == "CLP")
        assert clp["decimal_digits"] == 0
