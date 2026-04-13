"""Tests for document upload API endpoint."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.interview import router
from src.modules.copilot.application.services.document_processor import (
    DocumentProcessingResult,
)
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id=None):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/interview")
    tenant_id = tenant_id or uuid4()
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id
    )
    return TestClient(app), tenant_id


class TestProcessDocuments:
    @patch("src.modules.copilot.api.interview.DocumentProcessor")
    @patch("src.modules.copilot.api.interview.InterviewService")
    def test_process_documents_success(self, mock_service_cls, mock_processor_cls):
        session_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_session.return_value = MagicMock(
            id=session_id,
            domain="brand",
            mapa_global={},
            config_snapshot={
                "document_extraction_template": "brand_doc_extraction",
            },
        )
        mock_service.update_mapa_global = MagicMock()
        mock_service_cls.return_value = mock_service

        mock_processor = MagicMock()
        mock_processor.process_for_interview = AsyncMock(
            return_value=DocumentProcessingResult(
                delta={"identity.brand_name": "TestBrand"},
                summary="Extraídos 1 campos de 1 documento(s).",
                source_documents=["test.pdf"],
                fields_extracted=1,
                fields_skipped=0,
            )
        )
        mock_processor_cls.return_value = mock_processor

        client, _ = _build_client()
        response = client.post(
            f"/api/v1/copilot/interview/{session_id}/documents",
            files=[("files", ("test.pdf", b"pdf content", "application/pdf"))],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["fields_extracted"] == 1
        assert "test.pdf" in data["source_documents"]
        assert data["delta"]["identity.brand_name"] == "TestBrand"

    @patch("src.modules.copilot.api.interview.DocumentProcessor")
    @patch("src.modules.copilot.api.interview.InterviewService")
    def test_process_documents_calls_update_mapa(
        self, mock_service_cls, mock_processor_cls
    ):
        session_id = uuid4()
        tenant_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_session.return_value = MagicMock(
            id=session_id,
            domain="brand",
            mapa_global={},
            config_snapshot={
                "document_extraction_template": "brand_doc_extraction",
            },
        )
        mock_service_cls.return_value = mock_service

        delta = {"identity.brand_name": "TestBrand"}
        mock_processor = MagicMock()
        mock_processor.process_for_interview = AsyncMock(
            return_value=DocumentProcessingResult(
                delta=delta,
                summary="Extracted 1 field",
                source_documents=["test.pdf"],
                fields_extracted=1,
                fields_skipped=0,
            )
        )
        mock_processor_cls.return_value = mock_processor

        client, _ = _build_client(tenant_id)
        client.post(
            f"/api/v1/copilot/interview/{session_id}/documents",
            files=[("files", ("test.pdf", b"pdf content", "application/pdf"))],
        )

        mock_service.update_mapa_global.assert_called_once_with(
            session_id=session_id, tenant_id=tenant_id, delta=delta
        )

    @patch("src.modules.copilot.api.interview.DocumentProcessor")
    @patch("src.modules.copilot.api.interview.InterviewService")
    def test_process_documents_empty_delta_no_update(
        self, mock_service_cls, mock_processor_cls
    ):
        session_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_session.return_value = MagicMock(
            id=session_id,
            domain="brand",
            mapa_global={},
            config_snapshot={
                "document_extraction_template": "brand_doc_extraction",
            },
        )
        mock_service_cls.return_value = mock_service

        mock_processor = MagicMock()
        mock_processor.process_for_interview = AsyncMock(
            return_value=DocumentProcessingResult(
                delta={},
                summary="No se pudo extraer texto.",
                source_documents=[],
                fields_extracted=0,
                fields_skipped=0,
            )
        )
        mock_processor_cls.return_value = mock_processor

        client, _ = _build_client()
        response = client.post(
            f"/api/v1/copilot/interview/{session_id}/documents",
            files=[("files", ("empty.pdf", b"", "application/pdf"))],
        )

        assert response.status_code == 200
        mock_service.update_mapa_global.assert_not_called()

    @patch("src.modules.copilot.api.interview.InterviewService")
    def test_process_documents_session_not_found(self, mock_service_cls):
        session_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_session.return_value = None
        mock_service_cls.return_value = mock_service

        client, _ = _build_client()
        response = client.post(
            f"/api/v1/copilot/interview/{session_id}/documents",
            files=[("files", ("test.pdf", b"pdf content", "application/pdf"))],
        )

        assert response.status_code == 404

    @patch("src.modules.copilot.api.interview.InterviewService")
    def test_process_documents_no_template(self, mock_service_cls):
        session_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_session.return_value = MagicMock(
            id=session_id,
            domain="brand",
            mapa_global={},
            config_snapshot={},  # No document_extraction_template
        )
        mock_service_cls.return_value = mock_service

        client, _ = _build_client()
        response = client.post(
            f"/api/v1/copilot/interview/{session_id}/documents",
            files=[("files", ("test.pdf", b"pdf content", "application/pdf"))],
        )

        assert response.status_code == 400
        assert "document processing" in response.json()["detail"].lower()
