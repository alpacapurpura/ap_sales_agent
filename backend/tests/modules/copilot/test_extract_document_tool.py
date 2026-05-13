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

from luana_core_copilot.application.services.document_processor import (
    DocumentProcessingResult,
)


class TestExtractDocumentToFields:
    def _patch_tenant(self, tenant_id):
        return patch(
            "luana_core_copilot.application.tools.guided.extract.get_tenant_id",
            return_value=tenant_id,
        )

    def _patch_session(self, asset):
        db_mock = MagicMock()

        def _session_factory():
            return db_mock

        asset_repo_mock = MagicMock()
        asset_repo_mock.get_by_id.return_value = asset

        return patch(
            "luana_core_copilot.application.tools.guided.extract.SessionLocal",
            side_effect=_session_factory,
        ), patch(
            "luana_core_assets.infrastructure.repositories.asset_repository.AssetRepository",
            return_value=asset_repo_mock,
        )

    def test_rejects_unsupported_domain(self) -> None:
        from luana_core_copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        result = extract_document_to_fields.invoke(
            {"asset_id": str(uuid4()), "domain": "not_a_domain"},
        )
        parsed = json.loads(result)
        assert parsed.get("error") == "unsupported_domain"

    def test_rejects_bad_asset_id(self) -> None:
        from luana_core_copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        with self._patch_tenant(uuid4()):
            result = extract_document_to_fields.invoke(
                {"asset_id": "not-a-uuid", "domain": "brand"},
            )
        parsed = json.loads(result)
        assert parsed.get("error") == "bad_asset_id"

    def test_returns_error_when_asset_missing(self) -> None:
        from luana_core_copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        db_mock = MagicMock()
        asset_repo_mock = MagicMock()
        asset_repo_mock.get_by_id.return_value = None

        with (
            self._patch_tenant(uuid4()),
            patch(
                "luana_core_copilot.application.tools.guided.extract.SessionLocal",
                return_value=db_mock,
            ),
            patch(
                "luana_core_assets.infrastructure.repositories.asset_repository.AssetRepository",
                return_value=asset_repo_mock,
            ),
        ):
            result = extract_document_to_fields.invoke(
                {"asset_id": str(uuid4()), "domain": "brand"},
            )
        parsed = json.loads(result)
        assert parsed.get("error") == "asset_not_found"

    def test_returns_error_when_asset_has_no_text(self) -> None:
        from luana_core_copilot.application.tools.guided.extract import (
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
                "luana_core_copilot.application.tools.guided.extract.SessionLocal",
                return_value=db_mock,
            ),
            patch(
                "luana_core_assets.infrastructure.repositories.asset_repository.AssetRepository",
                return_value=asset_repo_mock,
            ),
        ):
            result = extract_document_to_fields.invoke(
                {"asset_id": str(asset.id), "domain": "brand"},
            )
        parsed = json.loads(result)
        assert parsed.get("error") == "asset_not_extracted"

    def test_successful_extraction_returns_delta(self) -> None:
        from luana_core_copilot.application.tools.guided.extract import (
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
                "luana_core_copilot.application.tools.guided.extract.SessionLocal",
                return_value=db_mock,
            ),
            patch(
                "luana_core_assets.infrastructure.repositories.asset_repository.AssetRepository",
                return_value=asset_repo_mock,
            ),
            patch(
                "luana_core_copilot.application.services.document_processor.DocumentProcessor",
                return_value=mock_processor,
            ),
        ):
            result = extract_document_to_fields.invoke(
                {"asset_id": str(asset.id), "domain": "brand"},
            )
        parsed = json.loads(result)
        # Sprint 1: tool emits canonical ``proposal`` ui_action (matches
        # ``propose_field_updates`` shape) so ProposalCard can render +
        # apply via bridge or fallback ``/mutations/apply``. Legacy
        # ``preview_update`` type is purged.
        assert parsed["ui_action"]["type"] == "proposal"
        updates = parsed["ui_action"]["updates"]
        assert isinstance(updates, list)
        assert len(updates) == 2
        by_field = {u["field_id"]: u for u in updates}
        assert by_field["identity.brand_name"]["new_value"] == "Nicolify"
        assert by_field["identity.industry"]["new_value"] == "SaaS"
        for u in updates:
            assert "reason" in u
        # Domain + fields_extracted survive at top-level for FE summary.
        assert parsed["ui_action"]["domain"] == "brand"
        assert parsed["ui_action"]["fields_extracted"] == 2

    def test_new_value_carries_raw_python_shapes(self) -> None:
        """``new_value`` is the raw value end-to-end — no JSON-stringify.

        The bridge / form-runtime / Pydantic apply DTO all accept the raw
        shape (string for text, list of objects for arrays). JSON-coerce
        broke schema validation for every multi-value field — the tool
        now forwards the value verbatim and the FE renderer +
        ``bridge.patchField`` consume it natively.
        """
        from luana_core_copilot.application.tools.guided.extract import (
            extract_document_to_fields,
        )

        asset = SimpleNamespace(
            id=uuid4(),
            filename="brief.pdf",
            extracted_text="...",
        )
        db_mock = MagicMock()
        asset_repo_mock = MagicMock()
        asset_repo_mock.get_by_id.return_value = asset

        mock_processor = MagicMock()
        mock_processor.extract_from_text.return_value = DocumentProcessingResult(
            delta={
                "audience.pain_points": [
                    {"description": "Dolor 1", "severity": 5},
                    {"description": "Dolor 2", "severity": 4},
                ],
                "audience.desires": ["deseo 1", "deseo 2"],
                "identity.brand_name": "Nicolify",
            },
            summary="3 campos",
            source_documents=["brief.pdf"],
            fields_extracted=3,
            fields_skipped=0,
        )

        with (
            self._patch_tenant(uuid4()),
            patch(
                "luana_core_copilot.application.tools.guided.extract.SessionLocal",
                return_value=db_mock,
            ),
            patch(
                "luana_core_assets.infrastructure.repositories.asset_repository.AssetRepository",
                return_value=asset_repo_mock,
            ),
            patch(
                "luana_core_copilot.application.services.document_processor.DocumentProcessor",
                return_value=mock_processor,
            ),
        ):
            result = extract_document_to_fields.invoke(
                {"asset_id": str(asset.id), "domain": "brand"},
            )
        parsed = json.loads(result)
        updates = parsed["ui_action"]["updates"]
        by_field = {u["field_id"]: u["new_value"] for u in updates}
        assert by_field["identity.brand_name"] == "Nicolify"
        assert by_field["audience.desires"] == ["deseo 1", "deseo 2"]
        assert by_field["audience.pain_points"] == [
            {"description": "Dolor 1", "severity": 5},
            {"description": "Dolor 2", "severity": 4},
        ]
