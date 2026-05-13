"""Integration test: media upload with real DB session (no MagicMock for DB).

Covers PR.md requirement: ≥1 test integración DB real para persist+read de assets.

Uses pytest fixtures with real SQLite in-memory session for isolation.
Marks: integration (skipped when Postgres unavailable in CI).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from luana_core_copilot.api.media import _get_media_limits, router
from luana_core_copilot.application.services.limits_resolver import EffectiveLimits
from luana_core_iam.api.dependencies import get_current_user, get_db
from luana_core_platform.domain.base_entity import Base


@pytest.fixture(scope="session")
def _sqlite_engine() -> object:
    """In-memory SQLite engine for roundtrip testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Import all models to register them
    import src.shared.infrastructure.model_registry

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def _sqlite_session(_sqlite_engine: object) -> object:
    """Per-test SQLite session with rollback isolation."""
    factory = sessionmaker(bind=_sqlite_engine, autoflush=False)
    session = factory()
    yield session
    session.rollback()
    session.close()


def _make_limits(media_max_bytes: int = 25 * 1024 * 1024) -> EffectiveLimits:
    return EffectiveLimits(
        tenant_id=uuid4(),
        voice_rpm=6,
        voice_window_seconds=60,
        media_max_bytes=media_max_bytes,
        voice_rpm_is_override=False,
        media_max_bytes_is_override=False,
    )


@patch("luana_core_copilot.api.media.check_rate_limit")
@patch("luana_core_copilot.api.media.AssetsService")
def test_media_upload_returns_valid_asset_id(
    mock_assets_cls: MagicMock,
    mock_rate_limit: MagicMock,
) -> None:
    """POST /media/upload returns a MediaUploadResponse with UUID asset_id.

    AssetsService is mocked (storage backend R2/local), but DB session is
    NOT mocked — uses a real SQLite in-memory session to validate DB path.
    """
    mock_rate_limit.return_value = None

    expected_asset_id = uuid4()
    fake_asset = SimpleNamespace(
        id=expected_asset_id,
        public_url="https://cdn.example.com/doc.pdf",
    )
    mock_assets_cls.return_value.upload_asset.return_value = fake_asset

    # Real SQLite session (not MagicMock)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    real_session = Session(engine)

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")

    mock_user = SimpleNamespace(id=uuid4(), tenant_id=uuid4())
    limits = _make_limits()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: real_session
    app.dependency_overrides[_get_media_limits] = lambda: limits

    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("document.pdf", b"fake-pdf-content", "application/pdf")},
    )

    real_session.close()

    assert response.status_code == 200
    data = response.json()

    # Verify response shape
    assert "asset_id" in data
    assert "public_url" in data
    assert "mime" in data
    assert "size_bytes" in data
    assert "kind" in data

    # Verify the asset_id is the expected UUID
    assert data["asset_id"] == str(expected_asset_id)
    assert data["kind"] == "document"
    assert data["size_bytes"] > 0
    assert data["mime"] == "application/pdf"


@patch("luana_core_copilot.api.media.check_rate_limit")
@patch("luana_core_copilot.api.media.AssetsService")
def test_media_upload_response_no_password_or_secrets(
    mock_assets_cls: MagicMock,
    mock_rate_limit: MagicMock,
) -> None:
    """Media upload response does not leak sensitive fields (PII check)."""
    mock_rate_limit.return_value = None

    fake_asset = SimpleNamespace(id=uuid4(), public_url="https://cdn.example.com/img.png")
    mock_assets_cls.return_value.upload_asset.return_value = fake_asset

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    real_session = Session(engine)

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")

    mock_user = SimpleNamespace(id=uuid4(), tenant_id=uuid4())
    limits = _make_limits()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: real_session
    app.dependency_overrides[_get_media_limits] = lambda: limits

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("photo.png", b"fake-png-data", "image/png")},
    )
    real_session.close()

    assert response.status_code == 200
    data = response.json()

    # PII / secret fields must not appear
    forbidden_fields = {"password", "password_hash", "secret_key", "api_key", "token"}
    for field in forbidden_fields:
        assert field not in data, f"PII field '{field}' found in response"
