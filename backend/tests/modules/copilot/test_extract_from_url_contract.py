"""Contract tests for ``extract_from_url`` — backwards-compat + new shape.

TDD: these tests are written before the implementation changes.
They document the expected contract per FLOW-SPEC §3.1 and §3.2.

Backwards-compat invariants:
- Old call (only module + url) still returns dispatched.
- Old call with offer_id still works (aliased to entity_id internally).

New invariants:
- Return JSON includes: target_label_es, source_kind, source_ref, eta_seconds.
- scope="section" without section param returns error.
- scope="visuals" on module="offer" returns error (pre-existing).
- scope="field" without field param returns error.
- module="asset" and module="persona" are accepted (new literals).
- mode="suggest" is accepted (new literal).
- entity_id is the primary param; offer_id is deprecated alias.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from luana_core_platform.core.context import set_tenant_id
from luana_core_copilot.application.tools.extraction_tools import (
    EXTRACTION_TOOLS,
    extract_from_url,
)

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OFFER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture(autouse=True)
def _set_tenant() -> None:
    set_tenant_id(TENANT_ID)
    yield
    set_tenant_id(None)


@pytest.fixture
def mock_arq_pool(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the process-wide ARQ pool with a mock that captures enqueues."""
    pool = MagicMock()
    pool.enqueue_job = AsyncMock(return_value=MagicMock(job_id="arq-id"))
    monkeypatch.setattr(
        "luana_core_copilot.application.tools.extraction_tools.get_arq_pool",
        lambda: pool,
    )
    monkeypatch.setattr(
        "luana_core_copilot.application.tools.extraction_tools.redis_client",
        MagicMock(setex=MagicMock()),
    )
    return pool


class TestBackwardsCompat:
    """Old callers must keep working unchanged."""

    async def test_old_brand_call_still_dispatches(self, mock_arq_pool: MagicMock) -> None:
        """Minimal old-style call: module + url only."""
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://visionarias.lat"},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        assert parsed["module"] == "brand"
        assert "job_id" in parsed
        assert "poll_endpoint" in parsed
        mock_arq_pool.enqueue_job.assert_awaited_once()

    async def test_offer_id_deprecated_alias_still_works(self, mock_arq_pool: MagicMock) -> None:
        """Passing offer_id (old param) must still dispatch correctly."""
        result = await extract_from_url.ainvoke(
            {
                "module": "offer",
                "url": "https://visionarias.lat/oferta",
                "offer_id": str(OFFER_ID),
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched", f"Expected dispatched, got: {parsed}"
        call_args = mock_arq_pool.enqueue_job.await_args
        assert call_args.args[0] == "run_offer_extraction"

    async def test_old_scope_full_mode_initial_still_works(self, mock_arq_pool: MagicMock) -> None:
        """scope=full + mode=initial (old defaults) keep working."""
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://example.com",
                "scope": "full",
                "mode": "initial",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        assert parsed["scope"] == "full"
        assert parsed["mode"] == "initial"

    async def test_old_scope_visuals_brand_still_works(self, mock_arq_pool: MagicMock) -> None:
        """scope=visuals for brand (old usage) still dispatches."""
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com", "scope": "visuals"},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"


class TestNewReturnShape:
    """New keys required by FLOW-SPEC §3.2."""

    async def test_dispatched_response_has_target_label_es(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com"},
        )
        parsed = json.loads(result)
        assert "target_label_es" in parsed, f"Missing target_label_es in {parsed}"
        assert isinstance(parsed["target_label_es"], str)
        assert len(parsed["target_label_es"]) > 0

    async def test_dispatched_response_has_source_kind_url(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com"},
        )
        parsed = json.loads(result)
        assert parsed.get("source_kind") == "url"

    async def test_dispatched_response_has_source_ref(self, mock_arq_pool: MagicMock) -> None:
        url = "https://example.com"
        result = await extract_from_url.ainvoke({"module": "brand", "url": url})
        parsed = json.loads(result)
        assert parsed.get("source_ref") == url

    async def test_dispatched_response_has_eta_seconds(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com"},
        )
        parsed = json.loads(result)
        assert "eta_seconds" in parsed
        assert isinstance(parsed["eta_seconds"], int)
        assert parsed["eta_seconds"] > 0

    async def test_message_field_kept_for_backwards_compat(self, mock_arq_pool: MagicMock) -> None:
        """The 'message' field must still be present for existing consumers."""
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com"},
        )
        parsed = json.loads(result)
        assert "message" in parsed

    async def test_section_returned_when_provided(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://example.com",
                "scope": "section",
                "section": "identity",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        assert parsed.get("section") == "identity"

    async def test_target_label_es_for_section_scope(self, mock_arq_pool: MagicMock) -> None:
        """When scope=section, target_label_es reflects the section."""
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://example.com",
                "scope": "section",
                "section": "identity",
            },
        )
        parsed = json.loads(result)
        assert "target_label_es" in parsed
        # Should mention the section in the label
        label = parsed["target_label_es"]
        assert "identidad" in label.lower() or "identity" in label.lower() or "brand" in label.lower()


