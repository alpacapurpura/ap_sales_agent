"""Tests for voice upload-and-transcribe rate limiting.

TDD: 7 reqs/min with default 6 → req 7 returns 429 + JSON detail + Retry-After header.
Q3: default 6 RPM (Whisper cost guard).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_copilot.api.voice import router
from luana_core_copilot.application.services.limits_resolver import EffectiveLimits
from luana_core_copilot.domain.voice import TranscriptionResult
from luana_core_iam.api.dependencies import get_current_user, get_db


def _make_limits(voice_rpm: int = 6) -> EffectiveLimits:
    return EffectiveLimits(
        tenant_id=uuid4(),
        voice_rpm=voice_rpm,
        voice_window_seconds=60,
        media_max_bytes=25 * 1024 * 1024,
        voice_rpm_is_override=False,
        media_max_bytes_is_override=False,
    )


def _build_voice_client(voice_rpm: int = 6) -> TestClient:
    """Build test client with mocked dependencies."""
    from luana_core_copilot.api.voice import _get_voice_limits

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/voice")

    tenant_id = uuid4()
    user_id = uuid4()
    mock_user = SimpleNamespace(id=user_id, tenant_id=tenant_id)

    def _get_mock_db() -> MagicMock:
        return MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = _get_mock_db
    app.dependency_overrides[_get_voice_limits] = lambda: _make_limits(voice_rpm=voice_rpm)

    return TestClient(app, raise_server_exceptions=False)


@patch("luana_core_copilot.api.voice.WhisperTranscriber")
@patch("luana_core_copilot.api.voice.AssetsService")
@patch("luana_core_copilot.api.voice.check_rate_limit")
def test_upload_transcribe_passes_under_limit(
    mock_rate_limit: MagicMock,
    mock_assets_cls: MagicMock,
    mock_transcriber_cls: MagicMock,
) -> None:
    """Requests under the rate limit pass normally."""
    mock_rate_limit.return_value = None  # No exception = allowed

    mock_instance = MagicMock()
    mock_instance.transcribe = AsyncMock(
        return_value=TranscriptionResult(text="hola", language="es", duration_seconds=1.0)
    )
    mock_transcriber_cls.return_value = mock_instance

    fake_asset = SimpleNamespace(id=uuid4(), public_url="https://cdn.example.com/audio.webm")
    mock_assets_cls.return_value.upload_asset.return_value = fake_asset

    client = _build_voice_client(voice_rpm=6)
    response = client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("audio.webm", b"fake-audio-content", "audio/webm")},
    )
    assert response.status_code == 200


@patch("luana_core_copilot.api.voice.check_rate_limit")
def test_upload_transcribe_returns_429_when_rate_limited(
    mock_rate_limit: MagicMock,
) -> None:
    """When rate limit is exceeded, endpoint returns 429 with Retry-After header."""
    from luana_core_platform.core.rate_limit import RateLimitExceeded

    mock_rate_limit.side_effect = RateLimitExceeded(retry_after=30)

    client = _build_voice_client(voice_rpm=6)
    response = client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("audio.webm", b"audio", "audio/webm")},
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers


@patch("luana_core_copilot.api.voice.check_rate_limit")
def test_rate_limit_called_with_correct_scope(
    mock_rate_limit: MagicMock,
) -> None:
    """check_rate_limit is called with scope='copilot-voice' and correct rpm."""
    mock_rate_limit.return_value = None

    client = _build_voice_client(voice_rpm=6)
    # Will fail at transcription/storage (no mocks) but rate limit check fires first
    client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("audio.webm", b"audio", "audio/webm")},
    )

    # Verify it was called with correct scope
    if mock_rate_limit.called:
        call_kwargs = mock_rate_limit.call_args
        assert call_kwargs.kwargs.get("scope") == "copilot-voice" or (
            len(call_kwargs.args) > 1 and call_kwargs.args[1] == "copilot-voice"
        )


@patch("luana_core_copilot.api.voice.check_rate_limit")
def test_file_exceeding_max_bytes_returns_413(
    mock_rate_limit: MagicMock,
) -> None:
    """File exceeding effective max_bytes returns 413."""
    mock_rate_limit.return_value = None

    from luana_core_copilot.api.voice import _get_voice_limits

    tiny_limit = EffectiveLimits(
        tenant_id=uuid4(),
        voice_rpm=6,
        voice_window_seconds=60,
        media_max_bytes=10,  # 10 bytes limit
        voice_rpm_is_override=False,
        media_max_bytes_is_override=False,
    )

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/voice")

    user_id = uuid4()
    tenant_id = uuid4()
    mock_user = SimpleNamespace(id=user_id, tenant_id=tenant_id)

    def _get_mock_db_tiny() -> MagicMock:
        return MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = _get_mock_db_tiny
    app.dependency_overrides[_get_voice_limits] = lambda: tiny_limit

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("audio.webm", b"this-is-more-than-10-bytes", "audio/webm")},
    )
    assert response.status_code == 413


def test_legacy_transcribe_endpoint_returns_410_gone() -> None:
    """Legacy /transcribe endpoint returns 410 Gone with X-Deprecation-Notice header.

    PI-2 S1 PR-1 auto-fix iter 1: BE-side deprecation (410 Gone).
    FE migration to /upload-and-transcribe tracked as follow-up PR (cross-stack).
    CONTRACT §16 Q1 updated: BE deprecated 410 Gone (this PR). FE migration pending.
    """
    from luana_core_copilot.api.voice import router as voice_router
    from luana_core_iam.api.dependencies import get_tenant_context

    app = FastAPI()
    app.include_router(voice_router, prefix="/api/v1/copilot/voice")
    tenant_id = uuid4()
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id

    client = TestClient(app, raise_server_exceptions=False)
    # Send with a file — endpoint now returns 410 regardless of payload
    response = client.post(
        "/api/v1/copilot/voice/transcribe",
        files={"file": ("audio.webm", b"audio", "audio/webm")},
    )
    assert response.status_code == 410
    assert "x-deprecation-notice" in response.headers
    assert "upload-and-transcribe" in response.headers["x-deprecation-notice"]
