"""Tests for the conversational ``extract_from_url`` tool.

The tool is the single entry point for brand+offer extraction triggered from
chat. Previously the wizards owned this flow; now the LLM can call this tool
directly when the user says e.g. "extrae todo de https://example.com al brand
studio". It delegates to the existing ARQ workers (``run_brand_extraction``
and ``run_offer_extraction``) — no new extraction infrastructure is added,
only a tool-facing contract.

Tenant isolation: the tool MUST read ``tenant_id`` from the request-scoped
context (``src.core.context.get_tenant_id``). Passing it as a tool argument
would let the LLM fabricate one and leak across tenants.
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


class TestExtractFromUrlBrand:
    async def test_dispatches_full_initial_extraction(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://visionarias.lat",
                "scope": "full",
                "mode": "initial",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        assert parsed["module"] == "brand"
        assert parsed["scope"] == "full"
        assert parsed["mode"] == "initial"
        assert "job_id" in parsed
        assert parsed["poll_endpoint"].endswith(parsed["job_id"])

        mock_arq_pool.enqueue_job.assert_awaited_once()
        call_args = mock_arq_pool.enqueue_job.await_args
        assert call_args.args[0] == "run_brand_extraction"
        assert call_args.kwargs["tenant_id"] == str(TENANT_ID)
        assert call_args.kwargs["url"] == "https://visionarias.lat"
        assert call_args.kwargs["mode"] == "initial"

    async def test_dispatches_update_with_instructions(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://visionarias.lat",
                "scope": "full",
                "mode": "update",
                "update_instructions": "Solo completa los campos vacíos.",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        assert parsed["mode"] == "update"
        call_kwargs = mock_arq_pool.enqueue_job.await_args.kwargs
        assert call_kwargs["update_instructions"] == "Solo completa los campos vacíos."

    async def test_visuals_scope_is_brand_only_ok(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://visionarias.lat",
                "scope": "visuals",
                "mode": "initial",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        assert parsed["scope"] == "visuals"
        call_kwargs = mock_arq_pool.enqueue_job.await_args.kwargs
        # visuals scope maps to include_visuals=True on the brand worker
        assert call_kwargs.get("include_visuals") is True


class TestExtractFromUrlOffer:
    async def test_requires_offer_id(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "offer",
                "url": "https://visionarias.lat/oferta",
                "scope": "full",
                "mode": "initial",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert "offer_id" in parsed["message"].lower()
        mock_arq_pool.enqueue_job.assert_not_awaited()

    async def test_dispatches_offer_extraction(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "offer",
                "url": "https://visionarias.lat/oferta",
                "scope": "full",
                "mode": "update",
                "offer_id": str(OFFER_ID),
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "dispatched"
        call_args = mock_arq_pool.enqueue_job.await_args
        assert call_args.args[0] == "run_offer_extraction"
        assert call_args.kwargs["offer_id"] == str(OFFER_ID)
        assert call_args.kwargs["mode"] == "update"

    async def test_visuals_scope_rejected_for_offer(self, mock_arq_pool: MagicMock) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "offer",
                "url": "https://visionarias.lat/oferta",
                "scope": "visuals",
                "mode": "initial",
                "offer_id": str(OFFER_ID),
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        mock_arq_pool.enqueue_job.assert_not_awaited()


class TestValidation:
    async def test_missing_tenant_context_fails(self, mock_arq_pool: MagicMock) -> None:
        set_tenant_id(None)
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://visionarias.lat",
                "scope": "full",
                "mode": "initial",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        mock_arq_pool.enqueue_job.assert_not_awaited()

    async def test_missing_arq_pool_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "luana_core_copilot.application.tools.extraction_tools.get_arq_pool",
            lambda: None,
        )
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": "https://visionarias.lat",
                "scope": "full",
                "mode": "initial",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"

    @pytest.mark.parametrize("bad_url", ["", "  ", "not-a-url", "ftp://foo"])
    async def test_rejects_invalid_url(self, mock_arq_pool: MagicMock, bad_url: str) -> None:
        result = await extract_from_url.ainvoke(
            {
                "module": "brand",
                "url": bad_url,
                "scope": "full",
                "mode": "initial",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        mock_arq_pool.enqueue_job.assert_not_awaited()


class TestToolRegistration:
    def test_extraction_tools_group_exports_extract_from_url(self) -> None:
        names = {t.name for t in EXTRACTION_TOOLS}
        assert "extract_from_url" in names

    def test_registry_exposes_extraction_group(self) -> None:
        from luana_core_copilot.application.tools.registry import TOOL_GROUPS

        assert "extraction" in TOOL_GROUPS
        names = {t.name for t in TOOL_GROUPS["extraction"]}
        assert "extract_from_url" in names

    @pytest.mark.parametrize(
        "route",
        [
            "/tenant-id/brand-studio/identity",
            "/tenant-id/offer-studio/edit/offer-id",
        ],
    )
    def test_bound_in_brand_and_offer_studio(self, route: str) -> None:
        from luana_core_copilot.application.tools.registry import (
            get_tool_names_for_route,
        )

        names = get_tool_names_for_route(route)
        assert "extract_from_url" in names
