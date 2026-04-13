"""Tests for the Voice API endpoint."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.api.voice import router
from src.modules.copilot.domain.voice import TranscriptionResult
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


@patch(
    "src.modules.copilot.api.voice.WhisperTranscriber",
)
def test_transcribe_audio_success(
    mock_transcriber_cls: MagicMock,
) -> None:
    """Test successful audio transcription."""
    mock_instance = MagicMock()
    mock_instance.transcribe = AsyncMock(
        return_value=TranscriptionResult(
            text="hola mundo",
            language="es",
            duration_seconds=2.0,
        ),
    )
    mock_transcriber_cls.return_value = mock_instance

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

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "hola mundo"
    assert data["language"] == "es"
    assert data["duration_seconds"] == 2.0


def test_transcribe_audio_no_file() -> None:
    """Test transcribe returns 422 without file."""
    client, _ = _build_client()
    response = client.post(
        "/api/v1/copilot/voice/transcribe",
    )
    assert response.status_code == 422


@patch(
    "src.modules.copilot.api.voice.WhisperTranscriber",
)
def test_transcribe_audio_logs_tenant_context(
    mock_transcriber_cls: MagicMock,
) -> None:
    """Verify endpoint accepts tenant context."""
    mock_instance = MagicMock()
    mock_instance.transcribe = AsyncMock(
        return_value=TranscriptionResult(
            text="prueba",
            language="es",
            duration_seconds=1.5,
        ),
    )
    mock_transcriber_cls.return_value = mock_instance

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

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "prueba"
