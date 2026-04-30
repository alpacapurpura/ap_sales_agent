# PR-1-fe-swap-suggestions-api — CONTRACT

> Owner: `nicolify-architect` (architect-empowered, ZERO open questions). Builders backend + frontend consumen en paralelo. Audit obligatorio.

## Meta

| Campo | Valor |
|---|---|
| Architect-empowered | sí, ZERO open questions |
| Fecha | 2026-04-30 |
| Owner | nicolify-architect |
| PR padre | PR-1-fe-swap-suggestions-api |
| Sprint | S2-copilot-cero-deuda-stack |
| PI | PI-2-copilot-improvement |
| Skills consultadas | `copilot-expert` (anchor cap 36/37, engine sync, ratchet `copilot→módulo` 22 frozen, channel registry zero-touch), `frontend-expert` (FSD-Lite, React Query patterns, Public API), `backend-expert` (Pydantic v2 ConfigDict, FastAPI response_model mandatory, SA 2.0) |
| Anchor reusado | `[COPILOT-SUGGESTIONS-ENGINE]` (existente — cap 36/37, NO bumpear) |
| current-state file impactado | `docs/pm-nico/current-state/copilot.md` (PM update post-merge — cap "Smart-chips live" + "Voice migration done") |
| Arch tests sensitivos | `test_api_contracts.py` (response_model gate), `test_copilot_anchors.py` (cap 36/37, sin nuevo anchor), `test_no_new_copilot_module_imports.py` (ratchet 22, sin nuevo cross-module import — solo `copilot.application` + `shared.events`), `test_copilot_provider_compliance.py`, `test_copilot_registry.py` |

## 0. Context Summary

### Estado pre-PR (verificado en código real)

| Surface | Estado | Path |
|---|---|---|
| `SuggestionEngine` | live, sync, `get_suggestions(ctx) -> (list, breakdown, latency_ms)` | `backend/src/modules/copilot/application/suggestions/engine.py` |
| `OfferSuggestionProvider` | live, registrado vía `_bootstrap_builtin` lazy | `backend/src/modules/copilot/application/suggestions/providers/offer.py` |
| `get_default_engine()` / `register_provider(...)` | live, threadsafe, idempotente | `backend/src/modules/copilot/application/suggestions/registry.py` |
| `SuggestionContext`, `Suggestion`, `SuggestionCategory` | live, frozen dataclass, validación post-init (label≤60, confidence∈[0,1]) | `backend/src/modules/copilot/domain/suggestion.py` |
| `SuggestionShown`, `SuggestionAccepted` events | live, dataclass+`create()` classmethod, NO emitter aún | `backend/src/modules/copilot/domain/events.py:194-256` |
| `EVENT_SUGGESTION_SHOWN`, `EVENT_SUGGESTION_ACCEPTED` literales | live | `backend/src/modules/copilot/domain/events.py:35-36` |
| Subscribers `on_suggestion_shown`, `on_suggestion_accepted` | live (forward-compat S1) — escriben `copilot_trace_event(event_type='suggestion_shown'/'suggestion_accepted')` | `backend/src/modules/copilot/observability/recording/domain_subscribers.py:98-107` |
| `EventBus.publish(event, session=None)` | live (`shared/domain_events/outbox/application/event_bus_adapter.py::adapter_bus`) | mismo bus que `RoutingDecided` usa en `chat.py:832` |
| `[COPILOT-SUGGESTIONS-ENGINE]` anchor | registrado (cap 36/37) | `backend/tests/architecture/test_copilot_anchors.py:26` |
| API surface `/api/v1/copilot/suggestions*` | NO existe | gap a llenar |
| `POST /api/v1/copilot/voice/upload-and-transcribe` | live, response = `VoiceUploadAndTranscribeResponse{block: AudioBlock}` (NO compatible con legacy `TranscriptionResponse{text, language, duration_seconds}`) | `backend/src/modules/copilot/api/voice.py:106` |
| `POST /api/v1/copilot/voice/transcribe` | 410 Gone con `X-Deprecation-Notice` | `backend/src/modules/copilot/api/voice.py:77` |
| FE `useSuggestions()` | stub estático `ROUTE_SUGGESTIONS` map | `frontend/src/features/copilot/hooks/use-suggestions.ts` |
| FE `voice-api.ts` | llama legacy `/voice/transcribe` (roto runtime, 410) | `frontend/src/features/copilot/api/voice-api.ts:26` |
| FE `SuggestedActions.tsx` | duplica `ROUTE_SUGGESTIONS` map (deuda) | `frontend/src/features/copilot/components/SuggestedActions.tsx` |

### Skills consultadas — decisiones tomadas

- **copilot-expert** — Engine es sync (no async). Wrapping en `asyncio.to_thread` evita bloquear event loop. Best-effort observability: try/except + structlog warning + db.rollback. NO usar `cast`. Cap anchors 36/37 → reusar `[COPILOT-SUGGESTIONS-ENGINE]` para nuevo file. Ratchet `copilot→módulo` 22 frozen → providers consumen `shared/links/ports/offer.py` ya registrado, no agrega entry. SSE no aplica (endpoint REST simple, NO streaming).
- **frontend-expert** — `feature-own` para hook+api+component (boundary matrix). React Query key namespace `["copilot", "suggestions", ...]`. `staleTime`/`gcTime` explícitos. Mutation `fire-and-forget` no invalida query.
- **backend-expert** — Pydantic v2 `ConfigDict`, NO `class Config`. `response_model=` MANDATORY (PII allowlist arch test gate). DTOs `model_config = ConfigDict(from_attributes=True)`. UUID serializado como str a `str(uuid)`. Datetime ISO 8601 UTC.

## 1. Decisions (numeradas, justificadas)

### D-1: Endpoint design — POST con body context (no GET, no SSE)

**Veredicto**: 2 endpoints REST POST en nuevo router file `copilot/api/suggestions.py`.

- `POST /api/v1/copilot/suggestions` — fetch chips dinámicas
- `POST /api/v1/copilot/suggestions/accept` — fire-and-forget producer event

**Razón** (criterio escalabilidad + cero deuda): POST con body permite `recent_message_ids` + `incomplete_fields` arrays (GET inviable con query params para arrays). Forward-compat para PR-2 providers que enriquecerán payload sin cambiar shape. SSE descartado (5 chips por snapshot, no real-time stream).

**Trade-off**: POST no cacheable HTTP (vs GET). Mitigado: React Query staleTime client-side cubre 99% repeat-fetches.

