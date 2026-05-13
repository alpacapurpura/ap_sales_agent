"""Campaigns router — CRUD + FSM lifecycle.

23 endpoints across campaigns, steps, segments, templates.
Routes are thin: validate DTO → service call → map exception → HTTPException.
No business logic in this layer.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from luana_core_campaigns.api._dependencies import get_campaigns_async_session
from luana_core_campaigns.api._service_factories import (
    get_campaign_orchestrator,
    get_campaign_service,
    get_campaign_stats_service,
)
from luana_core_campaigns.application.dtos.campaign_dtos import (
    CampaignCancelRequest,
    CampaignCreate,
    CampaignLaunchResponse,
    CampaignResponse,
    CampaignScheduleRequest,
    CampaignSortBy,
    CampaignStatsResponse,
    CampaignUpdate,
)
from luana_core_campaigns.application.dtos.campaign_step_dtos import (
    CampaignStepCreate,
    CampaignStepResponse,
    CampaignStepUpdate,
)
from luana_core_campaigns.application.dtos.pagination import PaginatedResponse
from luana_core_campaigns.application.services.campaign_service import (
    CampaignDuplicateNameError,
    CampaignInvalidTransitionError,
    CampaignInvariantError,
    CampaignNotEditableError,
    CampaignNotFoundError,
    CampaignPlanLimitExceededError,
    CampaignService,
)
from luana_core_campaigns.application.services.campaign_stats_service import CampaignStatsService
from luana_core_campaigns.application.services.orchestrator import (
    CampaignOrchestrator,
    OrchestratorCampaignNotFoundError,
    OrchestratorCampaignNotLaunchableError,
    OrchestratorMissingStepsError,
    OrchestratorSegmentEmptyError,
)
from luana_core_campaigns.domain.enums import CampaignStatus, CampaignType
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/campaigns",
    tags=["campaigns"],
)


def _tenant_id(user: User) -> UUID:
    """Extract tenant_id from authenticated user."""
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="Usuario sin tenant asignado.")
    return UUID(str(user.tenant_id))


# Map exception type → (http_status, fallback_message)
_CAMPAIGN_ERROR_MAP: dict[type[Exception], tuple[int, str]] = {
    CampaignNotFoundError: (404, "Campaña no encontrada."),
    CampaignDuplicateNameError: (409, "Ya existe una campaña con ese nombre."),
    CampaignInvalidTransitionError: (409, "Transición de estado no permitida."),
    CampaignNotEditableError: (409, "Solo campañas en estado DRAFT son editables."),
    CampaignPlanLimitExceededError: (402, "Límite de campañas activas del plan alcanzado."),
    CampaignInvariantError: (422, "Invariante de campaña violada."),
}


def _map_campaign_error(exc: Exception) -> HTTPException:
    """Map service exceptions to HTTP status codes."""
    for exc_type, (http_status, fallback) in _CAMPAIGN_ERROR_MAP.items():
        if isinstance(exc, exc_type):
            return HTTPException(status_code=http_status, detail=str(exc) or fallback)
    return HTTPException(status_code=500, detail="Error interno del servidor.")


# ── Campaign CRUD ─────────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear campaña",
)
async def create_campaign(
    body: CampaignCreate,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> CampaignResponse:
    """Create a new DRAFT campaign for the authenticated tenant."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.create(
            tenant_id=tenant_id,
            dto=body,
            session=session,
            user_id=UUID(str(user.id)),
        )
        return CampaignResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.get(
    "/",
    response_model=PaginatedResponse[CampaignResponse],
    summary="Listar campañas",
)
async def list_campaigns(
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
    status_filter: Annotated[list[CampaignStatus] | None, Query(alias="status")] = None,
    campaign_type: Annotated[list[CampaignType] | None, Query(alias="type")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort_by: Annotated[CampaignSortBy, Query()] = "created_at_desc",
) -> PaginatedResponse[CampaignResponse]:
    """List campaigns paginated with optional filters."""
    tenant_id = _tenant_id(user)
    return await svc.list(
        tenant_id=tenant_id,
        session=session,
        status_filter=status_filter,
        type_filter=campaign_type,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Obtener campaña",
)
async def get_campaign(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignResponse:
    """Get a single campaign by ID."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.get(tenant_id=tenant_id, campaign_id=campaign_id, session=session)
        return CampaignResponse.model_validate(result)
    except CampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Campaña no encontrada.") from exc


@router.patch(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Actualizar campaña",
)
async def update_campaign(
    campaign_id: UUID,
    body: CampaignUpdate,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignResponse:
    """Update a DRAFT campaign. Returns 409 if campaign is not in DRAFT status."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.update(tenant_id=tenant_id, campaign_id=campaign_id, dto=body, session=session)
        return CampaignResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar campaña (soft delete)",
)
async def delete_campaign(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> None:
    """Soft delete a campaign. Cancels running/paused campaigns first."""
    tenant_id = _tenant_id(user)
    try:
        await svc.delete(tenant_id=tenant_id, campaign_id=campaign_id, session=session)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


# ── FSM Transitions ───────────────────────────────────────────────────────────


@router.post(
    "/{campaign_id}/schedule",
    response_model=CampaignResponse,
    summary="Programar campaña (DRAFT → SCHEDULED)",
)
async def schedule_campaign(
    campaign_id: UUID,
    body: CampaignScheduleRequest,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignResponse:
    """Transition DRAFT → SCHEDULED. Requires segment_id set on campaign."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.schedule(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            scheduled_for=body.scheduled_for,
            session=session,
        )
        return CampaignResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.post(
    "/{campaign_id}/launch",
    response_model=CampaignLaunchResponse,
    summary="Lanzar campaña (SCHEDULED → RUNNING)",
)
async def launch_campaign(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    orchestrator: Annotated[CampaignOrchestrator, Depends(get_campaign_orchestrator)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignLaunchResponse:
    """Launch campaign: resolve segment, create root tasks, enqueue via ARQ.

    Returns 200 with tasks_generated count. Idempotent within 10min TTL.
    - 404: campaign not found or not owned by tenant.
    - 409: campaign not in a launchable state (e.g. already COMPLETED or CANCELED).
    - 422: segment empty or no root steps.
    """
    tenant_id = _tenant_id(user)
    try:
        async with session.begin():
            result = await orchestrator.launch(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                session=session,
            )
        # Post-commit: best-effort ARQ enqueue (scheduler_tick backstop on failure)
        await orchestrator.enqueue_pending_tasks()
        # Fetch updated campaign for response
        campaign_obj = await svc.get(tenant_id=tenant_id, campaign_id=campaign_id, session=session)
        return CampaignLaunchResponse(
            campaign=CampaignResponse.model_validate(campaign_obj),
            tasks_generated=result.tasks_generated,
            notice=(
                "Lanzamiento ejecutado. Tasks raíz creadas y dispatch en cola via "
                "ChannelRouterRegistry. Audit log: GET /campaigns/{id}/audit (futuro post-PI-1)."
            ),
        )
    except OrchestratorCampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Campaña no encontrada.") from exc
    except OrchestratorCampaignNotLaunchableError as exc:
        raise HTTPException(status_code=409, detail=str(exc) or "Transición de estado no permitida.") from exc
    except (OrchestratorSegmentEmptyError, OrchestratorMissingStepsError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.post(
    "/{campaign_id}/pause",
    response_model=CampaignResponse,
    summary="Pausar campaña (RUNNING → PAUSED)",
)
async def pause_campaign(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignResponse:
    """Pause a running campaign. Idempotent: PAUSED → PAUSED = 200."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.pause(tenant_id=tenant_id, campaign_id=campaign_id, session=session)
        return CampaignResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.post(
    "/{campaign_id}/resume",
    response_model=CampaignResponse,
    summary="Reanudar campaña (PAUSED → RUNNING)",
)
async def resume_campaign(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignResponse:
    """Resume a paused campaign. Idempotent: RUNNING → RUNNING = 200."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.resume(tenant_id=tenant_id, campaign_id=campaign_id, session=session)
        return CampaignResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.post(
    "/{campaign_id}/complete",
    response_model=CampaignResponse,
    summary="Completar campaña (RUNNING → COMPLETED)",
)
async def complete_campaign(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignResponse:
    """Mark a running campaign as completed (terminal state)."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.complete(tenant_id=tenant_id, campaign_id=campaign_id, session=session)
        return CampaignResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.post(
    "/{campaign_id}/cancel",
    response_model=CampaignResponse,
    summary="Cancelar campaña (* → CANCELED)",
)
async def cancel_campaign(
    campaign_id: UUID,
    body: CampaignCancelRequest,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignResponse:
    """Cancel a campaign from any non-terminal state."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.cancel(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            reason=body.reason,
            session=session,
        )
        return CampaignResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


# ── Stats ─────────────────────────────────────────────────────────────────────


@router.get(
    "/{campaign_id}/stats",
    response_model=CampaignStatsResponse,
    summary="Estadísticas agregadas de campaña",
)
async def get_campaign_stats(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignStatsService, Depends(get_campaign_stats_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignStatsResponse:
    """Estadísticas live de las campaign tasks. Tenant-scoped. Lectura idempotente."""
    tenant_id = _tenant_id(user)
    try:
        return await svc.get_stats(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            session=session,
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Campaña no encontrada.") from exc


# ── Steps ─────────────────────────────────────────────────────────────────────


@router.post(
    "/{campaign_id}/steps/",
    response_model=CampaignStepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar paso a campaña",
)
async def add_step(
    campaign_id: UUID,
    body: CampaignStepCreate,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignStepResponse:
    """Add a step to a DRAFT campaign."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.add_step(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            dto=body,
            session=session,
        )
        return CampaignStepResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.patch(
    "/{campaign_id}/steps/{step_id}",
    response_model=CampaignStepResponse,
    summary="Actualizar paso de campaña",
)
async def update_step(
    campaign_id: UUID,
    step_id: UUID,
    body: CampaignStepUpdate,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignStepResponse:
    """Update a step on a DRAFT campaign."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.update_step(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            step_id=step_id,
            dto=body,
            session=session,
        )
        return CampaignStepResponse.model_validate(result)
    except Exception as exc:
        raise _map_campaign_error(exc) from exc


@router.delete(
    "/{campaign_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar paso de campaña",
)
async def delete_step(
    campaign_id: UUID,
    step_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignService, Depends(get_campaign_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> None:
    """Soft delete a step from a DRAFT campaign."""
    tenant_id = _tenant_id(user)
    try:
        await svc.delete_step(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            step_id=step_id,
            session=session,
        )
    except Exception as exc:
        raise _map_campaign_error(exc) from exc
