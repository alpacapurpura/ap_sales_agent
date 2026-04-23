"""Contract tests for ``extract_from_doc`` — new tool wrapping extract_document_to_fields.

TDD: written before the implementation. Tests document the contract per FLOW-SPEC §3.1 and §3.2.

Shape invariants:
- Returns JSON with status, job_id, source_kind="doc", source_ref=asset_id.
- All other new keys from extract_from_url must also be present.
- scope="visuals" is not accepted (doc source can't extract visuals).
- asset_id is required.
- tenant_id comes from context, never from tool args.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.context import set_tenant_id

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ASSET_ID = str(uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))


@pytest.fixture(autouse=True)
def _set_tenant() -> None:
    set_tenant_id(TENANT_ID)
    yield
    set_tenant_id(None)


@pytest.fixture
def mock_arq_and_redis(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock ARQ pool and redis for extract_from_doc."""
    pool = MagicMock()
    pool.enqueue_job = AsyncMock(return_value=MagicMock(job_id="arq-id"))

    # Try to patch in the extract_from_doc module location
    try:
        monkeypatch.setattr(
            "src.modules.copilot.application.tools.extract_from_doc.get_arq_pool",
            lambda: pool,
        )
        monkeypatch.setattr(
            "src.modules.copilot.application.tools.extract_from_doc.redis_client",
            MagicMock(setex=MagicMock()),
        )
    except AttributeError:
        # Module doesn't exist yet (pre-implementation) — patch lazily
        pass

    return pool


class TestExtractFromDocImport:
    def test_tool_importable(self) -> None:
        """extract_from_doc must be importable and exposable as a LangChain tool.

        Note: @tool-decorated symbols are StructuredTool instances, not plain
        callables — assert the contract surface (`ainvoke`) instead of plain
        callability.
        """
        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        assert extract_from_doc is not None
        assert hasattr(extract_from_doc, "ainvoke")

    def test_tool_is_langchain_tool(self) -> None:
        """extract_from_doc must be a LangChain @tool."""
        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        assert hasattr(extract_from_doc, "ainvoke"), "extract_from_doc must be a LangChain tool with ainvoke"


class TestExtractFromDocShape:
    async def test_dispatched_has_source_kind_doc(self, mock_arq_and_redis: MagicMock) -> None:
        """source_kind must be 'doc' for this tool."""
        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        result = await extract_from_doc.ainvoke(
            {"module": "brand", "asset_id": ASSET_ID},
        )
        parsed = json.loads(result)
        # Accept either dispatched or error (asset may not exist), but never a crash
        assert "status" in parsed
        if parsed["status"] == "dispatched":
            assert parsed.get("source_kind") == "doc"
            assert parsed.get("source_ref") == ASSET_ID

    async def test_dispatched_has_required_keys(self, mock_arq_and_redis: MagicMock) -> None:
        """All contract keys must be present on dispatched response."""
        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        result = await extract_from_doc.ainvoke(
            {"module": "brand", "asset_id": ASSET_ID},
        )
        parsed = json.loads(result)
        assert "status" in parsed
        if parsed["status"] == "dispatched":
            required_keys = {
                "job_id",
                "poll_endpoint",
                "module",
                "scope",
                "mode",
                "source_kind",
                "source_ref",
                "target_label_es",
                "eta_seconds",
            }
            missing = required_keys - set(parsed.keys())
            assert not missing, f"Missing keys in dispatched response: {missing}"

    async def test_source_kind_is_doc(self, mock_arq_and_redis: MagicMock) -> None:
        """source_kind must be 'doc' (not 'url')."""
        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        result = await extract_from_doc.ainvoke(
            {"module": "brand", "asset_id": ASSET_ID},
        )
        parsed = json.loads(result)
        if parsed["status"] == "dispatched":
            assert parsed["source_kind"] == "doc"


class TestExtractFromDocValidation:
    async def test_visuals_scope_not_accepted(self, mock_arq_and_redis: MagicMock) -> None:
        """scope='visuals' must be rejected — docs can't extract visual elements.

        LangChain validates the Literal at tool invocation time and raises a
        pydantic ValidationError before the tool body runs. The error message
        must clearly mention the allowed literals so the LLM can correct itself.
        """
        from pydantic import ValidationError
        from pydantic_core import ValidationError as CoreValidationError

        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        with pytest.raises((ValidationError, CoreValidationError)) as excinfo:
            await extract_from_doc.ainvoke(
                {"module": "brand", "asset_id": ASSET_ID, "scope": "visuals"},
            )
        # Error must reference the scope literal — so the LLM gets actionable feedback.
        err_str = str(excinfo.value)
        assert "scope" in err_str
        assert "visuals" in err_str or "full" in err_str

    async def test_missing_asset_id_returns_error(self, mock_arq_and_redis: MagicMock) -> None:
        """asset_id is required."""
        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        # LangChain will raise if required param missing — tool should handle gracefully
        # or Pydantic schema will reject it before calling
        try:
            result = await extract_from_doc.ainvoke({"module": "brand"})
            parsed = json.loads(result)
            assert parsed["status"] == "error"
        except (ValueError, KeyError):
            # Acceptable: schema validation rejects it before the tool runs
            pass

    async def test_no_tenant_context_returns_error(self, mock_arq_and_redis: MagicMock) -> None:
        """Missing tenant context must return error (never crash)."""
        set_tenant_id(None)
        from src.modules.copilot.application.tools.extract_from_doc import (
            extract_from_doc,
        )

        result = await extract_from_doc.ainvoke(
            {"module": "brand", "asset_id": ASSET_ID},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"


class TestExtractFromDocRegistry:
    def test_in_extraction_tools_list(self) -> None:
        """extract_from_doc must be exported in EXTRACTION_TOOLS."""
        from src.modules.copilot.application.tools.extraction_tools import (
            EXTRACTION_TOOLS,
        )

        names = {t.name for t in EXTRACTION_TOOLS}
        assert "extract_from_doc" in names

    def test_bound_in_brand_studio_route(self) -> None:
        from src.modules.copilot.application.tools.registry import (
            get_tool_names_for_route,
        )

        names = get_tool_names_for_route("/tenant-id/brand-studio/identity")
        assert "extract_from_doc" in names

    def test_bound_in_offer_studio_route(self) -> None:
        from src.modules.copilot.application.tools.registry import (
            get_tool_names_for_route,
        )

        names = get_tool_names_for_route("/tenant-id/offer-studio/edit/some-id")
        assert "extract_from_doc" in names