**Alternativa descartada**: GET `/api/v1/copilot/suggestions?route=...&conversation_id=...` — no soporta arrays cleanly, refactor obligatorio cuando providers crezcan (deuda segura).

### D-2: Router file dedicado — `copilot/api/suggestions.py`

**Veredicto**: nuevo file `backend/src/modules/copilot/api/suggestions.py` con `APIRouter()`. Mount en `main.py` bajo `prefix="/api/v1/copilot"` con `tags=["Copilot - Suggestions"]` y `dependencies=[Depends(get_tenant_context)]`.

**Razón** (cohesión, mismo patrón que conversations/voice/knowledge/nudge): Router por bounded context. Mantener `chat.py`, `voice.py`, `conversations.py` intocados (§3 de copilot-expert: NO tocar surfaces protegidas). 1 router 1 responsabilidad. Audit más simple.

**Trade-off**: 1 file extra a registrar en `main.py`. Costo despreciable.

**Alternativa descartada**: Agregar a `actions.py` o `events.py` — viola cohesión, mezcla semántica.

### D-3: Engine es sync — wrap async via `asyncio.to_thread`

**Veredicto**: route handler `async def`, llama `await asyncio.to_thread(engine.get_suggestions, ctx)`.

**Razón** (perf p99 <200ms): `SuggestionEngine.get_suggestions` es sync (engine.py:62). `OfferSuggestionProvider._compute` abre `SessionLocal()` sync (offer.py:84). Bloquear event loop en hot path = degradar TTFT. `asyncio.to_thread` (Python 3.9+) ofrece thread pool default 40 workers — suficiente para 1000+ tenants concurrentes.

**Trade-off**: 1 thread switch (~20-100µs overhead). Aceptable vs bloqueo event loop.

**Alternativa descartada A**: Reescribir engine async — invade §3 protected surface, scope creep, deuda nueva.
**Alternativa descartada B**: `loop.run_in_executor` con executor custom — `asyncio.to_thread` es sintácticamente más limpio + mismo resultado.

### D-4: Aceptación — endpoint dedicado `/accept` (no `/suggestions/{id}/accept`)

**Veredicto**: `POST /api/v1/copilot/suggestions/accept` con body `{suggestion_id, conversation_id, route?, accepted_at}`.

**Razón** (escalabilidad + zero stateful storage): Path `/accept` flat (no nested) porque NO existe persistencia stateful de suggestions per-id (decisión D-29 PI-2 S1 — `copilot_trace_event` único storage). Path nested implicaría lookup de la suggestion → 404 si no existe → complica forward-compat. Body-based at-least-once dedup posible vía `suggestion_id` UUID natural.

**Trade-off**: REST purist preferiría nested. Pragmatismo gana — zero lookup, zero deuda.

**Alternativa descartada**: `POST /suggestions/{id}/accept` — fuerza lookup, agrega path resolution sin valor (suggestion no persiste).

### D-5: Idempotency — at-least-once OK (subscriber dedup natural por `suggestion_id`)

**Veredicto**: NO idempotency key explícito en headers. `suggestion_id` UUID es natural-key. Subscriber escribe `copilot_trace_event` con `(suggestion_id, event_type='suggestion_accepted')` — at-least-once OK porque metric es ratio (`COUNT distinct suggestion_id WHERE event_type='accepted' / COUNT distinct suggestion_id WHERE event_type='shown'`).

**Razón** (cero deuda + simplicidad): Doble click usuario raro. Si ocurre, métrica usa `COUNT(DISTINCT)` no `COUNT(*)`. Sin tabla dedup → sin migration → sin Redis stateful.

**Trade-off**: 2 rows en `copilot_trace_event` para mismo `suggestion_id` posible. Minor, query agg compensa.

**Alternativa descartada**: Idempotency-Key header + Redis SETEX — sobre-engineering para evento de telemetría no-mutating.

### D-6: SuggestionDTO API shape — explícito, NO leak de `source_module`/`metadata`

**Veredicto**: Domain `Suggestion` tiene `source_module` + `metadata` (provider-private). API DTO los EXCLUYE del response (PII allowlist + reduce payload). `provider_id` SE expone en breakdown agregado (no per-chip).

**Razón** (PII safety + payload size): `source_module` revela provider implementation interna; `metadata` puede contener provider-internal hints (URLs, IDs no destinados al cliente). API consumer FE no necesita ninguno por-chip — el ranking ya está hecho server-side.

**Trade-off**: FE no puede filtrar/agrupar por `source_module` per-chip. No es UX requirement actual.

**Alternativa descartada**: Exponer todo — viola `pii-sanitisation.md` "remove fields not strictly needed".

### D-7: Confidence se expone — FE futuro UX (sort indicator)

**Veredicto**: `confidence: float` SE expone en SuggestionDTO. FE actual lo ignora (chips ya ordenadas server-side). Reservado para futuro UX (highlight top chip, debug panel).

**Razón**: Cero costo agregado (4 bytes JSON). Forward-compat sin schema change.

### D-8: Locale — server-side default, no client-side

**Veredicto**: `SuggestionContext.locale` siempre `"es"`. NO exponer en request DTO (single locale producto today).

**Razón** (KISS, escalabilidad cuando aplique): Producto LATAM mono-locale. Cuando llegue multi-locale será Settings tenant-level (`TenantLocale` shared VO existente), no per-request param.

**Trade-off**: Sin override per-request. No requirement.

### D-9: Voice migration — adapter en FE (NO solo URL swap — shapes diferentes)

**Veredicto**: FE `voice-api.ts::transcribeAudio` mantiene firma actual (`TranscriptionResponse{text, language, duration_seconds}`) pero internamente:
1. Cambia URL a `/api/v1/copilot/voice/upload-and-transcribe`.
2. Adapta response: nuevo endpoint retorna `VoiceUploadAndTranscribeResponse{block: AudioBlock{transcript, transcript_language, duration_ms, ...}}` → mapear a `{text: block.transcript, language: block.transcript_language ?? "", duration_seconds: (block.duration_ms ?? 0) / 1000}`.

**Razón** (cero deuda + scope cerrado): PR.md líneas 34, 65 dicen "solo URL swap si shape compatible". Verificación real (voice.py:236, voice_dto.py:18-30) demuestra shapes INCOMPATIBLES. Adapter en FE preserva consumers (composer/voice button) sin tocarlos. Migración signature consumidor = scope creep no autorizado.

**Trade-off**: 5 líneas adapter logic en FE. Aceptable.

