"""Tests for the ``extract_document_to_fields`` guided-setup tool.

Replaces the legacy ``POST /api/v1/copilot/interview/{id}/documents`` endpoint.
Instead of a dedicated HTTP endpoint, the copilot invokes this tool whenever
the user uploads a document in any conversation. Docs are read from the
already-extracted ``assets.extracted_text`` column (one-shot extraction at
upload time) so no re-parsing happens on each LLM turn.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.services.document_processor import (
    DocumentProcessingResult,
)


class TestExtractDocumentToFields:
    def _patch_tenant(self, tenant_id):
        return patch(
            "src.modules.copilot.application.tools.guided.extract.get_tenant_id",
            return_value=tenant_id,
        )

    def _patch_session(self, asset):
        db_mock = MagicMock()

        def _session_factory():
            return db_mock

        asset_repo_mock = MagicMock()
        asset_repo_mock.get_by_id.return_value = asset

        return patch(
            "src.modules.copilot.application.tools.guided.extract.SessionLocal",
            side_effect=_session_factory,
        ), patch(
            "src.modules.assets.infrastructure.repositories.asset_repository.AssetRepository",
            return_value=asset_repo_mock,
        )

    def test_rejects_unsupported_domain(self) -> None:
        from src.modules.copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        result = extract_document_to_fields.invoke(
            {"asset_id": str(uuid4()), "domain": "not_a_domain"},
        )
        parsed = json.loads(result)
        assert parsed.get("error") == "unsupported_domain"

    def test_rejects_bad_asset_id(self) -> None:
        from src.modules.copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        with self._patch_tenant(uuid4()):
            result = extract_document_to_fields.invoke(
                {"asset_id": "not-a-uuid", "domain": "brand"},
            )
        parsed = json.loads(result)
        assert parsed.get("error") == "bad_asset_id"

    def test_returns_error_when_asset_missing(self) -> None:
        from src.modules.copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        db_mock = MagicMock()
        asset_repo_mock = MagicMock()
        asset_repo_mock.get_by_id.return_value = None

        with (
            self._patch_tenant(uuid4()),
            patch(
                "src.modules.copilot.application.tools.guided.extract.SessionLocal",
                return_value=db_mock,
            ),
            patch(
                "src.modules.assets.infrastructure.repositories.asset_repository.AssetRepository",
                return_value=asset_repo_mock,
            ),
        ):
            result = extract_document_to_fields.invoke(
                {"asset_id": str(uuid4()), "domain": "brand"},
            )
        parsed = json.loads(result)
        assert parsed.get("error") == "asset_not_found"

    def test_returns_error_when_asset_has_no_text(self) -> None:
        from src.modules.copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        asset = SimpleNamespace(
            id=uuid4(),
            filename="brief.pdf",
            extracted_text="   ",
        )
        db_mock = MagicMock()
        asset_repo_mock = MagicMock()
        asset_repo_mock.get_by_id.return_value = asset

        with (
            self._patch_tenant(uuid4()),
            patch(
                "src.modules.copilot.application.tools.guided.extract.SessionLocal",
                return_value=db_mock,
            ),
            patch(
                "src.modules.assets.infrastructure.repositories.asset_repository.AssetRepository",
                return_value=asset_repo_mock,
            ),
        ):
            result = extract_document_to_fields.invoke(
                {"asset_id": str(asset.id), "domain": "brand"},
            )
        parsed = json.loads(result)
        assert parsed.get("error") == "asset_not_extracted"

    def test_successful_extraction_returns_delta(self) -> None:
        from src.modules.copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        asset = SimpleNamespace(
            id=uuid4(),
            filename="brief.pdf",
            extracted_text="Brand name: Nicolify\nIndustry: SaaS\n",
        )
        db_mock = MagicMock()
        asset_repo_mock = MagicMock()
        asset_repo_mock.get_by_id.return_value = asset

        mock_processor = MagicMock()
        mock_processor.extract_from_text.return_value = DocumentProcessingResult(
            delta={"identity.brand_name": "Nicolify", "identity.industry": "SaaS"},
            summary="Extraídos 2 campos de 1 documento(s).",
            source_documents=["brief.pdf"],
            fields_extracted=2,
            fields_skipped=0,
        )

        with (
            self._patch_tenant(uuid4()),
            patch(
                "src.modules.copilot.application.tools.guided.extract.SessionLocal",
                return_value=db_mock,
            ),
            patch(
                "src.modules.assets.infrastructure.repositories.asset_repository.AssetRepository",
                return_value=asset_repo_mock,
            ),
            patch(
                "src.modules.copilot.application.services.document_processor.DocumentProcessor",
                return_value=mock_processor,
            ),
        ):
            result = extract_document_to_fields.invoke(
                {"asset_id": str(asset.id), "domain": "brand"},
            )
        parsed = json.loads(result)
        assert parsed["ui_action"]["type"] == "preview_update"
        assert parsed["ui_action"]["domain"] == "brand"
        assert parsed["ui_action"]["fields_extracted"] == 2
        assert parsed["ui_action"]["delta"]["identity.brand_name"] == "Nicolify"
