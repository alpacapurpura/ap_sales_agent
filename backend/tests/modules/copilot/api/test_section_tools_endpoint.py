"""Tests for POST /copilot/offer-section-tools/{tool_key} endpoint.

Architecture:
- Builds a minimal FastAPI test app with the section_tools router.
- Mocks SessionLocal, get_tenant_id, and individual tool invocations so no DB
  is touched.
- Verifies response contract, tenant isolation, 404 on unknown tool, and 422 on
  missing required fields.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.section_tools import router
from src.modules.iam.api.dependencies import get_current_user

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()

SAMPLE_TOOL_RESPONSE = json.dumps(
    {
        "section_slug": "identity",
        "draft_fields": {"public_name": "Acme"},
        "suggestions": ["Nombre extraído de la identidad de marca."],
        "confidence": 0.85,
        "citations": ["brand:identity"],
    }
)


def _build_client(tenant_id=None) -> TestClient:
    """Build a TestClient with dependency overrides for DB and auth."""
    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/copilot/offer-section-tools")

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id or TENANT_ID,
    )
    return TestClient(app)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_invoke_valid_tool_returns_200_with_dto():
    """POST with a known tool_key should return 200 + matching OfferSectionToolResult."""
    client = _build_client()

    with (
        patch(
            "src.modules.copilot.api.section_tools.set_tenant_id",
        ),
        patch(
            "src.modules.copilot.api.section_tools._TOOLS_BY_NAME",
            {"adapt_from_brand_identity": MagicMock(invoke=MagicMock(return_value=SAMPLE_TOOL_RESPONSE))},
        ),
    ):
        response = client.post(
            "/api/v1/copilot/offer-section-tools/adapt_from_brand_identity",
            json={"offer_id": str(uuid4()), "section_slug": "identity"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["section_slug"] == "identity"
    assert body["draft_fields"] == {"public_name": "Acme"}
    assert isinstance(body["suggestions"], list)
    assert isinstance(body["confidence"], float)
    assert isinstance(body["citations"], list)


def test_invoke_tool_with_tool_args_passes_args():
    """tool_args from request body must be forwarded to the tool's invoke()."""
    client = _build_client()

    mock_tool = MagicMock(invoke=MagicMock(return_value=SAMPLE_TOOL_RESPONSE))

    with (
        patch(
            "src.modules.copilot.api.section_tools.set_tenant_id",
        ),
        patch(
            "src.modules.copilot.api.section_tools._TOOLS_BY_NAME",
            {"adapt_from_brand_identity": mock_tool},
        ),
    ):
        response = client.post(
            "/api/v1/copilot/offer-section-tools/adapt_from_brand_identity",
            json={
                "offer_id": str(uuid4()),
                "section_slug": "identity",
                "tool_args": {"custom_key": "custom_val"},
            },
        )

    assert response.status_code == 200
    mock_tool.invoke.assert_called_once_with({"custom_key": "custom_val"})


# ---------------------------------------------------------------------------
# 404 for unknown tool_key
# ---------------------------------------------------------------------------


def test_unknown_tool_key_returns_404():
    """POST to an unknown tool_key must return 404."""
    client = _build_client()

    with (
        patch(
            "src.modules.copilot.api.section_tools.set_tenant_id",
        ),
        patch(
            "src.modules.copilot.api.section_tools._TOOLS_BY_NAME",
            {},
        ),
    ):
        response = client.post(
            "/api/v1/copilot/offer-section-tools/this_tool_does_not_exist",
            json={"offer_id": str(uuid4()), "section_slug": "identity"},
        )

    assert response.status_code == 404
    assert "tool_key" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_missing_offer_id_returns_422():
    """Request without offer_id should return 422 (Pydantic validation)."""
    client = _build_client()

    with (
        patch("src.modules.copilot.api.section_tools.set_tenant_id"),
        patch(
            "src.modules.copilot.api.section_tools._TOOLS_BY_NAME",
            {"adapt_from_brand_identity": MagicMock()},
        ),
    ):
        response = client.post(
            "/api/v1/copilot/offer-section-tools/adapt_from_brand_identity",
            json={"section_slug": "identity"},  # offer_id missing
        )

    assert response.status_code == 422


def test_missing_section_slug_returns_422():
    """Request without section_slug should return 422 (Pydantic validation)."""
    client = _build_client()

    with (
        patch("src.modules.copilot.api.section_tools.set_tenant_id"),
        patch(
            "src.modules.copilot.api.section_tools._TOOLS_BY_NAME",
            {"adapt_from_brand_identity": MagicMock()},
        ),
    ):
        response = client.post(
            "/api/v1/copilot/offer-section-tools/adapt_from_brand_identity",
            json={"offer_id": str(uuid4())},  # section_slug missing
        )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tenant context
# ---------------------------------------------------------------------------


def test_tenant_id_injected_from_current_user():
    """set_tenant_id must be called with the tenant_id from the authenticated user."""
    tenant_id = uuid4()
    client = _build_client(tenant_id=tenant_id)

    mock_set_tid = MagicMock()

    with (
        patch(
            "src.modules.copilot.api.section_tools.set_tenant_id",
            mock_set_tid,
        ),
        patch(
            "src.modules.copilot.api.section_tools._TOOLS_BY_NAME",
            {"adapt_from_brand_identity": MagicMock(invoke=MagicMock(return_value=SAMPLE_TOOL_RESPONSE))},
        ),
    ):
        response = client.post(
            "/api/v1/copilot/offer-section-tools/adapt_from_brand_identity",
            json={"offer_id": str(uuid4()), "section_slug": "identity"},
        )

    assert response.status_code == 200
    mock_set_tid.assert_called_once_with(str(tenant_id))


# ---------------------------------------------------------------------------
# Edition code (optional field)
# ---------------------------------------------------------------------------


def test_edition_code_is_optional():
    """edition_code is optional — omitting it must still return 200."""
    client = _build_client()

    with (
        patch("src.modules.copilot.api.section_tools.set_tenant_id"),
        patch(
            "src.modules.copilot.api.section_tools._TOOLS_BY_NAME",
            {"adapt_from_brand_identity": MagicMock(invoke=MagicMock(return_value=SAMPLE_TOOL_RESPONSE))},
        ),
    ):
        response = client.post(
            "/api/v1/copilot/offer-section-tools/adapt_from_brand_identity",
            json={
                "offer_id": str(uuid4()),
                "section_slug": "identity",
                # edition_code omitted intentionally
            },
        )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# All 17 tool keys are discoverable
# ---------------------------------------------------------------------------


def test_all_17_tools_are_registered():
    """_TOOLS_BY_NAME must contain all 17 expected tool keys."""
    from src.modules.copilot.api.section_tools import _TOOLS_BY_NAME

    expected = {
        "adapt_from_brand_identity",
        "adapt_from_brand_narrative",
        "rewrite_tones",
        "validate_preset_coherence",
        "reuse_brand_buyer_personas",
        "inherit_brand_methodology",
        "high_ticket_tiering_template",
        "recurring_billing_setup",
        "detect_currency_mismatch",
        "import_scheduling_event_type",
        "detect_hybrid_split",
        "import_from_brand_vault",
        "suggest_missing_objections",
        "generate_from_preset_flags",
        "pull_sales_agent_common_questions",
        "assemble_from_brand_authority",
        "reuse_brand_team",
    }
    assert expected <= set(_TOOLS_BY_NAME.keys()), f"Missing tools: {expected - set(_TOOLS_BY_NAME.keys())}"