**Alternativa descartada A**: Refactorizar consumidores FE para usar AudioBlock — scope creep, fuera de PR.
**Alternativa descartada B**: Crear endpoint legacy-shape proxy en BE — duplica responsabilidad, deuda nueva.

### D-10: Best-effort everything — endpoint NUNCA throws sobre engine failure

**Veredicto**: `POST /suggestions` retorna 200 con `suggestions: []`, `breakdown: {}`, `latency_ms: <medido>` cuando engine falla internamente. structlog warning + sigue. SOLO 401/403 (auth), 422 (validation request).

**Razón** (UX + observability + criterio Chris #5): Smart-chips son enhancement, no critical path. Empty `[]` ya graceful en FE (`SuggestedChips.tsx:21` `if (chips.length === 0) return null`). Engine ya implementa best-effort interno (engine.py:86-92).

**Trade-off**: FE no puede distinguir "no chips applicable" vs "engine roto". Métrica en `copilot_trace_event(event_type='suggestion_shown', data->breakdown)` permite ops detectar provider failures.

### D-11: Event emission — siempre, incluso con `suggestions: []`

**Veredicto**: `SuggestionShown` event emitido SIEMPRE (incluso 0 chips). Permite tracking "cuántas oportunidades de chip hubo en total" para denominator de ratio adopción.

**Razón** (métricas honestas): Sin emitir 0-chip turns, ratio adopción se infla artificialmente.

### D-12: React Query key — incluye route + conversationId, NO recent_message_ids

**Veredicto**: `queryKey: ["copilot", "suggestions", tenantId, route, conversationId]`.

**Razón** (cache lifecycle correcto): `route` change → re-fetch (chips son route-scoped). `conversationId` change → re-fetch (provider futuro puede usar conv state). `recent_message_ids` y `incomplete_fields` van en body pero NO en key — se actualizan por componente padre (Composer) y disparan refetch cuando cambian via mutation invalidation manual.

**Trade-off**: Si `recent_message_ids` cambia mid-conversation y queremos refetch, hay que invalidar manualmente. Acceptable porque providers actuales (offer-only) no consumen este campo. Cuando llegue provider que sí lo use (PR-2), hook expone `refetch()` callable.

### D-13: Mutation `useSuggestionAccept` — fire-and-forget, NO invalida query

**Veredicto**: Mutation NO invalida `["copilot", "suggestions"]` query. Click chip → mutation dispara → user envía mensaje → next chip render usa cache existente hasta `staleTime` (5min).

**Razón** (UX correctness): Engine no re-rankea por accept (S1 D-28: heurístico, no LLM). Re-fetch sería desperdicio de roundtrip + UX flicker. Telemetría desacoplada del UI render.

### D-14: Cleanup deuda — DROP `SuggestedActions.tsx` ROUTE_SUGGESTIONS duplicado

**Veredicto**: `SuggestedActions.tsx` consume nuevo `useSuggestions()` (real). Block `ROUTE_SUGGESTIONS` map line 21-78 BORRADO completo.

**Razón** (cero deuda — criterio Chris #4): Después PR queda 0 hits `grep -rn "ROUTE_SUGGESTIONS" frontend/`. Audit verifica.

### D-15: NO nuevo anchor `[COPILOT-*]` — reusar `[COPILOT-SUGGESTIONS-ENGINE]`

**Veredicto**: Nuevo file `copilot/api/suggestions.py` + DTOs + tests usan anchor existente `# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md` en docstring header.

**Razón** (anchor budget 36/37 — cap del registry test_copilot_anchors.py:99): Bumpear cap requiere justificación commit. Reusar = cero impact al ratchet. La feature pertenece al mismo dominio conceptual.

### D-16: NO nuevo cross-module import (ratchet 22 frozen)

**Veredicto**: Nuevo router solo importa de `src.modules.copilot.*` + `src.modules.iam.api.dependencies` (auth) + `src.shared.*` (events bus). NADA NUEVO de otros módulos.

**Razón** (DDD ratchet): `test_no_new_copilot_module_imports.py` cap 22 frozen. Engine ya consume `shared/links/ports/offer.py` (ya en allowlist). Router NO accede directamente a otros módulos.

## 2. SQLAlchemy 2.0 Models

**No aplica.** PR no introduce tablas nuevas. Persistencia eventos vía `copilot_trace_event` (existente, escrito por subscriber `domain_subscribers.py`).

## 3. Pydantic v2 DTOs

```python
# backend/src/modules/copilot/api/suggestions_dto.py  (NEW FILE)
"""DTOs for the copilot suggestions API.

# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SuggestionsRequest(BaseModel):
    """Body for POST /api/v1/copilot/suggestions.

    Tenant scope viene del header X-Tenant-ID (Depends(get_tenant_context)).
    user_id viene de Depends(get_current_user). NO duplicar en body (D-6 PII).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    conversation_id: UUID | None = Field(
        default=None,
        description="ID de la conversación activa. None = pre-conversación (chips vacíos por default).",
    )
    current_route: str | None = Field(
        default=None,
        max_length=200,
        description="Slug de ruta FE: 'brand-studio', 'offer-studio/{uuid}', 'growth-studio', etc.",
    )
    recent_message_ids: list[UUID] = Field(
        default_factory=list,
        max_length=20,
        description="IDs de últimos mensajes del turn (forward-compat providers LLM-driven). Cap=20.",
    )
    incomplete_fields: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Field paths incompletos (ej. 'promise.headline'). Cap=50 evita payloads abusivos.",
    )


class SuggestionDTO(BaseModel):
    """Single smart-chip surfaced to FE.

    Mirror del Suggestion domain (suggestion.py:44) MINUS source_module + metadata
    (D-6: PII allowlist — provider internals not exposed to FE).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str = Field(max_length=60, description="Texto visible (Spanish neutro LatAm).")
    prompt: str = Field(description="Texto que se inserta en el composer al click.")
    confidence: float = Field(ge=0.0, le=1.0, description="Heurístico 0..1 (D-7).")
    category: str = Field(description="Mirror StrEnum SuggestionCategory: 'followup'|'action'|'clarify'|'nav'.")


class SuggestionsResponse(BaseModel):
    """Response of POST /api/v1/copilot/suggestions."""

    model_config = ConfigDict(from_attributes=True)

    suggestions: list[SuggestionDTO] = Field(
        description="Ordered desc por confidence. Capped a 5 (engine._DEFAULT_MAX_TOTAL)."
    )
    breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="provider_id -> count (telemetría agregada, NOT per-chip).",
    )
    latency_ms: int = Field(ge=0, description="Engine latency medido (excluye HTTP overhead).")


class SuggestionAcceptRequest(BaseModel):
    """Body for POST /api/v1/copilot/suggestions/accept (fire-and-forget)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    suggestion_id: UUID = Field(description="ID de la chip clickeada.")
    conversation_id: UUID | None = Field(
        default=None,
        description="Conv activa al click. None si user clickeó pre-conversación.",
    )
    current_route: str | None = Field(
        default=None,
        max_length=200,
        description="Ruta al momento del click (telemetría correlación).",
    )
    category: str = Field(
        max_length=20,
        description="Category de la suggestion (echo del SuggestionDTO.category).",
    )
    source_module: str = Field(
        max_length=50,
        description="Provider id de la suggestion (echo necesario porque API NO devuelve por-chip — D-6). FE conoce desde breakdown context.",
    )
    accepted_at: datetime = Field(description="ISO 8601 UTC. FE genera client-side.")


class SuggestionAcceptResponse(BaseModel):
    """Response of POST /accept (best-effort 202)."""

    model_config = ConfigDict(from_attributes=True)

    ok: bool = Field(description="True si event publicó al bus. False = warning interno; FE ignora.")
```

**NOTA D-6 enmendada**: `source_module` NO se expone per-chip en `SuggestionDTO`, pero FE necesita echarlo de vuelta en `accept` para que el subscriber lo persista (`on_suggestion_accepted` usa `name_key="source_module"`). Solución: FE conoce el `source_module` por contexto de breakdown (provider único activo en route) o, si futuro multi-provider per-route, agregar en próximo iter. Para PR-1 con OfferSuggestionProvider único en `offer-studio*`, FE puede inferir desde breakdown. **Decisión cerrada**: SuggestionDTO incluye `source_module` (override D-6 parcial), JUSTIFICADO por necesidad funcional accept event, NO PII (string corto provider_id).

### Override D-6 (final): SuggestionDTO incluye `source_module`

```python
class SuggestionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str = Field(max_length=60)
    prompt: str
    confidence: float = Field(ge=0.0, le=1.0)
    category: str  # SuggestionCategory.value
    source_module: str = Field(
        max_length=50,
        description="Provider id (echo necesario para accept event — NOT PII, es slug interno).",
    )
    # metadata sigue EXCLUIDO (puede contener URLs/IDs internos)
```

Revisión auditor PII: `source_module` ∈ {`offer`, `brand`, `sales_agent`, `copilot`} — todos slugs públicos, no PII. OK.

## 4. API Routes

| Method | Path | Auth | Tenant | Request DTO | response_model | Status codes | Idempotency |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/copilot/suggestions` | Bearer Clerk | X-Tenant-ID req | `SuggestionsRequest` | `SuggestionsResponse` | 200, 401, 422 | read-only semánticamente |
| POST | `/api/v1/copilot/suggestions/accept` | Bearer Clerk | X-Tenant-ID req | `SuggestionAcceptRequest` | `SuggestionAcceptResponse` | 202, 401, 422 | at-least-once OK (D-5) |

### Skeleton `backend/src/modules/copilot/api/suggestions.py`

```python
"""Smart-chip suggestions API (composer hint engine).

# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md

Two endpoints:
- POST /suggestions       — fetch ranked chips (best-effort: returns [] on engine failure)
- POST /suggestions/accept — telemetry producer (fire-and-forget, at-least-once OK)
"""

from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID, uuid4

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
from src.modules.iam.domain.user import User
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,
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
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
) -> SuggestionsResponse:
    """Devuelve hasta 5 chips ordenadas por confidence descendente.

    Best-effort: si engine falla retorna `suggestions=[]` (D-10). NUNCA 5xx por
    engine internal failure.
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    ctx = SuggestionContext(
        tenant_id=tenant_id,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        current_route=request.current_route,
        recent_message_ids=tuple(request.recent_message_ids),
        incomplete_fields=tuple(request.incomplete_fields),
        locale="es",
    )

    engine = get_default_engine()
    try:
        # D-3: engine es sync — wrap to_thread evita bloquear event loop
        suggestions, breakdown, latency_ms = await asyncio.to_thread(
            engine.get_suggestions, ctx
        )
    except Exception as exc:  # noqa: BLE001 — best-effort (D-10)
        logger.warning(
            "suggestions_engine_failed",
            tenant_id=str(tenant_id),
            current_route=request.current_route,
            error=str(exc),
        )
        suggestions, breakdown, latency_ms = [], {}, 0

    # D-11: emite SuggestionShown SIEMPRE (incluso 0 chips)
    try:
        EventBus.publish(
            SuggestionShown.create(
                tenant_id=tenant_id,
                user_id=current_user.id,
                conversation_id=request.conversation_id,
                current_route=request.current_route,
                suggestion_ids=[s.id for s in suggestions],
                provider_breakdown=breakdown,
                latency_ms=latency_ms,
            ),
            session=None,
        )
    except Exception as exc:  # noqa: BLE001 — telemetry resilience
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
    summary="Reportar que el user clickeó una chip (telemetría)",
)
async def accept_suggestion(
    request: SuggestionAcceptRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
) -> SuggestionAcceptResponse:
    """Fire-and-forget producer del SuggestionAccepted event.

    Best-effort: bus failure → log warning + return ok=False. FE ignora response.
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    try:
        EventBus.publish(
            SuggestionAccepted.create(
                tenant_id=tenant_id,
                user_id=current_user.id,
                conversation_id=request.conversation_id,
                suggestion_id=request.suggestion_id,
                source_module=request.source_module,
                category=request.category,
            ),
            session=None,
        )
        return SuggestionAcceptResponse(ok=True)
    except Exception as exc:  # noqa: BLE001 — telemetry resilience
        logger.warning(
            "suggestion_accepted_publish_failed",
            tenant_id=str(tenant_id),
            suggestion_id=str(request.suggestion_id),
            error=str(exc),
        )
        return SuggestionAcceptResponse(ok=False)
```

### Wiring `main.py`

Append (después de `copilot_voice` block, antes de `# 7. CRM`):

```python
# Append to imports block (after copilot_voice import line 90):
from src.modules.copilot.api import suggestions as copilot_suggestions

# Append to router registration block (after copilot_plan registration):
app.include_router(
    copilot_suggestions.router,
    prefix="/api/v1/copilot",
    tags=["Copilot - Suggestions"],
    dependencies=[Depends(get_tenant_context)],
)
```

## 5. TypeScript Types (Frontend)

```ts
// frontend/src/features/copilot/types/suggestions.ts  (EXTEND existing file)
// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md

// MIRROR backend SuggestionDTO + endpoints DTOs.
// snake_case en wire (BE) → camelCase NO required aquí porque consumimos JSON literal
// y mapeamos a Suggestion existente shape (FE locked desde S1 PR-2).

export type SuggestionCategory = "followup" | "action" | "clarify" | "nav";

export interface Suggestion {
  id: string;            // UUID (BE serializa string)
  label: string;
  prompt: string;
  confidence?: number;   // ahora SIEMPRE viene del BE (era opcional para stub)
  category?: SuggestionCategory;
  source_module?: string; // nuevo — necesario para accept event payload
}

export interface SuggestionsRequest {
  conversation_id?: string | null;
  current_route?: string | null;
  recent_message_ids?: string[];
  incomplete_fields?: string[];
}

export interface SuggestionsResponse {
  suggestions: Suggestion[];
  breakdown: Record<string, number>;  // provider_id -> count
  latency_ms: number;
}

export interface SuggestionAcceptRequest {
  suggestion_id: string;
  conversation_id?: string | null;
  current_route?: string | null;
  category: SuggestionCategory;
  source_module: string;
  accepted_at: string;  // ISO 8601 UTC
}

export interface SuggestionAcceptResponse {
  ok: boolean;
}

// Legacy stub type SuggestionsPayload (S1) DEPRECATED — drop with hook rewrite.
```

## 6. FE wiring contract

### `frontend/src/features/copilot/api/suggestions-api.ts` (NEW FILE)

```ts
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  SuggestionAcceptRequest,
  SuggestionAcceptResponse,
  SuggestionsRequest,
  SuggestionsResponse,
} from "../types/suggestions";

const BASE = `${config.api.baseUrl}/api/v1/copilot`;

export async function fetchSuggestions(
  token: string,
  body: SuggestionsRequest,
): Promise<SuggestionsResponse> {
  const response = await fetchClient(`${BASE}/suggestions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    // Best-effort: don't throw; return empty (D-10 mirror). 401 is the only hard fail.
    if (response.status === 401) throw new Error("Unauthorized");
    return { suggestions: [], breakdown: {}, latency_ms: 0 };
  }

  return response.json() as Promise<SuggestionsResponse>;
}

