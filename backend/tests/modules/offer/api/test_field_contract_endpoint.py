"""Smoke test for ``GET /api/v1/offer/field-contract``.

Fase 01 pilot — pricing contracts only. Validates shape and that every
pricing path declared in the FE pricing schema has a contract entry.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.modules.offer.domain.field_contract import (
    FIELD_CONTRACT_SNAPSHOT,
    PRICING_FIELD_CONTRACTS,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_endpoint_returns_200_with_versioned_contracts(client: TestClient) -> None:
    response = client.get("/api/v1/offer/field-contract")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["version"] == FIELD_CONTRACT_SNAPSHOT.version
    assert isinstance(body["contracts"], list)
    assert body["contracts"], "Contract registry must not be empty in Fase 01 pilot."


def test_pricing_contracts_carry_expected_paths(client: TestClient) -> None:
    response = client.get("/api/v1/offer/field-contract")
    paths = {c["path"] for c in response.json()["contracts"]}

    expected_pricing_paths = {fc.path for fc in PRICING_FIELD_CONTRACTS}
    # Fase 01 must surface every pricing contract.
    missing = expected_pricing_paths - paths
    assert not missing, f"Pricing contracts missing from endpoint: {missing}"


def test_pricing_latam_new_fields_are_present(client: TestClient) -> None:
    response = client.get("/api/v1/offer/field-contract")
    paths = {c["path"] for c in response.json()["contracts"]}
    for new_path in ("tax_included", "installments_available", "accepted_payment_providers"):
        assert new_path in paths, f"Fase 01 must emit {new_path}"


def test_every_contract_has_required_keys(client: TestClient) -> None:
    response = client.get("/api/v1/offer/field-contract")
    for contract in response.json()["contracts"]:
        assert set(contract.keys()) >= {
            "path",
            "type",
            "owner",
            "section",
            "required",
        }, f"Missing keys on {contract}"
