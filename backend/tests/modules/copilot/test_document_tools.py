"""Tests for the ``read_document`` copilot tool.

The tool is the canonical lazy path for the LLM to fetch the text content
of a previously-uploaded document/audio asset. It must:

* respect tenant isolation (tenant_id from LangGraph context),
* return the full text for small docs,
* return summary + a relevant fragment when a query is supplied,
* fail gracefully on missing assets or pending extraction.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from luana_core_assets.domain.enums import (
    AssetScope,
    AssetStatus,
    AssetType,
    ExtractionStatus,
)


def _make_asset(**overrides) -> SimpleNamespace:
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "type": AssetType.DOCUMENT.value,
        "filename": "brief.pdf",
        "mime_type": "application/pdf",
        "public_url": "/uploads/brief.pdf",
        "user_description": None,
        "ai_description": None,
        "scope": AssetScope.EPHEMERAL.value,
        "extraction_status": ExtractionStatus.EXTRACTED.value,
        "extracted_text": "Contenido del brief de marca. " * 10,
        "extracted_summary": "Brief de marca para Alpaca Púrpura.",
        "status": AssetStatus.COMPLETED.value,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@patch("luana_core_copilot.application.tools.document_tools.get_tenant_id")
@patch("luana_core_copilot.application.tools.document_tools.AssetExtractionService")
@patch("luana_core_copilot.application.tools.document_tools.AssetRepository")
@patch("luana_core_copilot.application.tools.document_tools.SessionLocal")
def test_read_document_returns_full_text_for_small_asset(
    mock_session_cls: MagicMock,
    mock_repo_cls: MagicMock,
    mock_extract_cls: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """When the doc is small the tool returns the full text + metadata."""
    from luana_core_copilot.application.tools.document_tools import read_document

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    asset = _make_asset(extracted_text="Texto corto del brief.")
    mock_repo_cls.return_value.get_by_id.return_value = asset
    # No extraction needed — already extracted.
    mock_extract_cls.return_value.ensure_extracted.return_value = asset

    asset_id = str(asset.id)
    result = read_document.invoke({"asset_id": asset_id})
    data = json.loads(result)

    assert data["asset_id"] == asset_id
    assert data["filename"] == "brief.pdf"
    assert data["content"] == "Texto corto del brief."
    assert data["truncated"] is False


@patch("luana_core_copilot.application.tools.document_tools.get_tenant_id")
@patch("luana_core_copilot.application.tools.document_tools.AssetExtractionService")
@patch("luana_core_copilot.application.tools.document_tools.AssetRepository")
@patch("luana_core_copilot.application.tools.document_tools.SessionLocal")
def test_read_document_returns_fragment_when_query(
    mock_session_cls: MagicMock,
    mock_repo_cls: MagicMock,
    mock_extract_cls: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """With a query, the tool returns summary + the most relevant fragment."""
    from luana_core_copilot.application.tools.document_tools import read_document

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id

    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    long_text = (
        "Intro genérica. " * 20
        + "El pricing de la oferta premium es USD 499 con 3 cuotas sin interés. "
        + "Garantía de 30 días. " * 5
    )
    asset = _make_asset(extracted_text=long_text)
    mock_repo_cls.return_value.get_by_id.return_value = asset
    mock_extract_cls.return_value.ensure_extracted.return_value = asset

    result = read_document.invoke({"asset_id": str(asset.id), "query": "pricing"})
    data = json.loads(result)

    assert "pricing" in data["content"].lower()
    assert data["fragment_matched"] is True
    assert data["summary"] == "Brief de marca para Alpaca Púrpura."


@patch("luana_core_copilot.application.tools.document_tools.get_tenant_id")
@patch("luana_core_copilot.application.tools.document_tools.AssetRepository")
@patch("luana_core_copilot.application.tools.document_tools.SessionLocal")
def test_read_document_missing_asset_returns_error(
    mock_session_cls: MagicMock,
    mock_repo_cls: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """Unknown asset_id → structured error, never a crash."""
    from luana_core_copilot.application.tools.document_tools import read_document

    mock_get_tenant_id.return_value = uuid4()
    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    mock_repo_cls.return_value.get_by_id.return_value = None

    result = read_document.invoke({"asset_id": str(uuid4())})
    data = json.loads(result)
    assert "error" in data


@patch("luana_core_copilot.application.tools.document_tools.get_tenant_id")
def test_read_document_without_tenant_returns_error(mock_get_tenant_id: MagicMock) -> None:
    """No tenant context → structured error."""
    from luana_core_copilot.application.tools.document_tools import read_document

    mock_get_tenant_id.return_value = None
    result = read_document.invoke({"asset_id": str(uuid4())})
    assert "error" in json.loads(result)


@patch("luana_core_copilot.application.tools.document_tools.get_tenant_id")
@patch("luana_core_copilot.application.tools.document_tools.AssetExtractionService")
@patch("luana_core_copilot.application.tools.document_tools.AssetRepository")
@patch("luana_core_copilot.application.tools.document_tools.SessionLocal")
def test_read_document_triggers_extraction_when_pending(
    mock_session_cls: MagicMock,
    mock_repo_cls: MagicMock,
    mock_extract_cls: MagicMock,
    mock_get_tenant_id: MagicMock,
) -> None:
    """If the asset has not been extracted yet, the tool runs ensure_extracted."""
    from luana_core_copilot.application.tools.document_tools import read_document

    tenant_id = uuid4()
    mock_get_tenant_id.return_value = tenant_id
    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = lambda s: mock_session
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    pending = _make_asset(
        extraction_status=ExtractionStatus.PENDING.value,
        extracted_text=None,
        extracted_summary=None,
    )
    extracted = _make_asset(
        extraction_status=ExtractionStatus.EXTRACTED.value,
        extracted_text="Texto recién extraído",
        extracted_summary="Resumen",
    )
    mock_repo_cls.return_value.get_by_id.return_value = pending
    mock_extract_cls.return_value.ensure_extracted.return_value = extracted

    result = read_document.invoke({"asset_id": str(pending.id)})
    data = json.loads(result)

    mock_extract_cls.return_value.ensure_extracted.assert_called_once()
    assert data["content"] == "Texto recién extraído"