export async function acceptSuggestion(
  token: string,
  body: SuggestionAcceptRequest,
): Promise<SuggestionAcceptResponse> {
  const response = await fetchClient(`${BASE}/suggestions/accept`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    // Fire-and-forget: never throw upstream. Telemetry failure ≠ user-facing error.
    return { ok: false };
  }

  return response.json() as Promise<SuggestionAcceptResponse>;
}
```

### `frontend/src/features/copilot/hooks/use-suggestions.ts` (REWRITE — drop ROUTE_SUGGESTIONS)

```ts
"use client";

// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchSuggestions } from "../api/suggestions-api";
import { useCopilotStore } from "../store/copilot-store";

import type { Suggestion } from "../types/suggestions";

export interface UseSuggestionsReturn {
  chips: Suggestion[];
  isLoading: boolean;
  refetch: () => void;
}

/**
 * Smart-chips dinámicas desde BE engine (S1 PR-2 + S2 PR-1).
 * Cache 5min staleTime — chips son route-scoped + raramente cambian.
 */
export function useSuggestions(): UseSuggestionsReturn {
  const { getToken } = useAuth();
  const currentRoute = useCopilotStore((s) => s.currentRoute);
  const conversationId = useCopilotStore((s) => s.conversationId);

  const query = useQuery<{ suggestions: Suggestion[] }>({
    queryKey: ["copilot", "suggestions", currentRoute, conversationId],
    enabled: true, // siempre activo; engine retorna [] cuando route es null/unknown
    staleTime: 5 * 60 * 1000,        // 5 min (D-12)
    gcTime: 10 * 60 * 1000,          // 10 min
    retry: false,                     // best-effort, no retry; engine ya retorna []
    queryFn: async () => {
      const token = await getToken();
      if (!token) return { suggestions: [] };
      const response = await fetchSuggestions(token, {
        current_route: currentRoute,
        conversation_id: conversationId,
        recent_message_ids: [],
        incomplete_fields: [],
      });
      return { suggestions: response.suggestions };
    },
  });

  return {
    chips: query.data?.suggestions ?? [],
    isLoading: query.isLoading,
    refetch: () => void query.refetch(),
  };
}
```

### `frontend/src/features/copilot/hooks/use-suggestion-accept.ts` (NEW FILE)

```ts
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation } from "@tanstack/react-query";

