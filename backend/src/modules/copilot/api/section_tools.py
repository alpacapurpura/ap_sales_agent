"""Offer Section Tools REST endpoint.

Exposes the 17 offer-section copilot tools as a direct REST surface so the
frontend ``OfferSectionCopilot`` component can invoke them without going
through the LangGraph chat orchestrator.

Route: POST /api/v1/copilot/offer-section-tools/{tool_key}

Architecture rules:
- Response-model is mandatory (PII gate).
- Tenant isolation is set via ``set_tenant_id`` from ``get_current_user``.
- Tools are invoked by their LangChain name (``tool.name``), not imported
  directly — keeps this file decoupled from the tool implementations.
- No cross-module imports beyond the tool registry and IAM dependency.
"""

import json
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.core.context import set_tenant_id
from src.modules.copilot.application.tools.offer_section_tools import OFFER_SECTION_TOOLS
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

logger = structlog.get_logger()

router = APIRouter()

# ---------------------------------------------------------------------------
# Tool registry — keyed by tool.name (matches the function name)
# ---------------------------------------------------------------------------

_TOOLS_BY_NAME: dict[str, Any] = {t.name: t for t in OFFER_SECTION_TOOLS}


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class OfferSectionToolRequest(BaseModel):
    """Payload for invoking an offer-section copilot tool."""

    offer_id: str
    section_slug: str
    edition_code: str | None = None
    tool_args: dict[str, str] = {}


class OfferSectionToolResult(BaseModel):
    """Response mirroring the JSON returned by every offer-section tool."""

    section_slug: str
    draft_fields: dict[str, Any]
    suggestions: list[str]
    confidence: float
    citations: list[str]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/{tool_key}", response_model=OfferSectionToolResult)  # noqa: FAST001
async def invoke_offer_section_tool(
    tool_key: str,
    body: OfferSectionToolRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> OfferSectionToolResult:
    """Invoke a named offer-section copilot tool and return draft fields.

    The tool is invoked synchronously (LangChain tools are synchronous) with
    the ``tool_args`` dict from the request body.  Tenant isolation is set in
    the context var before invocation so every tool's ``get_tenant_id()``
    call returns the correct value.

    Returns 404 when ``tool_key`` does not match any registered tool.
    Returns 422 when required fields are missing (handled by Pydantic).
    """
    tool = _TOOLS_BY_NAME.get(tool_key)
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tool_key '{tool_key}'. Available: {sorted(_TOOLS_BY_NAME.keys())}",
        )

    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant.")

    # Inject tenant_id into request-scoped context var so tools can call
    # get_tenant_id() and receive the correct value.
    set_tenant_id(str(current_user.tenant_id))

    logger.info(
        "offer_section_tool_invoked",
        tool_key=tool_key,
        offer_id=body.offer_id,
        section_slug=body.section_slug,
        tenant_id=str(current_user.tenant_id),
    )

    try:
        raw: str = tool.invoke(body.tool_args)
        data: dict[str, Any] = json.loads(raw)
    except Exception as exc:
        logger.exception(
            "offer_section_tool_error",
            tool_key=tool_key,
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Tool '{tool_key}' raised an unexpected error.",
        ) from exc

    return OfferSectionToolResult(
        section_slug=data.get("section_slug", body.section_slug),
        draft_fields=data.get("draft_fields", {}),
        suggestions=data.get("suggestions", []),
        confidence=float(data.get("confidence", 0.0)),
        citations=data.get("citations", []),
    )
