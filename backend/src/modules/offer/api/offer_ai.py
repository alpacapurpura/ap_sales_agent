"""Offer Ai API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

# DDD exception (intentional): copilot is explicitly allowed to be imported by
# any module — it's an infra-like orchestrator (see backend-ddd.md rule).
from luana_core_copilot.application.services.offer_psychology_service import (
    CopilotOfferPsychologyService,
)
from luana_core_iam.api.dependencies import get_tenant_context
from luana_core_offer_studio.application.offer_generator import OfferGeneratorService
from luana_core_offer_studio.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/psychology")
async def generate_offer_psychology(
    request: PsychologyGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
) -> PsychologyGenerationResponse:
    """Generate AI-powered psychology insights (pains & desires) for an offer.

    Requires an Avatar ID and Offer Context.
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    psychology_port = CopilotOfferPsychologyService(db)
    service = OfferGeneratorService(psychology_port)
    try:
        return await service.generate_psychology(request, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI Generation failed: {e!s}",
        ) from e
