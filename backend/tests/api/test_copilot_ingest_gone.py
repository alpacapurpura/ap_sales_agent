"""F10: legacy tenant knowledge ingest endpoints must return HTTP 410 Gone."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_copilot.api.knowledge import router


def _client() -> TestClient:
    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/copilot")
    return TestClient(app)


def test_post_ingest_returns_410() -> None:
    response = _client().post(
        "/api/v1/copilot/ingest",
        files={"file": ("x.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 410
    body = response.json()
    assert "El ingest de documentos por tenant fue retirado" in str(body)


def test_get_search_returns_410() -> None:
    response = _client().get("/api/v1/copilot/search?query=foo")
    assert response.status_code == 410


def test_delete_document_returns_410() -> None:
    response = _client().delete("/api/v1/copilot/abc-123")
    assert response.status_code == 410


def test_responses_carry_migration_hint() -> None:
    response = _client().post("/api/v1/copilot/ingest")
    assert response.status_code == 410
    body = response.json()
    detail = body.get("detail", {})
    assert isinstance(detail, dict), "detail should be the GoneResponse dict"
    assert "migration_hint" in detail
    assert "nicolify_marketing_kb" in detail["detail"]
