"""Smart-chip suggestions API (motor de sugerencias del composer).

# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md

Dos endpoints:
- POST /suggestions       — fetch ranked chips (best-effort: retorna [] en fallo de engine)
- POST /suggestions/accept — productor de telemetría (fire-and-forget, at-least-once OK)

Decisiones de diseño (CONTRACT §1):
- D-1:  POST con body context (no GET) — permite arrays recent_message_ids/incomplete_fields
- D-3:  engine es sync → asyncio.to_thread evita bloquear event loop
- D-4:  /accept flat (no nested) — sin lookup stateful de suggestion_id
- D-10: best-effort — endpoint NUNCA lanza 5xx por fallo interno del engine
- D-11: SuggestionShown emitido SIEMPRE (incluso 0 chips) para denominator métrica adopción
- D-15: reusar anchor [COPILOT-SUGGESTIONS-ENGINE] (cap 36/37)
- D-16: NO nuevos cross-module imports (ratchet 22 frozen)
"""

from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.modules.copilot.api.suggestions_dto import (
    SuggestionAcceptRequest,
    SuggestionAcceptResponse,
    SuggestionDTO,
    SuggestionsRequest,
    SuggestionsResponse,
)
from src.modules.copilot.application.suggestions.registry import get_default_engine
from src.modules.copilot.domain.events import SuggestionAccepted, SuggestionShown
from src.modules.copilot.domain.suggestion import SuggestionContext
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)

logger = structlog.get_logger()

router = APIRouter(tags=["Copilot - Suggestions"])


@router.post(
    "/suggestions",
    response_model=SuggestionsResponse,
    summary="Obtener smart-chips dinámicas para el contexto actual",
)
async def get_suggestions(
    request: SuggestionsRequest,
    current_user: Annotated[object, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
) -> SuggestionsResponse:
    """Devuelve hasta 5 chips ordenadas por confidence descendente.

    Best-effort: si el engine falla retorna ``suggestions=[]`` (D-10).
    Nunca retorna 5xx por fallo interno del engine — solo 401/403/422.
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    user_id: UUID | None = getattr(current_user, "id", None)

    ctx = SuggestionContext(
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=request.conversation_id,
        current_route=request.current_route,
        recent_message_ids=tuple(request.recent_message_ids),
        incomplete_fields=tuple(request.incomplete_fields),
        locale="es",  # D-8: mono-locale LATAM, no client-side override
    )

    engine = get_default_engine()
    try:
        # D-3: engine es sync — asyncio.to_thread evita bloquear event loop
        suggestions, breakdown, latency_ms = await asyncio.to_thread(engine.get_suggestions, ctx)
    except Exception as exc:  # noqa: BLE001 — best-effort (D-10)
        logger.warning(
            "suggestions_engine_failed",
            tenant_id=str(tenant_id),
            current_route=request.current_route,
            error=str(exc),
        )
        suggestions, breakdown, latency_ms = [], {}, 0

    # D-11: emite SuggestionShown SIEMPRE (incluso 0 chips)
    # Permite tracking "oportunidades totales" como denominador del ratio adopción.
    try:
        EventBus.publish(
            SuggestionShown.create(
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=request.conversation_id,
                current_route=request.current_route,
                suggestion_ids=[s.id for s in suggestions],
                provider_breakdown=breakdown,
                latency_ms=latency_ms,
            ),
            session=None,
        )
    except Exception as exc:  # noqa: BLE001 — observability resilience
        logger.warning(
            "suggestion_shown_publish_failed",
            tenant_id=str(tenant_id),
            error=str(exc),
        )

    return SuggestionsResponse(
        suggestions=[
            SuggestionDTO(
                id=s.id,
                label=s.label,
                prompt=s.prompt,
                confidence=s.confidence,
                category=s.category.value,
                source_module=s.source_module,
                # metadata EXCLUIDO (D-6 PII allowlist)
            )
            for s in suggestions
        ],
        breakdown=breakdown,
        latency_ms=latency_ms,
    )


@router.post(
    "/suggestions/accept",
    response_model=SuggestionAcceptResponse,
    status_code=202,
    summary="Reportar que el usuario clickeó una chip (telemetría)",
)
async def accept_suggestion(
    request: SuggestionAcceptRequest,
    current_user: Annotated[object, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
) -> SuggestionAcceptResponse:
    """Productor fire-and-forget del evento SuggestionAccepted.

    Best-effort: fallo del bus → log warning + retorna ok=False. FE ignora response.
    At-least-once OK (D-5) — métrica usa COUNT(DISTINCT suggestion_id).
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    user_id: UUID | None = getattr(current_user, "id", None)

    try:
        EventBus.publish(
            SuggestionAccepted.create(
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=request.conversation_id,
                suggestion_id=request.suggestion_id,
                source_module=request.source_module,
                category=request.category,
            ),
            session=None,
        )
        return SuggestionAcceptResponse(ok=True)
    except Exception as exc:  # noqa: BLE001 — telemetría no debe romper UX
        logger.warning(
            "suggestion_accepted_publish_failed",
            tenant_id=str(tenant_id),
            suggestion_id=str(request.suggestion_id),
            error=str(exc),
        )
        return SuggestionAcceptResponse(ok=False)


__all__ = ["router"]
