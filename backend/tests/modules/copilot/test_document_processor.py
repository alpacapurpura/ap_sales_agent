"""Tests for DocumentProcessor service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.copilot.application.services.document_processor import (
    DocumentProcessingResult,
    DocumentProcessor,
)


class TestDocumentProcessingResult:
    def test_structure(self):
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

    def test_empty_result(self):
        result = DocumentProcessingResult(
            delta={},
            summary="No data",
            source_documents=[],
            fields_extracted=0,
            fields_skipped=0,
        )
        assert result.delta == {}
        assert result.fields_extracted == 0


class TestDocumentProcessor:
    @pytest.mark.asyncio
    async def test_process_single_document(self):
        mock_file = MagicMock()
        mock_file.filename = "brief.pdf"
        mock_file.content_type = "application/pdf"

        mock_parser = MagicMock()
        mock_parser.parse_file = AsyncMock(
            return_value="Somos una marca de coaching para emprendedoras"
        )

        mock_ai = MagicMock()
        mock_ai.run_structured_action = MagicMock(
            return_value=MagicMock(
                extracted_fields={
                    "identity.brand_name": "CoachPro",
                    "positioning.uvp": "Transforma tu negocio",
                }
            )
        )

        processor = DocumentProcessor(ai_service=mock_ai, file_parser=mock_parser)
        result = await processor.process_for_interview(
            files=[mock_file],
            extraction_template="brand_doc_extraction",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert isinstance(result, DocumentProcessingResult)
        assert result.fields_extracted == 2
        assert result.fields_skipped == 0
        assert "brief.pdf" in result.source_documents
        assert result.delta["identity.brand_name"] == "CoachPro"
        assert result.delta["positioning.uvp"] == "Transforma tu negocio"

    @pytest.mark.asyncio
    async def test_process_skips_existing_non_empty_fields(self):
        mock_file = MagicMock()
        mock_file.filename = "brief.pdf"

        mock_parser = MagicMock()
        mock_parser.parse_file = AsyncMock(return_value="Some content")

        mock_ai = MagicMock()
        mock_ai.run_structured_action = MagicMock(
            return_value=MagicMock(
                extracted_fields={
                    "identity.brand_name": "NewName",
                    "positioning.uvp": "New UVP",
                }
            )
        )

        processor = DocumentProcessor(ai_service=mock_ai, file_parser=mock_parser)
        result = await processor.process_for_interview(
            files=[mock_file],
            extraction_template="brand_doc_extraction",
            existing_mapa={"identity.brand_name": "OldName"},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 1
        assert result.fields_skipped == 1
        # Should NOT include the field that was already set
        assert "identity.brand_name" not in result.delta
        # Should include the new field
        assert result.delta["positioning.uvp"] == "New UVP"

    @pytest.mark.asyncio
    async def test_process_overwrites_empty_existing_fields(self):
        mock_file = MagicMock()
        mock_file.filename = "brief.pdf"

        mock_parser = MagicMock()
        mock_parser.parse_file = AsyncMock(return_value="Some content")

        mock_ai = MagicMock()
        mock_ai.run_structured_action = MagicMock(
            return_value=MagicMock(extracted_fields={"identity.brand_name": "NewName"})
        )

        processor = DocumentProcessor(ai_service=mock_ai, file_parser=mock_parser)
        result = await processor.process_for_interview(
            files=[mock_file],
            extraction_template="brand_doc_extraction",
            existing_mapa={"identity.brand_name": ""},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 1
        assert result.fields_skipped == 0
        assert result.delta["identity.brand_name"] == "NewName"

    @pytest.mark.asyncio
    async def test_process_multiple_documents(self):
        file1 = MagicMock()
        file1.filename = "brief.pdf"
        file2 = MagicMock()
        file2.filename = "values.docx"

        mock_parser = MagicMock()
        mock_parser.parse_file = AsyncMock(
            side_effect=["Content from PDF", "Content from DOCX"]
        )

        mock_ai = MagicMock()
        mock_ai.run_structured_action = MagicMock(
            return_value=MagicMock(
                extracted_fields={
                    "identity.brand_name": "BrandX",
                    "values.core_values": "honestidad, calidad",
                }
            )
        )

        processor = DocumentProcessor(ai_service=mock_ai, file_parser=mock_parser)
        result = await processor.process_for_interview(
            files=[file1, file2],
            extraction_template="brand_doc_extraction",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 2
        assert "brief.pdf" in result.source_documents
        assert "values.docx" in result.source_documents

    @pytest.mark.asyncio
    async def test_process_empty_files(self):
        mock_file = MagicMock()
        mock_file.filename = "empty.pdf"

        mock_parser = MagicMock()
        mock_parser.parse_file = AsyncMock(return_value="")

        mock_ai = MagicMock()

        processor = DocumentProcessor(ai_service=mock_ai, file_parser=mock_parser)
        result = await processor.process_for_interview(
            files=[mock_file],
            extraction_template="brand_doc_extraction",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 0
        assert result.delta == {}
        # AI should NOT be called if no text was extracted
        mock_ai.run_structured_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_with_none_filename(self):
        mock_file = MagicMock()
        mock_file.filename = None

        mock_parser = MagicMock()
        mock_parser.parse_file = AsyncMock(return_value="Some content")

        mock_ai = MagicMock()
        mock_ai.run_structured_action = MagicMock(
            return_value=MagicMock(extracted_fields={"field1": "value1"})
        )

        processor = DocumentProcessor(ai_service=mock_ai, file_parser=mock_parser)
        result = await processor.process_for_interview(
            files=[mock_file],
            extraction_template="brand_doc_extraction",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert "unknown" in result.source_documents

    @pytest.mark.asyncio
    async def test_process_ai_returns_empty(self):
        mock_file = MagicMock()
        mock_file.filename = "brief.pdf"

        mock_parser = MagicMock()
        mock_parser.parse_file = AsyncMock(return_value="Some content")

        mock_ai = MagicMock()
        mock_ai.run_structured_action = MagicMock(
            return_value=MagicMock(extracted_fields={})
        )

        processor = DocumentProcessor(ai_service=mock_ai, file_parser=mock_parser)
        result = await processor.process_for_interview(
            files=[mock_file],
            extraction_template="brand_doc_extraction",
            existing_mapa={},
            tenant_id=uuid4(),
        )

        assert result.fields_extracted == 0
        assert result.delta == {}
