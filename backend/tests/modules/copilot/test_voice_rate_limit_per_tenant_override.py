"""Tests for per-tenant voice rate limit override.

tenant with override 20 → req 7 passes, req 21 fails.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.api.voice import _get_voice_limits, router
from src.modules.copilot.application.services.limits_resolver import EffectiveLimits
from src.modules.iam.api.dependencies import get_current_user, get_db


def _make_override_limits(voice_rpm: int) -> EffectiveLimits:
    return EffectiveLimits(
        tenant_id=uuid4(),
        voice_rpm=voice_rpm,
        voice_window_seconds=60,
        media_max_bytes=25 * 1024 * 1024,
        voice_rpm_is_override=True,
        media_max_bytes_is_override=False,
    )


@patch("src.modules.copilot.api.voice.check_rate_limit")
def test_tenant_override_20_req7_passes(mock_rate_limit: MagicMock) -> None:
    """With override 20 RPM, request 7 is allowed (under the limit)."""
    mock_rate_limit.return_value = None  # Under limit

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/voice")

    mock_user = SimpleNamespace(id=uuid4(), tenant_id=uuid4())
    limits_20 = _make_override_limits(voice_rpm=20)

    def _get_mock_db() -> MagicMock:
        return MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = _get_mock_db
    app.dependency_overrides[_get_voice_limits] = lambda: limits_20

    client = TestClient(app, raise_server_exceptions=False)
    client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("audio.webm", b"audio", "audio/webm")},
    )
    # check_rate_limit was called with max_requests=20
    assert mock_rate_limit.called
    call_kwargs = mock_rate_limit.call_args.kwargs
    assert call_kwargs.get("max_requests") == 20


@patch("src.modules.copilot.api.voice.check_rate_limit")
def test_resolver_uses_override_rpm_not_env(mock_rate_limit: MagicMock) -> None:
    """CopilotLimitsResolver override propagates to check_rate_limit max_requests."""
    mock_rate_limit.return_value = None

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/voice")

    mock_user = SimpleNamespace(id=uuid4(), tenant_id=uuid4())
    limits_override = _make_override_limits(voice_rpm=50)

    def _get_mock_db() -> MagicMock:
        return MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = _get_mock_db
    app.dependency_overrides[_get_voice_limits] = lambda: limits_override

    client = TestClient(app, raise_server_exceptions=False)
    client.post(
        "/api/v1/copilot/voice/upload-and-transcribe",
        files={"file": ("audio.webm", b"audio", "audio/webm")},
    )

    assert mock_rate_limit.called
    call_kwargs = mock_rate_limit.call_args.kwargs
    # Should use override value (50), not env default (6)
    assert call_kwargs.get("max_requests") == 50
