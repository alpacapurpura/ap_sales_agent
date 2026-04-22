"""Tests for the media upload endpoint (POST /copilot/media/upload).

RED phase: defines the expected contract for the upload endpoint.
"""

from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.iam.api.dependencies import get_current_user, get_db, get_tenant_context


def _fresh_db_mock() -> MagicMock:
    """DB dependency override — returns a new MagicMock per request.

    Using `MagicMock` directly as the override makes FastAPI introspect
    `MagicMock.__init__`'s `(*args, **kw)` signature and treat them as query
    params. A helper function with no args yields no such params.
    """
    return MagicMock()


def _build_app_with_media_router() -> tuple[FastAPI, MagicMock]:
    """Build a test FastAPI app with the media router and mocked deps."""
    from src.modules.copilot.api.media import router

    app = FastAPI()
    tenant_id = uuid4()
    user_id = uuid4()

    mock_user = SimpleNamespace(id=user_id, tenant_id=tenant_id)
    mock_db = MagicMock()

    app.include_router(router, prefix="/api/v1/copilot")
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    return app, mock_db


# ── Happy paths ───────────────────────────────────────────────────────


@patch("src.modules.copilot.api.media.AssetsService")
def test_upload_image_returns_200(mock_assets_cls: MagicMock) -> None:
    """Image upload delegates to AssetsService and returns asset_id + public_url."""
    fake_asset = SimpleNamespace(
        id=uuid4(),
        public_url="https://cdn.example.com/img.png",
        mime_type="image/png",
        filename="photo.png",
        type="IMAGE",
    )
    mock_instance = MagicMock()
    mock_instance.upload_asset.return_value = fake_asset
    mock_assets_cls.return_value = mock_instance

    app, _ = _build_app_with_media_router()
    client = TestClient(app, raise_server_exceptions=True)

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16  # minimal PNG header
    response = client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("photo.png", io.BytesIO(png_bytes), "image/png")},
        data={"kind": "image"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "asset_id" in data
    assert "public_url" in data
    assert "mime" in data
    assert "kind" in data
    assert data["kind"] == "image"


@patch("src.modules.copilot.api.media.AssetsService")
def test_upload_delegates_to_assets_service(mock_assets_cls: MagicMock) -> None:
    """Verify upload_asset is called with tenant_id from auth context."""
    fake_asset = SimpleNamespace(
        id=uuid4(),
        public_url="https://cdn.example.com/doc.pdf",
        mime_type="application/pdf",
        filename="report.pdf",
        type="DOCUMENT",
    )
    mock_instance = MagicMock()
    mock_instance.upload_asset.return_value = fake_asset
    mock_assets_cls.return_value = mock_instance

    app, _ = _build_app_with_media_router()
    client = TestClient(app, raise_server_exceptions=True)

    response = client.post(
        "/api/v1/copilot/media/upload",
        files={
            "file": (
                "report.pdf",
                io.BytesIO(b"%PDF-1.4 test"),
                "application/pdf",
            )
        },
        data={"kind": "document"},
    )

    assert response.status_code == 200
    # upload_asset must have been called once
    assert mock_instance.upload_asset.call_count == 1
    call_kwargs = mock_instance.upload_asset.call_args
    # tenant_id comes from get_current_user.tenant_id
    assert "tenant_id" in call_kwargs.kwargs or call_kwargs.args[0] is not None


# ── Validation failures ───────────────────────────────────────────────


def test_upload_without_file_returns_422() -> None:
    """POST without a file returns 422."""
    from src.modules.copilot.api.media import router

    app = FastAPI()
    tenant_id = uuid4()
    app.include_router(router, prefix="/api/v1/copilot")
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=tenant_id)
    app.dependency_overrides[get_db] = _fresh_db_mock

    client = TestClient(app)
    response = client.post("/api/v1/copilot/media/upload")
    assert response.status_code == 422


@patch("src.modules.copilot.api.media.AssetsService")
def test_upload_unsupported_mime_returns_415(mock_assets_cls: MagicMock) -> None:
    """Unsupported MIME type returns 415 Unsupported Media Type."""
    app, _ = _build_app_with_media_router()
    client = TestClient(app, raise_server_exceptions=True)

    response = client.post(
        "/api/v1/copilot/media/upload",
        files={
            "file": (
                "bad.exe",
                io.BytesIO(b"MZ\x90\x00"),
                "application/x-msdownload",
            )
        },
    )

    assert response.status_code == 415


# ── Tenant isolation ──────────────────────────────────────────────────


@patch("src.modules.copilot.api.media.AssetsService")
def test_upload_passes_tenant_id_to_service(mock_assets_cls: MagicMock) -> None:
    """The tenant_id from auth must be forwarded to AssetsService.upload_asset."""
    expected_tenant_id = uuid4()
    fake_asset = SimpleNamespace(
        id=uuid4(),
        public_url="https://cdn.example.com/img.png",
        mime_type="image/png",
        filename="img.png",
        type="IMAGE",
    )
    mock_instance = MagicMock()
    mock_instance.upload_asset.return_value = fake_asset
    mock_assets_cls.return_value = mock_instance

    from src.modules.copilot.api.media import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")
    app.dependency_overrides[get_tenant_context] = lambda: expected_tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=expected_tenant_id)
    app.dependency_overrides[get_db] = _fresh_db_mock

    client = TestClient(app, raise_server_exceptions=True)
    client.post(
        "/api/v1/copilot/media/upload",
        files={"file": ("img.png", io.BytesIO(b"PNG"), "image/png")},
    )

    call_kwargs = mock_instance.upload_asset.call_args
    # tenant_id must match
    received_tenant = call_kwargs.kwargs.get("tenant_id") or call_kwargs.args[0]
    assert str(received_tenant) == str(expected_tenant_id)
