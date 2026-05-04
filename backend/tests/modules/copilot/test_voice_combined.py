"""Tests for the combined voice upload+transcribe endpoint.

RED phase: validates the /voice/upload-and-transcribe endpoint behavior.
"""

from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.domain.voice import TranscriptionResult
from src.modules.iam.api.dependencies import get_current_user, get_db, get_tenant_context


def _build_voice_app() -> tuple[FastAPI, MagicMock]:
    """Build a test app with the voice router."""
    from src.modules.copilot.api.voice import router

    app = FastAPI()
    tenant_id = uuid4()
    mock_db = MagicMock()

    app.include_router(router, prefix="/api/v1/copilot/voice")
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=tenant_id)
    app.dependency_overrides[get_db] = lambda: mock_db

    return app, mock_db


@patch("src.modules.copilot.api.voice.AssetsService")
@patch("src.modules.copilot.api.voice.WhisperTranscriber")
def test_voice_upload_and_transcribe_returns_audio_block(
    mock_transcriber_cls: MagicMock,
    mock_assets_cls: MagicMock,
) -> None:
    """Combined endpoint returns an AudioBlock with url + transcript."""
    # Mock transcriber
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe = AsyncMock(
        return_value=TranscriptionResult(
            text="Buenos días",
            language="es",
            duration_seconds=2.5,
        )
    )
    mock_transcriber_cls.return_value = mock_transcriber

    # Mock asset service
    asset_id = uuid4()
    fake_asset = SimpleNamespace(
        id=asset_id,
        public_url="https://cdn.example.com/voice.webm",
        mime_type="audio/webm",
        filename="voice.webm",
        type="AUDIO",
    )
    mock_assets = MagicMock()
    mock_assets.upload_asset.return_value = fake_asset
    mock_assets_cls.return_value = mock_assets

    app, _ = _build_voice_app()
    client = TestClient(app, raise_server_exceptions=True)

    response = client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("voice.webm", io.BytesIO(b"fake-audio"), "audio/webm")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "block" in data
    block = data["block"]
    assert block["type"] == "audio"
    assert "url" in block
    assert "transcript" in block
    assert block["transcript"] == "Buenos días"
    assert "asset_id" in block


@patch("src.modules.copilot.api.voice.AssetsService")
@patch("src.modules.copilot.api.voice.WhisperTranscriber")
def test_voice_upload_stt_fails_transcript_is_empty_string(
    mock_transcriber_cls: MagicMock,
    mock_assets_cls: MagicMock,
) -> None:
    """When STT fails, block.transcript is empty string (not missing/null)."""
    # Transcriber fails
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe = AsyncMock(side_effect=Exception("Whisper API down"))
    mock_transcriber_cls.return_value = mock_transcriber

    # Upload succeeds
    fake_asset = SimpleNamespace(
        id=uuid4(),
        public_url="https://cdn.example.com/voice.webm",
        mime_type="audio/webm",
        filename="voice.webm",
        type="AUDIO",
    )
    mock_assets = MagicMock()
    mock_assets.upload_asset.return_value = fake_asset
    mock_assets_cls.return_value = mock_assets

    app, _ = _build_voice_app()
    client = TestClient(app, raise_server_exceptions=True)

    response = client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("voice.webm", io.BytesIO(b"audio"), "audio/webm")},
    )

    assert response.status_code == 200
    block = response.json()["block"]
    # transcript must be present (empty string, not None)
    assert block["transcript"] == ""
    assert block["type"] == "audio"


def test_voice_combined_no_file_returns_422() -> None:
    """POST without a file returns 422."""
    app, _ = _build_voice_app()
    client = TestClient(app)
    response = client.post("/api/v1/copilot/voice/upload-and-transcribe")
    assert response.status_code == 422


def test_legacy_transcribe_endpoint_still_works() -> None:
    """Legacy /transcribe deprecado: retorna 410 Gone con header X-Deprecation-Notice.

    PI-2 S1 PR-1 (BE side) deprecó este endpoint; migración FE a
    /upload-and-transcribe queda como follow-up PR. Este test garantiza
    que el contrato de deprecación (410 + header) se mantiene estable.
    """
    from src.modules.copilot.api.voice import router

    app = FastAPI()
    tenant_id = uuid4()
    app.include_router(router, prefix="/api/v1/copilot/voice")
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=tenant_id)
    app.dependency_overrides[get_db] = MagicMock

    client = TestClient(app, raise_server_exceptions=True)
    response = client.post(
        "/api/v1/copilot/voice/transcribe",
        files={"file": ("r.webm", io.BytesIO(b"audio"), "audio/webm")},
    )

    assert response.status_code == 410
    assert "upload-and-transcribe" in response.headers.get("X-Deprecation-Notice", "")
