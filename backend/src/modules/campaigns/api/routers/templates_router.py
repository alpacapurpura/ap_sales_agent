"""Templates router — catalog list + clone_to_campaign.

Routes are thin: validate DTO → service call → map exception → HTTPException.
No business logic in this layer.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.api._dependencies import get_campaigns_async_session
from src.modules.campaigns.api._service_factories import get_template_service
from src.modules.campaigns.application.dtos.campaign_dtos import CampaignResponse
from src.modules.campaigns.application.dtos.campaign_template_dtos import (
    CampaignCreateFromTemplate,
    CampaignTemplateResponse,
)
from src.modules.campaigns.application.services.campaign_template_service import (
    CampaignTemplateNotFoundError,
    CampaignTemplateService,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/templates",
    tags=["campaign-templates"],
)


def _tenant_id(user: User) -> UUID:
    """Extract tenant_id from authenticated user."""
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="Usuario sin tenant asignado.")
    return UUID(str(user.tenant_id))


# ── Templates catalog ─────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[CampaignTemplateResponse],
    summary="Listar templates de campañas (globals + tenant)",
)
async def list_templates(
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignTemplateService, Depends(get_template_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> list[CampaignTemplateResponse]:
    """List available templates (global Nicolify-provided + tenant-specific). Cached 5min."""
    tenant_id = _tenant_id(user)
    results = await svc.list_available(tenant_id=tenant_id, session=session)
    return [CampaignTemplateResponse.model_validate(t) for t in results]


@router.get(
    "/{template_id}",
    response_model=CampaignTemplateResponse,
    summary="Obtener template de campaña",
)
async def get_template(
    template_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignTemplateService, Depends(get_template_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignTemplateResponse:
    """Get a single template (global or tenant-scoped)."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.get(tenant_id=tenant_id, template_id=template_id, session=session)
        return CampaignTemplateResponse.model_validate(result)
    except CampaignTemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Template no encontrado.") from exc


@router.post(
    "/{template_id}/clone",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clonar template a nueva campaña",
)
async def clone_template(
    template_id: UUID,
    body: CampaignCreateFromTemplate,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignTemplateService, Depends(get_template_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> CampaignResponse:
    """Clone a template into a new Campaign with Steps in a single transaction."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.clone_to_campaign(
            tenant_id=tenant_id,
            template_id=template_id,
            dto=body,
            session=session,
            user_id=UUID(str(user.id)),
        )
        return CampaignResponse.model_validate(result)
    except CampaignTemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Template no encontrado.") from exc
    except Exception as exc:
        logger.exception("clone_template_error", error=str(exc), template_id=str(template_id))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