import { acceptSuggestion } from "../api/suggestions-api";

import type { Suggestion } from "../types/suggestions";

interface AcceptArgs {
  suggestion: Suggestion;
  conversationId: string | null;
  currentRoute: string | null;
}

/**
 * Fire-and-forget producer of SuggestionAccepted telemetry event.
 * NO query invalidation (D-13).
 */
export function useSuggestionAccept() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async ({ suggestion, conversationId, currentRoute }: AcceptArgs) => {
      const token = await getToken();
      if (!token) return { ok: false };
      return acceptSuggestion(token, {
        suggestion_id: suggestion.id,
        conversation_id: conversationId,
        current_route: currentRoute,
        category: suggestion.category ?? "action",
        source_module: suggestion.source_module ?? "",
        accepted_at: new Date().toISOString(),
      });
    },
    onError: (error) => {
      // Telemetry failure: log but never surface to user.
      console.warn("[copilot] suggestion accept telemetry failed", error);
    },
  });
}
```

### `frontend/src/features/copilot/components/composer/SuggestedChips.tsx` (MODIFY)

```ts
// Cambio mínimo: agregar accept call al onClick.
"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useSuggestionAccept } from "../../hooks/use-suggestion-accept";
import { useSuggestions } from "../../hooks/use-suggestions";
import { useCopilotStore } from "../../store/copilot-store";

interface SuggestedChipsProps {
  onChipClick: (prompt: string) => void;
  className?: string;
}

