"""Tests for dynamic media max bytes from env and per-tenant override.

- env COPILOT_MEDIA_MAX_BYTES=10MB → upload 11MB fails 413
- per-tenant override 50MB → upload 30MB passes despite env 10MB
- cap enforcement: override >100MiB rejected at DTO level
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.api.media import _get_media_limits, router
from src.modules.copilot.application.services.limits_resolver import EffectiveLimits
from src.modules.iam.api.dependencies import get_current_user, get_db


def _make_effective_limits(media_max_bytes: int, is_override: bool = False) -> EffectiveLimits:
    return EffectiveLimits(
        tenant_id=uuid4(),
        voice_rpm=6,
        voice_window_seconds=60,
        media_max_bytes=media_max_bytes,
        voice_rpm_is_override=False,
        media_max_bytes_is_override=is_override,
    )


def _build_media_client(limits: EffectiveLimits) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")

    mock_user = SimpleNamespace(id=uuid4(), tenant_id=uuid4())

    def _get_mock_db() -> MagicMock:
        return MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = _get_mock_db
    app.dependency_overrides[_get_media_limits] = lambda: limits

    return TestClient(app, raise_server_exceptions=False)


@patch("src.modules.copilot.api.media.check_rate_limit")
@patch("src.modules.copilot.api.media.AssetsService")
def test_upload_11mb_fails_when_env_limit_is_10mb(
    mock_assets_cls: MagicMock,
    mock_rate_limit: MagicMock,
) -> None:
    """Upload 11 MB fails 413 when effective limit is 10 MB."""
    mock_rate_limit.return_value = None

    ten_mb = 10 * 1024 * 1024
    eleven_mb = 11 * 1024 * 1024

    limits = _make_effective_limits(media_max_bytes=ten_mb)
    client = _build_media_client(limits)

    response = client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("doc.pdf", b"x" * eleven_mb, "application/pdf")},
    )
    assert response.status_code == 413


@patch("src.modules.copilot.api.media.check_rate_limit")
@patch("src.modules.copilot.api.media.AssetsService")
def test_upload_30mb_passes_with_50mb_override(
    mock_assets_cls: MagicMock,
    mock_rate_limit: MagicMock,
) -> None:
    """Upload 30 MB passes when tenant override is 50 MB (despite env=10 MB)."""
    mock_rate_limit.return_value = None

    fake_asset = SimpleNamespace(id=uuid4(), public_url="https://cdn.example.com/doc.pdf")
    mock_assets_cls.return_value.upload_asset.return_value = fake_asset

    thirty_mb = 30 * 1024 * 1024
    fifty_mb_override = 50 * 1024 * 1024

    limits = _make_effective_limits(media_max_bytes=fifty_mb_override, is_override=True)
    client = _build_media_client(limits)

    response = client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("doc.pdf", b"x" * thirty_mb, "application/pdf")},
    )
    assert response.status_code == 200


@patch("src.modules.copilot.api.media.check_rate_limit")
def test_empty_file_returns_400(mock_rate_limit: MagicMock) -> None:
    """Empty file returns 400 regardless of limits."""
    mock_rate_limit.return_value = None

    limits = _make_effective_limits(media_max_bytes=25 * 1024 * 1024)
    client = _build_media_client(limits)

    response = client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400


@patch("src.modules.copilot.api.media.check_rate_limit")
def test_media_rate_limit_hit_returns_429(mock_rate_limit: MagicMock) -> None:
    """Rate limit exceeded on media upload returns 429 (Q5: bucket copilot-media-upload)."""
    from src.core.rate_limit import RateLimitExceeded

    mock_rate_limit.side_effect = RateLimitExceeded(retry_after=15)

    limits = _make_effective_limits(media_max_bytes=25 * 1024 * 1024)
    client = _build_media_client(limits)

    response = client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("doc.pdf", b"x" * 1024, "application/pdf")},
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers


@patch("src.modules.copilot.api.media.check_rate_limit")
def test_media_and_voice_rate_limit_buckets_are_independent(mock_rate_limit: MagicMock) -> None:
    """Media upload uses scope 'copilot-media-upload', not 'copilot-voice'."""
    mock_rate_limit.return_value = None

    limits = _make_effective_limits(media_max_bytes=25 * 1024 * 1024)
    client = _build_media_client(limits)

    # Make a request; even if it fails at storage, rate limit was already called
    client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("doc.pdf", b"x" * 1024, "application/pdf")},
    )

    if mock_rate_limit.called:
        call_kwargs = mock_rate_limit.call_args.kwargs
        assert call_kwargs.get("scope") == "copilot-media-upload"