class TestNewLiterals:
    """New parameter literals accepted per FLOW-SPEC §3.1."""

    async def test_module_asset_accepted(self, mock_arq_pool: MagicMock) -> None:
        """module='asset' is now a valid literal."""
        result = await extract_from_url.ainvoke(
            {"module": "asset", "url": "https://example.com"},
        )
        parsed = json.loads(result)
        # The Literal must accept "asset" at validation time. Implementation may
        # return a friendly "not yet supported" error until an asset worker exists,
        # but it must NOT be a Literal-validation error.
        assert parsed["status"] in ("dispatched", "error")
        if parsed["status"] == "error":
            # Not a "unknown literal" error — friendly message mentioning it's
            # pending is fine.
            msg = parsed.get("message", "").lower()
            assert "literal" not in msg
            assert "invalid" not in msg

    async def test_module_persona_accepted(self, mock_arq_pool: MagicMock) -> None:
        """module='persona' is now a valid literal."""
        result = await extract_from_url.ainvoke(
            {"module": "persona", "url": "https://example.com"},
        )
        parsed = json.loads(result)
        assert parsed["status"] in ("dispatched", "error")

    async def test_mode_suggest_accepted(self, mock_arq_pool: MagicMock) -> None:
        """mode='suggest' is now a valid literal for brand."""
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com", "mode": "suggest"},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        assert parsed["mode"] == "suggest"

    async def test_scope_section_accepted_with_section_param(self, mock_arq_pool: MagicMock) -> None:
        """scope='section' with section param provided is valid."""
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://example.com",
                "scope": "section",
                "section": "strategy",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"

    async def test_scope_field_accepted_with_field_param(self, mock_arq_pool: MagicMock) -> None:
        """scope='field' with field param provided is valid."""
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://example.com",
                "scope": "field",
                "field": "identity.brand_name",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"

    async def test_entity_id_used_for_offer(self, mock_arq_pool: MagicMock) -> None:
        """entity_id is the new primary param for offer (offer_id is deprecated alias)."""
        result = await extract_from_url.ainvoke(
            {
                "module": "offer",
                "url": "https://example.com/oferta",
                "entity_id": str(OFFER_ID),
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        call_args = mock_arq_pool.enqueue_job.await_args
        assert call_args.args[0] == "run_offer_extraction"


class TestValidationErrors:
    """Validation edge cases — error shape preserved."""

    async def test_scope_section_without_section_param_is_error(self, mock_arq_pool: MagicMock) -> None:
        """scope='section' without section= returns error, not a crash."""
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com", "scope": "section"},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert "section" in parsed["message"].lower()
        mock_arq_pool.enqueue_job.assert_not_awaited()

    async def test_scope_field_without_field_param_is_error(self, mock_arq_pool: MagicMock) -> None:
        """scope='field' without field= returns error."""
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "https://example.com", "scope": "field"},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        mock_arq_pool.enqueue_job.assert_not_awaited()

    async def test_offer_module_without_entity_or_offer_id_fails(self, mock_arq_pool: MagicMock) -> None:
        """offer module still requires an entity identifier."""
        result = await extract_from_url.ainvoke(
            {"module": "offer", "url": "https://example.com/oferta"},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        mock_arq_pool.enqueue_job.assert_not_awaited()

    async def test_visuals_scope_rejected_for_offer(self, mock_arq_pool: MagicMock) -> None:
        """scope='visuals' is invalid for offer module (pre-existing rule)."""
        result = await extract_from_url.ainvoke(
            {
                "module": "offer",
                "url": "https://example.com/oferta",
                "scope": "visuals",
                "offer_id": str(OFFER_ID),
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        mock_arq_pool.enqueue_job.assert_not_awaited()

    async def test_invalid_url_still_rejected(self, mock_arq_pool: MagicMock) -> None:
        """URL validation is unchanged."""
        result = await extract_from_url.ainvoke(
            {"module": "brand", "url": "not-a-url"},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        mock_arq_pool.enqueue_job.assert_not_awaited()


class TestToolRegistration:
    def test_extraction_tools_list_unchanged(self) -> None:
        """extract_from_url is still in EXTRACTION_TOOLS."""
        names = {t.name for t in EXTRACTION_TOOLS}
        assert "extract_from_url" in names

    def test_extract_from_doc_added_to_extraction_tools(self) -> None:
        """extract_from_doc must be in EXTRACTION_TOOLS after implementation."""
        names = {t.name for t in EXTRACTION_TOOLS}
        assert "extract_from_doc" in names, "extract_from_doc must be registered in EXTRACTION_TOOLS"

    def test_both_tools_in_registry_extraction_group(self) -> None:
        from luana_core_copilot.application.tools.registry import TOOL_GROUPS

        names = {t.name for t in TOOL_GROUPS["extraction"]}
        assert "extract_from_url" in names
        assert "extract_from_doc" in names
