"""Tests for orchestrator attachment rendering (hint vs inline).

The orchestrator materializes user-supplied blocks into a string that is
appended to the ``HumanMessage`` content before the LLM call. Since moving
to a three-layer design (ingest / hint / retrieval), the rules are:

* Small documents (< INLINE_THRESHOLD chars) continue to be inlined —
  paying a tool hop isn't worth it.
* Large documents emit a *hint* with filename, asset_id, and summary.
  The LLM is expected to call ``read_document`` for detail.
* Fallback (no extracted text yet): emit a hint that advertises the
  asset so the LLM can invoke ``read_document`` (which triggers
  extraction on demand).
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from luana_core_copilot.application.orchestrator.chat import (
    INLINE_DOCUMENT_THRESHOLD,
    _render_attachment_context,
)


def _mock_asset(**overrides) -> SimpleNamespace:
    defaults = {
        "id": uuid.uuid4(),
        "filename": "brief.pdf",
        "mime_type": "application/pdf",
        "extracted_text": None,
        "extracted_summary": None,
        "extraction_status": "pending",
        "storage_path": "/tmp/brief.pdf",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@patch("luana_core_copilot.application.orchestrator.chat.AssetExtractionService")
@patch("luana_core_copilot.application.orchestrator.chat.AssetRepository")
def test_small_document_is_inlined(
    mock_repo_cls: MagicMock,
    mock_extract_cls: MagicMock,
) -> None:
    """A document with short extracted text is included verbatim."""
    text = "Este es el brief corto de la marca. Contenido relevante."
    asset = _mock_asset(
        extracted_text=text,
        extracted_summary="Brief corto.",
        extraction_status="extracted",
    )
    mock_repo_cls.return_value.get_by_id.return_value = asset
    mock_extract_cls.return_value.ensure_extracted.return_value = asset

    tenant_id = uuid.uuid4()
    block = {"type": "document", "asset_id": str(asset.id), "filename": "brief.pdf"}

    rendered = _render_attachment_context([block], tenant_id=tenant_id, db=MagicMock())

    assert text in rendered
    assert str(asset.id) in rendered  # ensures the tool can locate it


@patch("luana_core_copilot.application.orchestrator.chat.AssetExtractionService")
@patch("luana_core_copilot.application.orchestrator.chat.AssetRepository")
def test_large_document_is_hinted_not_inlined(
    mock_repo_cls: MagicMock,
    mock_extract_cls: MagicMock,
) -> None:
    """A document above the inline threshold emits a hint with summary + asset_id."""
    big_text = "Contenido muy largo. " * 500  # well above threshold
    summary = "Brief de marca para Alpaca Púrpura — identidad, tono, personas."
    asset = _mock_asset(
        extracted_text=big_text,
        extracted_summary=summary,
        extraction_status="extracted",
    )
    mock_repo_cls.return_value.get_by_id.return_value = asset
    mock_extract_cls.return_value.ensure_extracted.return_value = asset

    block = {"type": "document", "asset_id": str(asset.id), "filename": "brief.pdf"}
    rendered = _render_attachment_context([block], tenant_id=uuid.uuid4(), db=MagicMock())

    assert big_text not in rendered  # not inlined
    assert summary in rendered  # hinted
    assert str(asset.id) in rendered
    assert "read_document" in rendered.lower()  # tool guidance present
    assert len(rendered) < len(big_text) / 2


@patch("luana_core_copilot.application.orchestrator.chat.AssetExtractionService")
@patch("luana_core_copilot.application.orchestrator.chat.AssetRepository")
def test_pending_extraction_emits_hint_and_triggers_extraction(
    mock_repo_cls: MagicMock,
    mock_extract_cls: MagicMock,
) -> None:
    """If extraction hasn't run yet, orchestrator still returns a usable hint."""
    pending = _mock_asset()  # pending, no text
    extracted = _mock_asset(
        extracted_text="Texto recién parseado.",
        extracted_summary="Recién parseado.",
        extraction_status="extracted",
    )
    mock_repo_cls.return_value.get_by_id.return_value = pending
    mock_extract_cls.return_value.ensure_extracted.return_value = extracted

    block = {"type": "document", "asset_id": str(pending.id), "filename": "x.pdf"}
    rendered = _render_attachment_context([block], tenant_id=uuid.uuid4(), db=MagicMock())

    mock_extract_cls.return_value.ensure_extracted.assert_called_once()
    assert "Texto recién parseado." in rendered or "read_document" in rendered.lower()


@patch("luana_core_copilot.application.orchestrator.chat.AssetExtractionService")
@patch("luana_core_copilot.application.orchestrator.chat.AssetRepository")
def test_missing_asset_returns_empty(
    mock_repo_cls: MagicMock,
    mock_extract_cls: MagicMock,
) -> None:
    """Unknown asset_id → empty context, not exception."""
    mock_repo_cls.return_value.get_by_id.return_value = None

    block = {"type": "document", "asset_id": str(uuid.uuid4()), "filename": "x.pdf"}
    rendered = _render_attachment_context([block], tenant_id=uuid.uuid4(), db=MagicMock())
    assert rendered == ""


def test_threshold_constant_reasonable() -> None:
    """Threshold must be small enough that inlining isn't wasteful but big
    enough that tiny plain-text notes still avoid an extra tool call."""
    assert 500 <= INLINE_DOCUMENT_THRESHOLD <= 4000
