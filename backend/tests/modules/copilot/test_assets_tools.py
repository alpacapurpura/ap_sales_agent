"""Tests for copilot outbound assets tools.

RED phase: validates tenant scoping, search/get behavior.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


def _make_mock_asset(
    asset_id=None,
    public_url: str = "https://cdn.example.com/flyer.png",
    mime_type: str = "image/png",
    asset_type: str = "IMAGE",
    filename: str = "flyer.png",
    description: str = "Flyer de lanzamiento",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=asset_id or uuid4(),
        public_url=public_url,
        mime_type=mime_type,
        type=asset_type,
        filename=filename,
        user_description=description,
        ai_description=None,
        deleted_at=None,
    )


# ── search_assets ─────────────────────────────────────────────────────


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
@patch("src.modules.copilot.application.tools.assets_tools._search_assets_query")
@patch("src.modules.copilot.application.tools.assets_tools.SessionLocal")
def test_search_assets_returns_asset_refs(
    mock_session_cls: MagicMock,
    mock_search_query: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """search_assets returns a JSON list of AssetRef dicts."""
    from src.modules.copilot.application.tools.assets_tools import search_assets

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    mock_search_query.return_value = [_make_mock_asset()]

    result = search_assets.invoke({"query": "flyer lanzamiento", "limit": 5})

    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 1
    assert "asset_id" in data[0]
    assert "public_url" in data[0]
    assert "kind" in data[0]
    # storage_path must NOT be returned (internal field)
    assert "storage_path" not in data[0]


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
def test_search_assets_without_tenant_returns_error(
    mock_get_tenant_id: MagicMock,
) -> None:
    """search_assets returns an error JSON when tenant context is missing."""
    from src.modules.copilot.application.tools.assets_tools import search_assets

    mock_get_tenant_id.return_value = None

    result = search_assets.invoke({"query": "something"})
    data = json.loads(result)
    assert "error" in data


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
@patch("src.modules.copilot.application.tools.assets_tools._search_assets_query")
@patch("src.modules.copilot.application.tools.assets_tools.SessionLocal")
def test_search_assets_filters_by_kind(
    mock_session_cls: MagicMock,
    mock_search_query: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """Kind parameter is forwarded to the internal search query."""
    from src.modules.copilot.application.tools.assets_tools import search_assets

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    mock_search_query.return_value = []

    search_assets.invoke({"query": "logo", "kind": "image", "limit": 3})

    # The search function must have been called once
    assert mock_search_query.call_count == 1
    call_kwargs = mock_search_query.call_args
    # Verify kind was passed (positional or keyword)
    passed_kind = call_kwargs.kwargs.get("kind") or (call_kwargs.args[3] if len(call_kwargs.args) > 3 else None)
    assert passed_kind == "image"


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
@patch("src.modules.copilot.application.tools.assets_tools._search_assets_query")
@patch("src.modules.copilot.application.tools.assets_tools.SessionLocal")
def test_search_assets_empty_results_returns_empty_list(
    mock_session_cls: MagicMock,
    mock_search_query: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """When no assets found, returns an empty JSON list."""
    from src.modules.copilot.application.tools.assets_tools import search_assets

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_search_query.return_value = []

    result = search_assets.invoke({"query": "xyz_not_found"})
    data = json.loads(result)
    assert data == []


# ── scope filter ──────────────────────────────────────────────────────


def test_search_assets_query_excludes_ephemeral(db, seed_tenant, tenant_id) -> None:
    """Ephemeral assets must NOT appear in search_assets results.

    This is the anti-pollution guard: temporary uploads from the copilot
    chat stay out of the library catalog, so the sales_agent / landing
    builders only surface canonical assets.
    """
    import uuid as _uuid

    from src.modules.assets.domain.enums import (
        AssetScope,
        AssetStatus,
        AssetType,
        StorageProvider,
    )
    from src.modules.assets.infrastructure.models.asset_model import AssetModel
    from src.modules.copilot.application.tools.assets_tools import _search_assets_query

    def _make(scope: str, filename: str) -> None:
        db.add(
            AssetModel(
                id=_uuid.uuid4(),
                tenant_id=tenant_id,
                type=AssetType.IMAGE.value,
                filename=filename,
                mime_type="image/png",
                storage_provider=StorageProvider.LOCAL.value,
                storage_path=f"/tmp/{filename}",
                public_url=f"/static/{filename}",
                status=AssetStatus.COMPLETED.value,
                scope=scope,
            ),
        )

    _make(AssetScope.EPHEMERAL.value, "temp-context.png")
    _make(AssetScope.LIBRARY.value, "logo.png")
    _make(AssetScope.DELIVERABLE.value, "flyer.png")
    db.commit()

    results = _search_assets_query(db, tenant_id=tenant_id, query="png")
    names = {r.filename for r in results}

    assert "temp-context.png" not in names
    assert {"logo.png", "flyer.png"}.issubset(names)


# ── get_asset ─────────────────────────────────────────────────────────


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
@patch("src.modules.copilot.application.tools.assets_tools.AssetRepository")
@patch("src.modules.copilot.application.tools.assets_tools.SessionLocal")
def test_get_asset_returns_ref(
    mock_session_cls: MagicMock,
    mock_repo_cls: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """get_asset returns an AssetRef JSON for a valid asset_id."""
    from src.modules.copilot.application.tools.assets_tools import get_asset

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    mock_repo = MagicMock()
    mock_repo_cls.return_value = mock_repo

    asset_id = uuid4()
    mock_repo.get_by_id.return_value = _make_mock_asset(asset_id=asset_id)

    result = get_asset.invoke({"asset_id": str(asset_id)})

    data = json.loads(result)
    assert data.get("asset_id") == str(asset_id)
    assert "storage_path" not in data
    assert "public_url" in data
    assert "kind" in data


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
@patch("src.modules.copilot.application.tools.assets_tools.AssetRepository")
@patch("src.modules.copilot.application.tools.assets_tools.SessionLocal")
def test_get_asset_not_found_returns_error_json(
    mock_session_cls: MagicMock,
    mock_repo_cls: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """get_asset returns error JSON for cross-tenant or missing asset."""
    from src.modules.copilot.application.tools.assets_tools import get_asset

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    mock_repo = MagicMock()
    mock_repo_cls.return_value = mock_repo
    mock_repo.get_by_id.return_value = None

    result = get_asset.invoke({"asset_id": str(uuid4())})

    data = json.loads(result)
    assert data.get("error") == "not_found"


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
def test_get_asset_without_tenant_returns_error(
    mock_get_tenant_id: MagicMock,
) -> None:
    """get_asset returns an error JSON when tenant context is missing."""
    from src.modules.copilot.application.tools.assets_tools import get_asset

    mock_get_tenant_id.return_value = None

    result = get_asset.invoke({"asset_id": str(uuid4())})
    data = json.loads(result)
    assert "error" in data


@patch("src.modules.copilot.application.tools.assets_tools.get_tenant_id")
def test_get_asset_invalid_uuid_returns_not_found(
    mock_get_tenant_id: MagicMock,
) -> None:
    """Invalid asset_id UUID returns not_found (not a 500)."""
    from src.modules.copilot.application.tools.assets_tools import get_asset

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    result = get_asset.invoke({"asset_id": "not-a-valid-uuid"})
    data = json.loads(result)
    assert data.get("error") == "not_found"


# ── ASSETS_TOOLS list ─────────────────────────────────────────────────


def test_assets_tools_list_exported() -> None:
    """ASSETS_TOOLS list must contain the two tool functions."""
    from src.modules.copilot.application.tools.assets_tools import (
        ASSETS_TOOLS,
        get_asset,
        search_assets,
    )

    tool_names = {t.name for t in ASSETS_TOOLS}
    assert "search_assets" in tool_names
    assert "get_asset" in tool_names
