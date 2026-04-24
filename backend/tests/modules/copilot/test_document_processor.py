"""Tests for DocumentProcessor service after the registry-driven refactor.

Coverage:
* DocumentProcessingResult dataclass shape.
* process_files / extract_from_text use the per-domain registry to pick
  template + action_name.
* Existing mapa skip semantics for scalars and structured values.
* Buyer-persona path: heterogeneous (list[dict]) values pass through
  intact since the response model now accepts ``dict[str, Any]``.
* Unsupported domain returns an empty result without invoking the LLM.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.application.services.document_processor import (
    DocumentProcessingResult,
    DocumentProcessor,
)


class TestDocumentProcessingResult:
    def test_structure(self) -> None:
        result = DocumentProcessingResult(
            delta={"field1": "value1"},
            summary="Extracted 1 field from 1 document",
            source_documents=["test.pdf"],
            fields_extracted=1,
            fields_skipped=0,
        )
        assert result.delta == {"field1": "value1"}
        assert result.fields_extracted == 1
        assert result.fields_skipped == 0
        assert result.source_documents == ["test.pdf"]
        assert "Extracted 1 field" in result.summary

    def test_empty_result(self) -> None:
        result = DocumentProcessingResult(
            delta={},
            summary="No data",
            source_documents=[],
            fields_extracted=0,
            fields_skipped=0,
        )
        assert result.delta == {}
        assert result.fields_extracted == 0


def _make_file(filename: str | None = "doc.pdf") -> MagicMock:
    f = MagicMock()
    f.filename = filename
    return f


def _make_parser(text: str) -> MagicMock:
    parser = MagicMock()
    parser.parse_file = AsyncMock(return_value=text)
    return parser


def _make_ai(extracted: dict) -> MagicMock:
    ai = MagicMock()
    ai.run_structured_action = MagicMock(
        return_value=MagicMock(extracted_fields=extracted),
    )
    return ai


@pytest.fixture(autouse=True)
def _stub_prompt_loader():
    """Stub prompt_loader.render so tests don't need real Jinja templates on disk."""
    with patch("src.modules.copilot.application.services.document_processor.prompt_loader") as loader:
        loader.render.return_value = "rendered prompt"
        yield loader


class TestDocumentProcessor:
    @pytest.mark.asyncio
    async def test_brand_extraction_uses_per_domain_action_name(self) -> None:
        ai = _make_ai({"identity.brand_name": "CoachPro", "positioning.uvp": "X"})
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser("Brand brief content"),
        )
        result = await processor.process_files(
            files=[_make_file("brief.pdf")],
            domain="brand",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert isinstance(result, DocumentProcessingResult)
        assert result.fields_extracted == 2
        assert result.delta["identity.brand_name"] == "CoachPro"

        call_kwargs = ai.run_structured_action.call_args.kwargs
        assert call_kwargs["action_name"] == "brand_doc_extraction"

    @pytest.mark.asyncio
    async def test_skips_existing_non_empty_fields(self) -> None:
        ai = _make_ai({"identity.brand_name": "NewName", "positioning.uvp": "New UVP"})
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser("content"),
        )
        result = await processor.process_files(
            files=[_make_file()],
            domain="brand",
            existing_mapa={"identity.brand_name": "OldName"},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 1
        assert result.fields_skipped == 1
        assert "identity.brand_name" not in result.delta
        assert result.delta["positioning.uvp"] == "New UVP"

    @pytest.mark.asyncio
    async def test_overwrites_empty_existing_fields(self) -> None:
        ai = _make_ai({"identity.brand_name": "NewName"})
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser("content"),
        )
        result = await processor.process_files(
            files=[_make_file()],
            domain="brand",
            existing_mapa={"identity.brand_name": ""},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 1
        assert result.fields_skipped == 0
        assert result.delta["identity.brand_name"] == "NewName"

    @pytest.mark.asyncio
    async def test_buyer_persona_accepts_list_of_dict_values(self) -> None:
        """Regression: dict[str, str]-only response model rejected list values
        and surfaced as ``extraction_failed``. Now ``dict[str, Any]`` lets
        pain_points / desires through intact for the persister to validate.
        """
        pain_points = [
            {"description": "Trabajo solo, sin estructura.", "severity": 4},
            {"description": "Improviso demasiado.", "severity": 3},
        ]
        ai = _make_ai(
            {
                "name": "Avatar Coach",
                "demographics.age_range": "30-40",
                "pain_points": pain_points,
            }
        )
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser("Avatar profile"),
        )
        result = await processor.process_files(
            files=[_make_file("avatar.pdf")],
            domain="buyer_persona",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 3
        assert result.delta["pain_points"] == pain_points
        call_kwargs = ai.run_structured_action.call_args.kwargs
        assert call_kwargs["action_name"] == "buyer_persona_doc_extraction"

    @pytest.mark.asyncio
    async def test_unsupported_domain_returns_empty_without_calling_ai(self) -> None:
        ai = MagicMock()
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser("anything"),
        )
        result = await processor.process_files(
            files=[_make_file()],
            domain="not_a_domain",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 0
        assert result.delta == {}
        ai.run_structured_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_files_skip_ai(self) -> None:
        ai = MagicMock()
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser(""),
        )
        result = await processor.process_files(
            files=[_make_file("empty.pdf")],
            domain="brand",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 0
        assert result.delta == {}
        ai.run_structured_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_filename_falls_back_to_unknown(self) -> None:
        ai = _make_ai({"field1": "value1"})
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser("content"),
        )
        result = await processor.process_files(
            files=[_make_file(filename=None)],
            domain="brand",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert "unknown" in result.source_documents

    @pytest.mark.asyncio
    async def test_ai_returns_empty_dict(self) -> None:
        ai = _make_ai({})
        processor = DocumentProcessor(
            ai_service=ai,
            file_parser=_make_parser("content"),
        )
        result = await processor.process_files(
            files=[_make_file()],
            domain="brand",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 0
        assert result.delta == {}
