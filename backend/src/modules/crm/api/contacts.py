"""CRM Contacts API — PR-10 PI-1 S4.

5 endpoints forward-compat:
  GET /api/v1/contacts              — listado paginado con TODOS PI-3 filters
  GET /api/v1/contacts/{id}         — detalle completo
  GET /api/v1/contacts/{id}/journey — 501 deferred PI-3
  GET /api/v1/contacts/{id}/campaigns — 501 deferred PI-3
  GET /api/v1/contacts/_filter-schema — metadata filtros para UI dinámica

Tenant isolation: tenant_id de get_current_user (via Clerk JWT + X-Tenant-ID).
response_model= en cada endpoint (PII allowlist).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.api._dependencies import get_campaigns_async_session
from src.modules.campaigns.application.dtos.pagination import PaginatedResponse
from src.modules.crm.api.dto.contact_filters import ContactFilterParams
from src.modules.crm.api.dto.contacts import (
    ContactDetail,
    ContactListItem,
    DeferredEndpointResponse,
    FilterFieldMeta,
    FilterSchemaResponse,
)
from src.modules.crm.application.services.contact_query_service import (
    ContactQueryService,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.shared.domain.enums import LifecycleStage
from src.shared.links.ports.campaigns import create_campaigns_lookup_port

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/contacts",
    tags=["crm:contacts"],
)


def _get_tenant_id(user: User) -> UUID:
    """Extraer tenant_id del usuario autenticado.

    Raises:
        HTTPException 403 si el usuario no tiene tenant asignado.
    """
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="Usuario sin tenant asignado.")
    return UUID(str(user.tenant_id))


async def _get_contact_query_service(
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> ContactQueryService:
    """Factory de ContactQueryService para inyección de dependencias."""
    campaigns_lookup = create_campaigns_lookup_port()
    return ContactQueryService(session=session, campaigns_lookup=campaigns_lookup)


def _parse_datetime(val: str | None, field_name: str) -> datetime | None:
    """Parsear datetime desde string ISO 8601.

    Args:
        val: String ISO 8601 o None.
        field_name: Nombre del campo (para mensaje de error).

    Returns:
        datetime con timezone o None.

    Raises:
        HTTPException 400 si el formato es inválido.
    """
    if val is None:
        return None
    try:
        # fromisoformat en Python 3.11+ ya soporta 'Z' como UTC
        return datetime.fromisoformat(val)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de fecha inválido en '{field_name}': '{val}'. Use ISO 8601.",
        ) from None


# ── Metadata de filtros (estática — generada desde schema) ────────────────────
_FILTER_SCHEMA_FIELDS: list[FilterFieldMeta] = [
    FilterFieldMeta(
        name="lifecycle_stage_in",
        type="enum_list",
        enum_values=[s.value for s in LifecycleStage],
        description="Filtra por uno o más lifecycle stages.",
    ),
    FilterFieldMeta(
        name="score_min",
        type="int_range",
        enum_values=None,
        description="lead_score mínimo (0-100).",
    ),
    FilterFieldMeta(
        name="score_max",
        type="int_range",
        enum_values=None,
        description="lead_score máximo (0-100).",
    ),
    FilterFieldMeta(
        name="source_in",
        type="string",
        enum_values=None,
        description="Filtra por lead_source string (lista).",
    ),
    FilterFieldMeta(
        name="has_email",
        type="bool",
        enum_values=None,
        description="Solo contactos con email registrado.",
    ),
    FilterFieldMeta(
        name="has_phone",
        type="bool",
        enum_values=None,
        description="Solo contactos con teléfono registrado.",
    ),
    FilterFieldMeta(
        name="has_telegram_id",
        type="bool",
        enum_values=None,
        description="Solo contactos con ID de Telegram.",
    ),
    FilterFieldMeta(
        name="has_whatsapp_id",
        type="bool",
        enum_values=None,
        description="Solo contactos con ID de WhatsApp.",
    ),
    FilterFieldMeta(
        name="has_instagram_id",
        type="bool",
        enum_values=None,
        description="Solo contactos con ID de Instagram.",
    ),
    FilterFieldMeta(
        name="has_tiktok_id",
        type="bool",
        enum_values=None,
        description="Solo contactos con ID de TikTok.",
    ),
    FilterFieldMeta(
        name="created_after",
        type="datetime",
        enum_values=None,
        description="Contactos creados después de esta fecha (ISO 8601).",
    ),
    FilterFieldMeta(
        name="created_before",
        type="datetime",
        enum_values=None,
        description="Contactos creados antes de esta fecha (ISO 8601).",
    ),
    FilterFieldMeta(
        name="last_activity_after",
        type="datetime",
        enum_values=None,
        description="Última actividad después de esta fecha.",
    ),
    FilterFieldMeta(
        name="last_activity_before",
        type="datetime",
        enum_values=None,
        description="Última actividad antes de esta fecha.",
    ),
    FilterFieldMeta(
        name="is_inactive",
        type="bool",
        enum_values=None,
        description="Contactos marcados como inactivos.",
    ),
    FilterFieldMeta(
        name="has_campaign_engagement",
        type="bool",
        enum_values=None,
        description="Contactos que recibieron >=1 campaña en los últimos 90 días.",
    ),
    FilterFieldMeta(
        name="country_in",
        type="string",
        enum_values=None,
        description="País ISO 3166-1 alpha-2 lowercase (ej. 'mx', 'pe', 'co').",
    ),
    FilterFieldMeta(
        name="q",
        type="string",
        enum_values=None,
        description="Búsqueda por nombre, email o teléfono (máx. 120 caracteres).",
    ),
]


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=PaginatedResponse[ContactListItem],
    summary="Listar contactos",
    description=(
        "Listado paginado de contactos con filtros forward-compat. "
        "UI lite consume subset de filtros hoy; PI-3 expande la UI sin modificar esta API. "
        "Ordenado por última actividad descendente (más reciente primero). "
        "Máximo 100 resultados por página. "
        "Cache-Control: private, max-age=30."
    ),
)
@router.get(
    "/",
    response_model=PaginatedResponse[ContactListItem],
    include_in_schema=False,
)
async def list_contacts(
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[ContactQueryService, Depends(_get_contact_query_service)],
    limit: Annotated[int, Query(ge=1, le=100, description="Máximo de resultados (1-100).")] = 50,
    offset: Annotated[int, Query(ge=0, description="Offset para paginación.")] = 0,
    lifecycle_stage_in: Annotated[
        list[LifecycleStage] | None,
        Query(alias="lifecycle_stage_in", description="Lifecycle stages a incluir."),
    ] = None,
    score_min: Annotated[int | None, Query(ge=0, le=100)] = None,
    score_max: Annotated[int | None, Query(ge=0, le=100)] = None,
    source_in: Annotated[list[str] | None, Query(alias="source_in")] = None,
    has_email: Annotated[bool | None, Query()] = None,
    has_phone: Annotated[bool | None, Query()] = None,
    has_telegram_id: Annotated[bool | None, Query()] = None,
    has_whatsapp_id: Annotated[bool | None, Query()] = None,
    has_instagram_id: Annotated[bool | None, Query()] = None,
    has_tiktok_id: Annotated[bool | None, Query()] = None,
    created_after: Annotated[datetime | None, Query(description="ISO 8601 datetime.")] = None,
    created_before: Annotated[datetime | None, Query(description="ISO 8601 datetime.")] = None,
    last_activity_after: Annotated[datetime | None, Query(description="ISO 8601 datetime.")] = None,
    last_activity_before: Annotated[datetime | None, Query(description="ISO 8601 datetime.")] = None,
    is_inactive: Annotated[bool | None, Query()] = None,
    has_campaign_engagement: Annotated[bool | None, Query()] = None,
    country_in: Annotated[list[str] | None, Query(alias="country_in")] = None,
    q: Annotated[str | None, Query(max_length=120, description="Búsqueda por nombre, email o teléfono.")] = None,
) -> PaginatedResponse[ContactListItem]:
    """Listar contactos con filtros y paginación."""
    tenant_id = _get_tenant_id(user)

    filters = ContactFilterParams(
        lifecycle_stage_in=lifecycle_stage_in,
        score_min=score_min,
        score_max=score_max,
        source_in=source_in,
        has_email=has_email,
        has_phone=has_phone,
        has_telegram_id=has_telegram_id,
        has_whatsapp_id=has_whatsapp_id,
        has_instagram_id=has_instagram_id,
        has_tiktok_id=has_tiktok_id,
        created_after=created_after,
        created_before=created_before,
        last_activity_after=last_activity_after,
        last_activity_before=last_activity_before,
        is_inactive=is_inactive,
        has_campaign_engagement=has_campaign_engagement,
        country_in=country_in,
        q=q,
    )

    return await svc.list_contacts(
        tenant_id=tenant_id,
        filters=filters,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/_filter-schema",
    response_model=FilterSchemaResponse,
    summary="Schema de filtros disponibles",
    description=(
        "Retorna metadata de todos los filtros disponibles para el endpoint de contactos. "
        "Usado por la UI para construir el panel de filtros de forma dinámica (PI-3). "
        "También sirve como documentación auto-contenida del contrato de filtros."
    ),
)
async def get_filter_schema() -> FilterSchemaResponse:
    """Retornar schema de filtros disponibles para construcción dinámica de UI."""
    return FilterSchemaResponse(
        version="1.0",
        fields=_FILTER_SCHEMA_FIELDS,
    )


@router.get(
    "/{contact_id}",
    response_model=ContactDetail,
    summary="Detalle de contacto",
    description=(
        "Retorna el detalle completo de un contacto. "
        "Incluye datos del perfil unificado (CustomerProfile), "
        "datos del lead asociado (canales, scoring), e identidades multi-canal. "
        "Retorna 404 tanto si el contacto no existe como si pertenece a otro tenant "
        "(sin filtrar existencia)."
    ),
)
async def get_contact_detail(
    contact_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[ContactQueryService, Depends(_get_contact_query_service)],
) -> ContactDetail:
    """Obtener detalle completo de un contacto por ID."""
    tenant_id = _get_tenant_id(user)

    detail = await svc.get_contact_detail(
        tenant_id=tenant_id,
        contact_id=contact_id,
    )

    if detail is None:
        raise HTTPException(status_code=404, detail="Contacto no encontrado.")

    return detail


@router.get(
    "/{contact_id}/journey",
    response_model=DeferredEndpointResponse,
    status_code=501,
    summary="Timeline de eventos del contacto (deferred PI-3)",
    description=(
        "Timeline de eventos del contacto (page views, opens, clicks, conversions). "
        "Endpoint canonical declarado para PR-10 forward-compat. "
        "Implementación deferred PI-3 — consumir cuando el endpoint retorne 200."
    ),
    responses={
        501: {
            "model": DeferredEndpointResponse,
            "headers": {
                "Retry-After": {
                    "schema": {"type": "string"},
                    "description": "Implementación disponible en PI-3.",
                }
            },
        }
    },
)
async def get_contact_journey(contact_id: UUID) -> JSONResponse:
    """Stub 501 — implementación deferred PI-3."""
    payload = DeferredEndpointResponse(
        detail="Este endpoint está declarado para forward-compat y será implementado en PI-3.",
        deferred_until="PI-3",
        canonical_path=f"/api/v1/contacts/{contact_id}/journey",
        expected_response_model="ContactJourneyResponse",
    )
    return JSONResponse(
        status_code=501,
        content=payload.model_dump(),
        headers={"Retry-After": "PI-3"},
    )


@router.get(
    "/{contact_id}/campaigns",
    response_model=DeferredEndpointResponse,
    status_code=501,
    summary="Historial de campañas del contacto (deferred PI-3)",
    description=(
        "Historial de campañas en las que el contacto participó. "
        "Endpoint canonical declarado para PR-10 forward-compat. "
        "Implementación deferred PI-3 — consumir cuando el endpoint retorne 200."
    ),
    responses={
        501: {
            "model": DeferredEndpointResponse,
            "headers": {
                "Retry-After": {
                    "schema": {"type": "string"},
                    "description": "Implementación disponible en PI-3.",
                }
            },
        }
    },
)
async def get_contact_campaigns(contact_id: UUID) -> JSONResponse:
    """Stub 501 — implementación deferred PI-3."""
    payload = DeferredEndpointResponse(
        detail="Este endpoint está declarado para forward-compat y será implementado en PI-3.",
        deferred_until="PI-3",
        canonical_path=f"/api/v1/contacts/{contact_id}/campaigns",
        expected_response_model="ContactCampaignsResponse",
    )
    return JSONResponse(
        status_code=501,
        content=payload.model_dump(),
        headers={"Retry-After": "PI-3"},
    )
