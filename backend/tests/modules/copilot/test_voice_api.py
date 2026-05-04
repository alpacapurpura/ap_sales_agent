"""Tests for the Voice API endpoint.

Legacy /transcribe endpoint deprecated en PI-2 S1 PR-1 (BE side):
returns 410 Gone con header X-Deprecation-Notice. Migración FE a
/upload-and-transcribe pendiente como follow-up PR.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.api.voice import router
from src.modules.iam.api.dependencies import (
    get_current_user,
    get_tenant_context,
)


def _build_client() -> tuple[TestClient, UUID]:
    """Build a test client with overridden deps."""
    app = FastAPI()
    app.include_router(
        router,
        prefix="/api/v1/copilot/voice",
    )
    tenant_id = uuid4()
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
    )
    return TestClient(app), tenant_id


def test_transcribe_audio_success() -> None:
    """Legacy /transcribe returns 410 Gone con deprecation header."""
    client, _ = _build_client()
    response = client.post(
        "/api/v1/copilot/voice/transcribe",
        files={
            "file": (
                "recording.webm",
                b"fake-audio",
                "audio/webm",
            ),
        },
    )

    assert response.status_code == 410
    assert "upload-and-transcribe" in response.headers.get(
        "X-Deprecation-Notice",
        "",
    )


def test_transcribe_audio_no_file() -> None:
    """Test transcribe returns 422 without file."""
    client, _ = _build_client()
    response = client.post(
        "/api/v1/copilot/voice/transcribe",
    )
    assert response.status_code == 422


def test_transcribe_audio_logs_tenant_context() -> None:
    """Legacy /transcribe accepts tenant context y retorna 410 Gone."""
    client, _tenant_id = _build_client()
    response = client.post(
        "/api/v1/copilot/voice/transcribe",
        files={
            "file": (
                "audio.wav",
                b"wav-bytes",
                "audio/wav",
            ),
        },
    )

    assert response.status_code == 410
    assert "upload-and-transcribe" in response.headers.get(
        "X-Deprecation-Notice",
        "",
    )
