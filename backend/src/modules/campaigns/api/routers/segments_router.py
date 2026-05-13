"""Segments router — CRUD + resolve + estimate-size + snapshot.

Routes are thin: validate DTO → service call → map exception → HTTPException.
No business logic in this layer.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from luana_core_campaigns.api._dependencies import get_campaigns_async_session
from luana_core_campaigns.api._service_factories import get_segment_service
from luana_core_campaigns.application.dtos.pagination import PaginatedResponse
from luana_core_campaigns.application.dtos.segment_dtos import (
    SegmentCreate,
    SegmentEstimateSizeResponse,
    SegmentResolveRequest,
    SegmentResolveResponse,
    SegmentResponse,
    SegmentSnapshotResponse,
    SegmentUpdate,
)
from luana_core_campaigns.application.services.segment_service import (
    SegmentDuplicateNameError,
    SegmentLeadOwnershipError,
    SegmentNotFoundError,
    SegmentService,
)
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/segments",
    tags=["segments"],
)


def _tenant_id(user: User) -> UUID:
    """Extract tenant_id from authenticated user."""
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="Usuario sin tenant asignado.")
    return UUID(str(user.tenant_id))


def _map_segment_error(exc: Exception) -> HTTPException:
    """Map service exceptions to HTTP status codes."""
    if isinstance(exc, SegmentNotFoundError):
        return HTTPException(status_code=404, detail=str(exc) or "Segmento no encontrado.")
    if isinstance(exc, SegmentDuplicateNameError):
        return HTTPException(status_code=409, detail=str(exc) or "Ya existe un segmento con ese nombre.")
    if isinstance(exc, SegmentLeadOwnershipError):
        return HTTPException(status_code=422, detail=str(exc) or "Algunos lead_ids no pertenecen a este tenant.")
    return HTTPException(status_code=500, detail="Error interno del servidor.")


# ── Segment CRUD ──────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=PaginatedResponse[SegmentResponse],
    summary="Listar segmentos",
)
async def list_segments(
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[SegmentResponse]:
    """List segments paginated for the authenticated tenant."""
    tenant_id = _tenant_id(user)
    return await svc.list_segments(tenant_id=tenant_id, session=session, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=SegmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear segmento",
)
async def create_segment(
    body: SegmentCreate,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> SegmentResponse:
    """Create a new segment for the authenticated tenant."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.create(tenant_id=tenant_id, dto=body, session=session)
        return SegmentResponse.model_validate(result)
    except Exception as exc:
        raise _map_segment_error(exc) from exc


@router.get(
    "/{segment_id}",
    response_model=SegmentResponse,
    summary="Obtener segmento",
)
async def get_segment(
    segment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> SegmentResponse:
    """Get a single segment by ID."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.get(tenant_id=tenant_id, segment_id=segment_id, session=session)
        return SegmentResponse.model_validate(result)
    except SegmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Segmento no encontrado.") from exc


@router.patch(
    "/{segment_id}",
    response_model=SegmentResponse,
    summary="Actualizar segmento",
)
async def update_segment(
    segment_id: UUID,
    body: SegmentUpdate,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> SegmentResponse:
    """Update a segment. Invalidates estimate_size cache."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.update(tenant_id=tenant_id, segment_id=segment_id, dto=body, session=session)
        return SegmentResponse.model_validate(result)
    except Exception as exc:
        raise _map_segment_error(exc) from exc


@router.delete(
    "/{segment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar segmento (soft delete)",
)
async def delete_segment(
    segment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> None:
    """Soft delete a segment."""
    tenant_id = _tenant_id(user)
    try:
        await svc.delete(tenant_id=tenant_id, segment_id=segment_id, session=session)
    except SegmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Segmento no encontrado.") from exc


# ── Segment Actions ───────────────────────────────────────────────────────────


@router.post(
    "/{segment_id}/resolve",
    response_model=SegmentResolveResponse,
    summary="Resolver segmento (lazy SQL, devuelve UUIDs)",
)
async def resolve_segment(
    segment_id: UUID,
    body: SegmentResolveRequest,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> SegmentResolveResponse:
    """Resolve segment to a list of lead UUIDs (SQL-side filtering, no PII)."""
    tenant_id = _tenant_id(user)
    try:
        lead_ids, lead_count, truncated = await svc.resolve(
            tenant_id=tenant_id,
            segment_id=segment_id,
            at=body.at,
            limit=body.limit,
            session=session,
        )
        return SegmentResolveResponse(
            segment_id=segment_id,
            at=body.at or utc_now(),
            lead_count=lead_count,
            lead_ids=lead_ids,
            truncated=truncated,
        )
    except SegmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Segmento no encontrado.") from exc


@router.get(
    "/{segment_id}/estimate-size",
    response_model=SegmentEstimateSizeResponse,
    summary="Estimación de tamaño del segmento (caché 5min)",
)
async def estimate_segment_size(
    segment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> SegmentEstimateSizeResponse:
    """Get cached estimate of segment size (5-min cache)."""
    tenant_id = _tenant_id(user)
    try:
        estimated_size, cached_at, cache_hit = await svc.estimate_size(
            tenant_id=tenant_id,
            segment_id=segment_id,
            session=session,
        )
        return SegmentEstimateSizeResponse(
            segment_id=segment_id,
            estimated_size=estimated_size,
            cached_at=cached_at,
            cache_hit=cache_hit,
        )
    except SegmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Segmento no encontrado.") from exc


@router.post(
    "/{segment_id}/snapshot",
    response_model=SegmentSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Materializar snapshot del segmento",
)
async def snapshot_segment(
    segment_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SegmentService, Depends(get_segment_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> SegmentSnapshotResponse:
    """Create a point-in-time snapshot of the segment."""
    tenant_id = _tenant_id(user)
    try:
        result = await svc.snapshot(tenant_id=tenant_id, segment_id=segment_id, session=session)
        return SegmentSnapshotResponse.model_validate(result)
    except SegmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Segmento no encontrado.") from exc