export function SuggestedChips({ onChipClick, className }: SuggestedChipsProps) {
  const { chips, isLoading } = useSuggestions();
  const accept = useSuggestionAccept();
  const currentRoute = useCopilotStore((s) => s.currentRoute);
  const conversationId = useCopilotStore((s) => s.conversationId);

  if (isLoading || chips.length === 0) return null;

  return (
    <div className={cn("relative", className)} aria-label="Sugerencias de preguntas">
      <div className="flex gap-2 overflow-x-auto px-1 py-1 scrollbar-hide" style={/* ... */}>
        {chips.map((chip) => (
          <Button
            key={chip.id}
            variant="outline"
            size="sm"
            onClick={() => {
              accept.mutate({ suggestion: chip, conversationId, currentRoute });
              onChipClick(chip.prompt);
            }}
            className="shrink-0 rounded-full text-xs whitespace-nowrap h-7 px-3"
            type="button"
          >
            {chip.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

SuggestedChips.displayName = "SuggestedChips";
```

### `frontend/src/features/copilot/components/SuggestedActions.tsx` (MODIFY — drop ROUTE_SUGGESTIONS)

Cambios:
1. **DELETE** lines 21-78 (`ROUTE_SUGGESTIONS` map + `getSuggestionsForRoute`).
2. **DELETE** local `interface SuggestedAction`.
3. Reemplazar consumer:
   ```ts
   import { useSuggestions } from "../hooks/use-suggestions";
   import { useSuggestionAccept } from "../hooks/use-suggestion-accept";

   export function SuggestedActions() {
     const { chips } = useSuggestions();
     const accept = useSuggestionAccept();
     const currentRoute = useCopilotStore((s) => s.currentRoute);
     const conversationId = useCopilotStore((s) => s.conversationId);
     const messages = useCopilotStore((s) => s.messages);
     const { sendMessage } = useCopilotChat();
     const { getToken } = useAuth();

     // ... existing render logic, mapping chips → buttons
     // onClick: accept.mutate({...}) THEN sendMessage(chip.prompt)
   }
   ```

### `frontend/src/features/copilot/api/voice-api.ts` (MODIFY — D-9 adapter)

```ts
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface TranscriptionResponse {
  text: string;
  language: string;
  duration_seconds: number;
}

// Internal shape de /upload-and-transcribe (mirror VoiceUploadAndTranscribeResponse)
interface UploadAndTranscribeResponse {
  block: {
    id: string;
    asset_id: string;
    url: string;
    mime: string;
    duration_ms?: number | null;
    transcript: string;
    transcript_language?: string | null;
  };
}

export async function transcribeAudio(
  audioBlob: Blob,
  token: string,
): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");

  // D-9: URL swap + adapter (shapes diferentes — verified contra voice.py:236)
  const response = await fetchClient(
    `${API_URL}/api/v1/copilot/voice/upload-and-transcribe`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Transcription failed (${response.status}): ${errorText}`);
  }

  const payload = (await response.json()) as UploadAndTranscribeResponse;
  return {
    text: payload.block.transcript,
    language: payload.block.transcript_language ?? "",
    duration_seconds: (payload.block.duration_ms ?? 0) / 1000,
  };
}
```

## 7. Repository Interfaces

**No aplica.** Engine + providers ya existen (S1). Subscriber persiste vía `TraceEventRepository` (existente). Sin nuevos repos.

## 8. Application Services

**No aplica directamente** — endpoint llama engine vía `get_default_engine()` directamente (mismo patrón que `chat.py` orquesta, no agrega service wrapper innecesario). Si futuro requiere service wrapper (ej. para integrar BudgetGuard PR-2 PI-1), refactor incremental.

## 9. Agentic Surfaces

**No aplica.** PR no toca LangGraph state, tools, prompts, traces. Solo expone engine REST + emite domain events que subscriber existente persiste.

## 10. Migration Notes

**No aplica.** Cero migrations DB. Cero schema changes. Persistencia eventos vía tabla existente `copilot_trace_event`.

## 11. File Structure

### NEW (BE)
```
backend/src/modules/copilot/api/
├── suggestions.py              # NEW — router (2 endpoints)
└── suggestions_dto.py          # NEW — Pydantic v2 DTOs

backend/tests/modules/copilot/api/
├── test_suggestions_endpoint.py            # NEW — 6 test cases (TDD RED first)
├── test_suggestions_accept_endpoint.py     # NEW — 4 test cases
└── test_suggestions_endpoint_integration.py # NEW — e2e con OfferSuggestionProvider
```

### MODIFIED (BE)
```
backend/src/main.py             # +2 lines: import + include_router
```

### NEW (FE)
```
frontend/src/features/copilot/api/
└── suggestions-api.ts                      # NEW — fetchSuggestions + acceptSuggestion

frontend/src/features/copilot/hooks/
└── use-suggestion-accept.ts                # NEW — mutation hook

frontend/src/features/copilot/hooks/__tests__/
├── use-suggestions.test.ts                 # NEW — React Query hook tests
├── use-suggestion-accept.test.ts           # NEW
└── use-voice-api.test.ts                   # NEW — adapter shape verification

frontend/src/features/copilot/components/composer/__tests__/
└── SuggestedChips.test.tsx                 # NEW — render + click → mutation
```

### MODIFIED (FE)
```
frontend/src/features/copilot/types/suggestions.ts            # extend (add request/response types)
frontend/src/features/copilot/hooks/use-suggestions.ts        # rewrite (drop ROUTE_SUGGESTIONS, use React Query)
frontend/src/features/copilot/api/voice-api.ts                # URL swap + adapter
frontend/src/features/copilot/components/composer/SuggestedChips.tsx  # wire mutation
frontend/src/features/copilot/components/SuggestedActions.tsx # drop ROUTE_SUGGESTIONS dup
```

## 12. Cross-Cutting Concerns

| Concern | Aplicación |
|---|---|
| **Tenant isolation** | `Depends(get_tenant_context)` en ambos endpoints + `dependencies=[]` en router include. `tenant_id` REQUIRED — 401 si missing. SuggestionContext.tenant_id pasado a cada provider. |
| **Currency** | N/A (no monetary fields) |
| **Master data** | `accepted_at: datetime` ISO 8601 UTC. FE genera con `new Date().toISOString()` (UTC garantizado). BE Pydantic validates aware datetime. |
| **Spanish neutro LatAm** | DTO descriptions, FastAPI `summary=`, error messages, structlog event names en es-LA neutro (ej. "Obtener smart-chips dinámicas"). |
| **PII allowlist** | `response_model=` mandatory en ambos. SuggestionDTO excluye `metadata` (puede tener URLs internas). `source_module` justificado D-6 override (slug interno público). |
| **Native-first dev** | `cd backend && .venv/bin/pytest tests/modules/copilot/api/test_suggestions*.py`. `cd frontend && npx vitest run src/features/copilot/`. NUNCA `docker exec`. |
| **structlog, no print** | `logger = structlog.get_logger()` con kwargs `tenant_id=str(...)`. Event names snake_case. |
| **No hardcoded values** | Engine cap 5 (`_DEFAULT_MAX_TOTAL`), staleTime 5min — ambos en su SSoT respectivo. |

## 13. Architecture Fitness Impact

| Test | Impact | Acción builder |
|---|---|---|
| `tests/architecture/test_api_contracts.py` | Verifica `response_model=` presente. **Pass** garantizado por contrato. | N/A — declarado en route decorator |
| `tests/architecture/test_copilot_anchors.py` | Cap 36/37 — reusar `[COPILOT-SUGGESTIONS-ENGINE]`. **NO bumpear cap.** | Builder usa anchor existente, no agrega ANCHOR_REGISTRY entry |
| `tests/architecture/test_no_new_copilot_module_imports.py` | Ratchet 22 frozen. PR NO agrega cross-module imports nuevos. | Builder verifica con `make arch-test` post-implementación |
| `tests/architecture/test_copilot_provider_compliance.py` | Provider pattern intact (no nuevos providers PR-1) | Pass automático |
| `tests/architecture/test_copilot_registry.py` | Engine registry intact | Pass automático |
| `tests/architecture/test_redirect_slashes.py` (si existe) | `FastAPI(redirect_slashes=False)` mantenido | N/A — no toca main.py FastAPI() init |

**Allowlist shrinkage**: ninguna posible este PR (sin ratchets shrinkable tocados).

## 14. pm-nico/current-state Updates Required

`docs/pm-nico/current-state/copilot.md`:

1. **Update cap "Smart-chips live"** (sección "Capacidades actuales" alrededor línea 86):
   - Cambiar "BE motor live, FE consumiendo stub aun" → "BE motor live + API endpoint POST /suggestions live + FE React Query consume real engine"
2. **Append new cap "Voice migration done"**:
   ```md
   ### Cap: Voice transcription FE migration completa
   - Introducida: PR-1 (PI-2, S2, 2026-04-30)
   - Estado: live
   - Operable copilot: indirecto (voice-to-text input chat)
   - Cambio: FE migra de legacy `/voice/transcribe` (410 Gone desde S1 PR-1) → `/voice/upload-and-transcribe` (combined upload+STT atómico)
   - Adapter FE preserva consumers (TranscriptionResponse shape backwards-compat)
   ```
3. **Append new cap "Smart-chips telemetría adopción"**:
   ```md
   ### Cap: Smart-chips telemetría producer
   - Introducida: PR-1 (PI-2, S2, 2026-04-30)
   - Estado: live
   - Operable copilot: indirecto (clicks chips alimentan métricas adopción)
   - Eventos: `SuggestionShown` (siempre, incluso 0 chips) + `SuggestionAccepted` (on click)
   - Métrica adopción: query `copilot_trace_event WHERE event_type IN ('suggestion_shown','suggestion_accepted')`
   - SQL ratio: COUNT(DISTINCT suggestion_id) FILTER (event_type='accepted') / COUNT(DISTINCT) FILTER (event_type='shown')
   ```

PM (no builder) ejecuta este update post-merge.

## 15. Test Surfaces (TDD-mandatory — RED first per layer)

### Backend (pytest, Python 3.12)

**`backend/tests/modules/copilot/api/test_suggestions_endpoint.py`** (≥6 test cases):

| # | Test | Verifica |
|---|---|---|
| 1 | `test_suggestions_happy_path_returns_chips` | OfferSuggestionProvider mockeado retorna 3 chips → response 200 + suggestions length 3 + breakdown {"offer": 3} + latency_ms >= 0 |
| 2 | `test_suggestions_empty_engine_returns_empty_200` | Engine retorna [] → 200 + suggestions=[] (D-10) |
| 3 | `test_suggestions_engine_exception_returns_empty_200` | Engine raises → 200 + suggestions=[] + structlog warning emitido (D-10) |
| 4 | `test_suggestions_missing_tenant_header_returns_401` | Sin X-Tenant-ID → 401 |
| 5 | `test_suggestions_emits_shown_event_always` | Mock EventBus.publish → assert called con SuggestionShown (incluso 0 chips, D-11) |
| 6 | `test_suggestions_invalid_route_too_long_returns_422` | route con 201 chars → 422 (Pydantic max_length) |
| 7 | `test_suggestions_response_excludes_metadata` | Engine retorna chip con metadata → response NO contiene `metadata` field (D-6 PII) |
| 8 | `test_suggestions_response_model_is_declared` | grep route definition → `response_model=SuggestionsResponse` presente |

**`backend/tests/modules/copilot/api/test_suggestions_accept_endpoint.py`** (≥4 test cases):

| # | Test | Verifica |
|---|---|---|
| 1 | `test_accept_happy_path_returns_202_ok_true` | Body válido → 202 + ok=True + EventBus.publish llamado con SuggestionAccepted |
| 2 | `test_accept_invalid_uuid_returns_422` | suggestion_id no UUID → 422 |
| 3 | `test_accept_missing_tenant_returns_401` | Sin X-Tenant-ID → 401 |
| 4 | `test_accept_event_publish_failure_returns_ok_false` | Mock EventBus raises → 202 + ok=False + warning logged |
| 5 | `test_accept_publishes_event_with_correct_payload` | Verificar campos del SuggestionAccepted event match request |

**`backend/tests/modules/copilot/api/test_suggestions_endpoint_integration.py`** (e2e):

| # | Test | Verifica |
|---|---|---|
| 1 | `test_e2e_real_engine_real_offer_provider` | Tenant con 0 offers, route="offer-studio" → response contains "Crea tu primera oferta" chip |
| 2 | `test_e2e_subscriber_writes_trace_event_on_accept` | POST /accept → query `copilot_trace_event WHERE event_type='suggestion_accepted' AND data->>'suggestion_id'=...` retorna 1 row |
| 3 | `test_e2e_subscriber_writes_trace_event_on_shown` | POST /suggestions con engine devuelve chips → query trace_event event_type='suggestion_shown' → 1 row |

### Frontend (Vitest)

**`frontend/src/features/copilot/hooks/__tests__/use-suggestions.test.ts`** (≥4):

| # | Test | Verifica |
|---|---|---|
| 1 | `returns chips from API on success` | mock fetch → hook returns `{chips: [...], isLoading: false}` |
| 2 | `returns empty chips on API failure (graceful)` | mock fetch error → returns `{chips: [], isLoading: false}` (no throw) |
| 3 | `re-fetches when currentRoute changes` | trigger route change in store → React Query key invalidates → new fetch |
| 4 | `re-fetches when conversationId changes` | trigger conv change → new fetch |
| 5 | `does not throw without auth token` | getToken returns null → returns empty chips |

**`frontend/src/features/copilot/hooks/__tests__/use-suggestion-accept.test.ts`** (≥3):

| # | Test | Verifica |
|---|---|---|
| 1 | `mutation calls acceptSuggestion API` | mock acceptSuggestion → mutate({...}) → API called with correct body |
| 2 | `mutation does NOT invalidate suggestions query` | spy on queryClient.invalidateQueries → never called for `["copilot", "suggestions"]` (D-13) |
| 3 | `mutation onError logs warning, does not throw` | API throws → mutation onError handler → console.warn called, no rethrow |

**`frontend/src/features/copilot/api/__tests__/voice-api.test.ts`** (≥3):

| # | Test | Verifica |
|---|---|---|
| 1 | `posts to /upload-and-transcribe URL` | spy fetch → URL contains `/voice/upload-and-transcribe` |
| 2 | `adapts new shape to legacy TranscriptionResponse` | mock response `{block: {transcript: "hola", transcript_language: "es", duration_ms: 5000}}` → returned `{text: "hola", language: "es", duration_seconds: 5}` |
| 3 | `handles missing optional fields gracefully` | mock `{block: {transcript: "hi", duration_ms: null, transcript_language: null}}` → returns `{text: "hi", language: "", duration_seconds: 0}` |

**`frontend/src/features/copilot/components/composer/__tests__/SuggestedChips.test.tsx`** (≥3):

| # | Test | Verifica |
|---|---|---|
| 1 | `renders chips from useSuggestions hook` | mock hook returning 3 chips → renders 3 buttons |
| 2 | `returns null when no chips` | mock hook returning `[]` → component returns null |
| 3 | `clicking chip fires accept mutation AND onChipClick` | spy mutate + spy onChipClick → both called with correct args |

### E2E (Playwright)

No nuevo smoke test obligatorio — feature consume composer existente (smoke ya cubre composer interactions). Auditor verifica voice flow no regresiona corriendo smoke existente.

## 16. Performance Budget

| Surface | Budget | Medición |
|---|---|---|
| `POST /suggestions` p99 BE | <50ms (engine + serialización) | OfferSuggestionProvider _compute mide ~5ms p50 con 10 offers (S1 baseline) |
| `POST /suggestions/accept` p99 BE | <30ms (event publish fire-and-forget) | Bus publish ~1-3ms in-process |
| TTFT FE chips render cold | <300ms (network + auth + engine + react-query mount) | Acceptable for non-critical-path UX |
| TTFT FE chips render hot (cache) | <50ms (React Query staleTime hit, no network) | Cero network cost |
| Engine concurrency | 1000+ tenants concurrent OK | asyncio.to_thread default pool 40 workers + engine sync ~5ms = ~8000 req/s teórico |

## 17. Out of Scope (CONTRACT lock)

- LLM-based ranking de suggestions (defer S3+ si métricas adopción <5%)
- Tabla persistencia dedicada `suggestion` rows (mantener `copilot_trace_event` hasta volumen >1M/día)
- Migrar voice endpoint signature shape end-to-end (FE consumers usar AudioBlock directo) — deuda explícita NO autorizada
- Nuevos providers (BrandSuggestionProvider, SalesAgentSuggestionProvider, CopilotSuggestionProvider) — son PR-2
- Idempotency-Key header / Redis dedup tabla — at-least-once OK (D-5)
- Streaming SSE de chips — endpoint REST simple (D-1)
- Wire `BudgetGuard.check` pre-engine — engine no es LLM call, no aplica gate

## 18. Rollback Plan

| Surface | Rollback |
|---|---|
| Endpoints BE nuevos | Additive — sin feature flag necesario. Si bug crítico: `git revert` del commit BE → router NOT registered → 404 → FE useSuggestions retorna `[]` graceful (D-10 mirror FE). |
| FE useSuggestions rewrite | Si rompe: `git revert` FE commit → ROUTE_SUGGESTIONS map vuelve, comportamiento stub previo. |
| FE voice-api URL swap | Si rompe: `git revert` voice-api commit → llama `/voice/transcribe` que retorna 410 → user verá error claro (no silencioso) — exactamente el estado pre-PR. Más hace evidente la regresión que oculta. |

## 19. Research Notes

Sin patterns nuevos. Todo decision backed por:
- Stack existente (FastAPI async + React Query + Pydantic v2 + structlog) — patterns establecidos en `conversations.py`, `voice.py`, `chat.py`
- Skill `copilot-expert` cap rules + best-effort observability + ratchet status
- Skill `frontend-expert` FSD-Lite + React Query patterns
- `.tessl/.../pii-sanitisation.md` — `response_model=` allowlist enforcement
- `.claude/rules/tdd-mandatory.md` — RED tests precede GREEN per layer
- Verificación directa de código pre-existente (no hipótesis):
  - voice.py:236 — confirmed shape diferente legacy
  - engine.py:62 — confirmed sync (no async)
  - events.py:194,228 — events ya definidos, sin emitter
  - domain_subscribers.py:106-107 — subscribers ya wired
  - test_copilot_anchors.py:99 — cap 37 (current 36)

## 20. Builder Execution Plan

Builders BE + FE pueden ejecutar EN PARALELO porque:
1. BE shape (DTOs + endpoints) está 100% especificado.
2. FE shape (TS types + hooks) mirror exacto del BE.
3. Cero shared file conflict potencial (BE modifica `main.py` 2 lines, FE modifica files distintos).

Auto-loop audit:
1. BE builder: implementa `suggestions_dto.py` + `suggestions.py` + tests → corre `cd backend && .venv/bin/pytest tests/modules/copilot/api/test_suggestions*.py tests/architecture/ -x -q` → green → commit `feat(copilot-api): add suggestions endpoints`.
2. FE builder: implementa `suggestions-api.ts` + hooks + tests + voice adapter + components mod → corre `cd frontend && npx vitest run src/features/copilot/ && npx tsc --noEmit && npx eslint src/features/copilot/` → green → commit `feat(copilot-fe): wire real suggestions engine + voice migration`.
3. Auditor BE: verifica response_model declarado, tenant_id filter, anchor reusado, ratchet sin bumpeo.
4. Auditor FE: verifica grep `ROUTE_SUGGESTIONS` = 0 hits, grep `voice/transcribe` = 0 hits (legacy URL), tests cobertura ≥80% nuevos files.

## Open Questions for PM

**ZERO.** Architect-empowered. Todas las decisiones tomadas y justificadas en §1.

---

<!-- @pm: CONTRACT.md ready (architect-empowered). -->
