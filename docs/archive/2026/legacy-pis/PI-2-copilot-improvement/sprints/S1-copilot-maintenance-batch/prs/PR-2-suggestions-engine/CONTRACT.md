# CONTRACT — PR-2-suggestions-engine

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend builders consumen este archivo. FE cards = PR siguiente (este PR es BE-only motor).

## 0. Context Summary

| Campo | Valor |
|---|---|
| PR | PI-2 / S1-copilot-maintenance-batch / PR-2-suggestions-engine |
| Modules afectados | `modules/copilot/{domain,application,observability}` (BE-only) |
| Skills consultados | `copilot-expert` (decisiones: best-effort observability, registry pattern à la `block_adapters.py`, dominio puro, `_subscribe_once` idempotente, ratchet 22 frozen NO se toca, anchor `COPILOT-SUGGESTIONS-ENGINE` ya registrado en línea 26 de `test_copilot_anchors.py`) |
| pm-nico/current-state afectados | `docs/pm-nico/current-state/copilot.md` — append capability "Suggestion engine + provider registry (BE motor)" + lineage |
| Arch gates que deben seguir verdes | `test_copilot_anchors.py`, `test_no_new_copilot_module_imports.py` (ratchet 22 — **NO grow**), `test_copilot_provider_compliance.py`, `test_copilot_registry.py`, `test_ddd_boundaries.py`, `test_domain_purity.py`, `test_api_contracts.py` (si añadimos endpoint), `test_pii_sanitization_coverage_*` |
| Anchor SSoT | `COPILOT-SUGGESTIONS-ENGINE` → `docs/domains/copilot/suggestions-engine.md` (existente, doc estado FE-stub describe Option A heuristic backend = lo que construimos) |

## 1. Decisiones diferidas resueltas (PR.md §"Decisiones diferidas")

| # | Pregunta | Decisión architect | Justificación |
|---|---|---|---|
| 1 | ¿Score ranking con LLM o heurística simple? | **Heurística simple** (default `score = base_priority * boost_route * boost_freshness`, todos en `[0,1]`) | PR.md default + research doc 2026-04-29 #1 ("válida pero requiere arq propia + discovery"). Latencia <10ms p99, costo cero. LLM ranking → backlog PI-2 S2+ si la heurística no alcanza. |
| 2 | Persistencia de suggestions accepted | **Reusar `copilot_trace_event`** con `event_type="suggestion_shown" / "suggestion_accepted"` y subscriber idempotente | Ya hay infra (recorder + sanitization + best-effort try/except patrón). Tabla nueva = migración, schema nuevo, retention nuevo, dashboard nuevo — premature. Cuando ML feedback loop llegue (PI-2 S2+), si volumen lo justifica, migración a tabla dedicada con backfill desde `copilot_trace_event` filtered. Ratchet observability: **single recorder writes** — no segundo writer. |
| 3 | Single provider este PR (offer)? | **Confirmado: solo `OfferSuggestionProvider`** | PR.md scope explícito. Brand/copilot/sales_agent providers = PRs siguientes. Engine + interface + registry + 1 provider concreto + observability hook = walking skeleton mínimo cohesivo. |

## 2. Domain entities (nuevas o modificadas)

> Capa pura — sin imports de framework, infra, ni `langchain`. Solo `dataclasses`, `enum`, `typing`, `uuid`, `decimal`. Cumple `test_domain_purity.py`.

### 2.1 `modules/copilot/domain/suggestion.py` (NUEVO)

```python
"""Domain value objects for copilot suggestion engine.

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class SuggestionCategory(StrEnum):
    """Mirrors FE locked TS union: "followup" | "action" | "clarify" | "nav".

    SSoT — `frontend/src/features/copilot/types/suggestions.ts:Suggestion.category`.
    """

    FOLLOWUP = "followup"
    ACTION = "action"
    CLARIFY = "clarify"
    NAV = "nav"


@dataclass(frozen=True, slots=True)
class SuggestionContext:
    """Runtime input the engine dispatches to providers.

    Tenant-scoped. ``current_route`` is the FE route slug (``brand-studio``,
    ``offer-studio/{id}``, …). ``recent_message_ids`` enables future LLM-driven
    providers (PI-2 S2+) without breaking interface; heuristic providers ignore.
    """

    tenant_id: UUID
    user_id: UUID | None
    conversation_id: UUID | None
    current_route: str | None
    recent_message_ids: tuple[UUID, ...] = ()
    incomplete_fields: tuple[str, ...] = ()
    locale: str = "es"


@dataclass(frozen=True, slots=True)
class Suggestion:
    """Smart-chip surfaced under chat input.

    Shape MIRRORS FE locked contract (`frontend/.../types/suggestions.ts`):
      - id (UUID, stable within turn)
      - label (≤60 chars, español neutro LatAm)
      - prompt (filled into input on click)
      - confidence ∈ [0,1] (heuristic score; renamed to `confidence` in API DTO)
      - category (SuggestionCategory)

    Domain extension fields (NOT exposed in API to FE):
      - source_module (which provider produced it; for telemetry)
      - metadata (provider-private payload; sanitized before persistence)
    """

    id: UUID = field(default_factory=uuid4)
    label: str = ""
    prompt: str = ""
    confidence: float = 0.0
    category: SuggestionCategory = SuggestionCategory.ACTION
    source_module: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Domain invariants — fail fast if provider produces garbage
        if not (0.0 <= self.confidence <= 1.0):
            msg = f"confidence must be in [0,1], got {self.confidence}"
            raise ValueError(msg)
        if len(self.label) > 60:
            msg = f"label exceeds 60 chars: {self.label[:60]}…"
            raise ValueError(msg)
        if not self.label.strip() or not self.prompt.strip():
            msg = "label and prompt are required"
            raise ValueError(msg)
```

### 2.2 `modules/copilot/domain/events.py` (MODIFICADO — append-only)

Añadir 2 dataclasses + 2 literales junto al patrón existente (`TurnStarted`, `CardEmitted`):

```python
EVENT_SUGGESTION_SHOWN: str = "copilot_suggestion_shown"
EVENT_SUGGESTION_ACCEPTED: str = "copilot_suggestion_accepted"


@dataclass
class SuggestionShown(DomainEvent):
    """Emitted when ``SuggestionEngine.get_suggestions(...)`` returns ≥1 chip."""

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        conversation_id: UUID | None,
        current_route: str | None,
        suggestion_ids: list[UUID],
        provider_breakdown: dict[str, int],   # {provider_id: count}
        latency_ms: int,
    ) -> SuggestionShown:
        return cls(
            event_name=EVENT_SUGGESTION_SHOWN,
            tenant_id=tenant_id,
            payload={
                "user_id": _str_or_none(user_id),
                "conversation_id": _str_or_none(conversation_id),
                "current_route": current_route,
                "suggestion_ids": [_str_or_none(sid) for sid in suggestion_ids],
                "provider_breakdown": dict(provider_breakdown),
                "latency_ms": int(latency_ms),
            },
        )


@dataclass
class SuggestionAccepted(DomainEvent):
    """Emitted when API receives ``POST /suggestions/{id}/accept`` (FE click chip)."""

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        conversation_id: UUID | None,
        suggestion_id: UUID,
        source_module: str,
        category: str,
    ) -> SuggestionAccepted:
        return cls(
            event_name=EVENT_SUGGESTION_ACCEPTED,
            tenant_id=tenant_id,
            payload={
                "user_id": _str_or_none(user_id),
                "conversation_id": _str_or_none(conversation_id),
                "suggestion_id": _str_or_none(suggestion_id),
                "source_module": source_module,
                "category": category,
            },
        )
```

Update `__all__` to include the 4 new symbols.

## 3. Application — engine + provider interface + registry

### 3.1 `modules/copilot/application/suggestions/__init__.py` (NUEVO)

Public API ergonomics:

```python
from src.modules.copilot.application.suggestions.engine import SuggestionEngine
from src.modules.copilot.application.suggestions.providers.base import SuggestionProvider
from src.modules.copilot.application.suggestions.registry import (
    get_default_engine,
    register_provider,
)

__all__ = [
    "SuggestionEngine",
    "SuggestionProvider",
    "get_default_engine",
    "register_provider",
]
```

### 3.2 `modules/copilot/application/suggestions/providers/base.py` (NUEVO)

```python
"""Provider port. Concrete providers live alongside in providers/."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.modules.copilot.domain.suggestion import Suggestion, SuggestionContext


@runtime_checkable
class SuggestionProvider(Protocol):
    """One module-scoped source of suggestions.

    Implementations MUST:
      - Be tenant-isolated (``ctx.tenant_id`` required by every read).
      - Be best-effort (catch internal exceptions; return ``[]`` on failure).
      - Return ≤``max_per_provider`` suggestions sorted by domain relevance.
      - Set ``source_module`` to a stable id matching ``module_id`` (e.g. ``"offer"``).
    """

    @property
    def provider_id(self) -> str:
        """Stable id used for telemetry breakdown (matches module_id)."""

    @property
    def applies_to_routes(self) -> tuple[str, ...]:
        """Route prefixes this provider activates on. Empty tuple = always."""

    def get_suggestions(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int = 5,
    ) -> list[Suggestion]:
        """Compute suggestions for ``ctx``. MUST NOT raise."""
```

### 3.3 `modules/copilot/application/suggestions/engine.py` (NUEVO)

```python
"""SuggestionEngine — composes providers, ranks, caps, emits telemetry.

Pure async-friendly orchestration. Heuristic ranking (no LLM call). Latency
target <10ms p99 with N≤6 providers. Best-effort observability — engine NEVER
raises; returns ``[]`` on internal failure and emits structlog warning.
"""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Iterable

import structlog

from src.modules.copilot.domain.suggestion import Suggestion, SuggestionContext
from src.modules.copilot.application.suggestions.providers.base import SuggestionProvider

logger = structlog.get_logger()

_DEFAULT_MAX_TOTAL = 5  # Mirrors FE locked contract (max 5 chips shown).
_DEFAULT_MAX_PER_PROVIDER = 5


class SuggestionEngine:
    """Composes registered providers into a ranked list of suggestions."""

    def __init__(
        self,
        providers: Iterable[SuggestionProvider] | None = None,
        *,
        max_total: int = _DEFAULT_MAX_TOTAL,
        max_per_provider: int = _DEFAULT_MAX_PER_PROVIDER,
    ) -> None:
        self._providers: list[SuggestionProvider] = list(providers or [])
        self._max_total = max_total
        self._max_per_provider = max_per_provider

    def register(self, provider: SuggestionProvider) -> None:
        """Idempotent — registering the same ``provider_id`` twice is a no-op.

        Mirrors ``orchestrator/block_adapters.py::register_block_handler``
        ValueError-on-conflict pattern: same id + different instance = bug.
        """
        existing = next((p for p in self._providers if p.provider_id == provider.provider_id), None)
        if existing is provider:
            return
        if existing is not None:
            msg = f"provider_id={provider.provider_id!r} already registered with a different instance"
            raise ValueError(msg)
        self._providers.append(provider)

    def get_suggestions(
        self,
        ctx: SuggestionContext,
    ) -> tuple[list[Suggestion], dict[str, int], int]:
        """Compose, rank, cap. Returns (suggestions, provider_breakdown, latency_ms).

        Caller is responsible for emitting ``SuggestionShown`` event with the
        returned breakdown + latency. Engine is tenant-isolated through
        ``ctx.tenant_id`` — providers MUST use it on every read.
        """
        t0 = time.monotonic()
        collected: list[Suggestion] = []
        breakdown: Counter[str] = Counter()

        for provider in self._providers:
            if provider.applies_to_routes and ctx.current_route is not None:
                if not any(ctx.current_route.startswith(p) for p in provider.applies_to_routes):
                    continue
            try:
                items = provider.get_suggestions(ctx, max_per_provider=self._max_per_provider)
            except Exception as exc:  # noqa: BLE001 — best-effort; never break caller
                logger.warning(
                    "suggestion_provider_failed",
                    provider_id=provider.provider_id,
                    tenant_id=str(ctx.tenant_id),
                    error=str(exc),
                )
                continue
            collected.extend(items)
            breakdown[provider.provider_id] += len(items)

        # Heuristic global rank: confidence desc, then provider order (stable).
        collected.sort(key=lambda s: s.confidence, reverse=True)
        latency_ms = int((time.monotonic() - t0) * 1000)
        return collected[: self._max_total], dict(breakdown), latency_ms
```

### 3.4 `modules/copilot/application/suggestions/registry.py` (NUEVO)

Process-singleton engine + bootstrap. Mirrors `block_adapters.py` registration timing (import-time).

```python
"""Default engine registration — bootstrap providers at module import.

Wired from ``application/discovery.py`` startup hook OR lazy-init on first
``get_default_engine()`` call (tests opt for lazy via ``_reset_for_tests``).
"""

from __future__ import annotations

from threading import Lock

from src.modules.copilot.application.suggestions.engine import SuggestionEngine
from src.modules.copilot.application.suggestions.providers.base import SuggestionProvider

_engine: SuggestionEngine | None = None
_engine_lock = Lock()


def get_default_engine() -> SuggestionEngine:
    """Return the process-wide engine. Lazy-init on first access.

    Bootstrap registers built-in providers (``OfferSuggestionProvider``).
    External plugins register via ``register_provider(...)``.
    """
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = SuggestionEngine()
                _bootstrap_builtin(_engine)
    return _engine


def register_provider(provider: SuggestionProvider) -> None:
    """Register a provider on the default engine."""
    get_default_engine().register(provider)


def _bootstrap_builtin(engine: SuggestionEngine) -> None:
    """Register the providers shipped in this PR. Future PRs append here."""
    from src.modules.copilot.application.suggestions.providers.offer import (
        OfferSuggestionProvider,
    )
    engine.register(OfferSuggestionProvider())


def _reset_for_tests() -> None:
    """Test-only — restart the lazy singleton between tests."""
    global _engine
    with _engine_lock:
        _engine = None
```

### 3.5 `modules/copilot/application/suggestions/providers/offer.py` (NUEVO)

```python
"""OfferSuggestionProvider — heuristic, route-scoped, tenant-isolated.

Reads offer state via ``shared/links/ports/offer.py`` (cross-module read goes
through the existing port — does NOT introduce a new entry in
``test_no_new_copilot_module_imports.py::KNOWN_COPILOT_TO_MODULE_IMPORTS`` since
``copilot -> offer`` already exists for ``offer_section_tools.py`` / ``offer_fields.py``).

Heuristic rules (initial set; expand in future PRs):
 1. Route ``offer-studio`` (no offer_id) → "Crea una oferta"
 2. Route ``offer-studio/{id}`` → preset-flag-driven:
    - ``HIGH_TICKET`` → "Sugiere 3-tier pricing"
    - ``RECURRING_BILLING`` → "Configura facturación recurrente"
    - ``IS_LEAD_MAGNET`` → "Vincula con oferta core"
 3. ``incomplete_fields`` includes ``promise.headline`` → "Genera variantes de promesa"

Confidence scoring (deterministic, ∈ [0,1]):
    base_priority (0.5–0.9) * route_match_boost (1.0 if exact, 0.7 if prefix)
    * freshness_decay (1.0 always — heuristic provider, no time decay yet)

Cross-module reads:
    - ``get_offer_repository(db).get_all_by_tenant(tenant_id)``
    - ``get_offer_type_preset(preset_id)`` → ``default_flags``
"""
```

Public class shape:

```python
class OfferSuggestionProvider:
    @property
    def provider_id(self) -> str: return "offer"

    @property
    def applies_to_routes(self) -> tuple[str, ...]: return ("offer-studio",)

    def get_suggestions(
        self, ctx: SuggestionContext, *, max_per_provider: int = 5,
    ) -> list[Suggestion]:
        # Open SessionLocal() (sync — same pattern as offer_section_tools.py).
        # Wrap whole body in try/except → return [] on failure.
        # Always pass ctx.tenant_id to repo calls.
        ...
```

### 3.6 `modules/copilot/application/tools/offer_section_tools.py` (MODIFICADO — minimal)

**Decision (resolves ambiguity in PR.md walking skeleton step 5):** the static `suggestions=[...]` lists inside individual tool outputs (`adapt_from_brand_identity`, `adapt_from_brand_narrative`, etc.) are tool-result `suggestions[]` strings rendered as in-card hints — they are **NOT** the same surface as smart-chip Suggestions for the FE composer. Refactoring those would change tool contract and require regenerating goldens.

This PR's refactor is **additive**: extract the existing `_offer_preset_flags` helper into a private read-side service consumed BOTH by the existing tools AND by `OfferSuggestionProvider`, so we don't duplicate the cross-module read. No tool signatures change. Tool tests stay green unchanged.

Concretely:
- New file `modules/copilot/application/services/offer_suggestion_reader.py` (helpers extracted; pure read, tenant-scoped).
- `offer_section_tools.py` rewires `_offer_preset_flags` to delegate to the new service (1-line change inside the helper). Public function names + behavior preserved.
- `OfferSuggestionProvider` consumes the same service.

If PM intent was "delete those static `suggestions=[...]` strings" → flag in §16 Open Questions.

## 4. Observability — domain subscribers

> Pattern: copilot publishes domain event → observability subscriber persists into ``copilot_trace_event``. Subscriber is best-effort + idempotent registration.

### 4.1 `modules/copilot/observability/recording/domain_subscribers.py` (MODIFICADO — append-only)

Add inside existing `register_subscribers(...)`:

```python
def on_suggestion_shown(event: DomainEvent) -> None:
    _persist(event, event_type="suggestion_shown", name_key="current_route")

def on_suggestion_accepted(event: DomainEvent) -> None:
    _persist(event, event_type="suggestion_accepted", name_key="source_module")

_subscribe_once(EVENT_SUGGESTION_SHOWN, on_suggestion_shown)
_subscribe_once(EVENT_SUGGESTION_ACCEPTED, on_suggestion_accepted)
```

`_persist` already wraps with try/except + structlog warning + best-effort commit + `sanitize_payload(...)` — reuse without modification.

`event_type` values fit the existing `String(32)` column (`"suggestion_shown"`=16 chars, `"suggestion_accepted"`=19 chars — under cap).

### 4.2 Trace-event row shape

| Column | Value for `suggestion_shown` |
|---|---|
| `event_type` | `"suggestion_shown"` |
| `name` | `current_route` (e.g. `"offer-studio"`, truncated 128 chars) |
| `data` | `{"suggestion_ids": [...], "provider_breakdown": {...}, "latency_ms": int}` (sanitized) |
| `tenant_id` | from event |
| `turn_id` | falls back to `tenant_id` per existing `_persist` logic (suggestions outside turn lifecycle) |
| `status` | `"ok"` |

| Column | Value for `suggestion_accepted` |
|---|---|
| `event_type` | `"suggestion_accepted"` |
| `name` | `source_module` (e.g. `"offer"`) |
| `data` | `{"suggestion_id": "...", "category": "..."}` |

## 5. API endpoints

> **NO new HTTP endpoints in this PR** (BE-only motor). FE consumes via stub hook today; FE swap to real engine = PR siguiente.
>
> Forward-looking shape (NOT IMPLEMENTED THIS PR — included only so builders + future FE PR keep contract stable):

| Method | Path | Auth | Request | response_model | Status | Notes |
|---|---|---|---|---|---|---|
| (future) GET | `/api/v1/copilot/suggestions` | Bearer + X-Tenant-ID | query: `conversation_id?`, `current_route?` | `SuggestionsResponseDTO` | 200 | Drives `useSuggestions()` real impl |
| (future) POST | `/api/v1/copilot/suggestions/{suggestion_id}/accept` | Bearer + X-Tenant-ID | `SuggestionAcceptDTO` | `SuggestionAcceptResponseDTO` | 202 | Emits `SuggestionAccepted` event |

Future DTOs (Pydantic v2, `model_config = ConfigDict(from_attributes=True)`):

```python
class SuggestionDTO(BaseModel):
    """Mirrors FE locked TS interface verbatim."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    label: str
    prompt: str
    confidence: float | None = None
    category: Literal["followup", "action", "clarify", "nav"]


class SuggestionsResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    conversation_id: UUID | None
    suggestions: list[SuggestionDTO]
    generated_at: datetime  # UTC, tz-aware


class SuggestionAcceptDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    conversation_id: UUID | None = None


class SuggestionAcceptResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    accepted: bool
    suggestion_id: UUID
```

PII review: `label`, `prompt` are tenant-authored hints — not PII. `source_module`, `metadata` excluded from API DTO (kept domain-internal). Compliant with `pii-sanitisation.md`.

## 6. DB schema

> **NO migration this PR.**
>
> `copilot_trace_event` table reused as-is (already at migration `085_copilot_tenant_limits` head). New `event_type` literal values ``"suggestion_shown"`` / ``"suggestion_accepted"`` fit existing `String(32)` constraint.
>
> If future analytics demand dedicated table → PI-2 S2+ migration `086_copilot_suggestion_event` would derive shape from existing `copilot_trace_event` rows (single-direction backfill).

## 7. Repository interfaces

> **No new repos.** Engine + providers consume:
>  - `shared/links/ports/offer.get_offer_repository(db)` (existing)
>  - `shared/links/ports/offer.get_offer_type_preset(preset_id)` (existing)
>  - `observability.persistence.trace_event_repository.TraceEventRepository` (existing — read for tests; subscriber writes)
>
> All take `tenant_id` on every method call (regla `tenant-isolation.md`).

## 8. Application services

`modules/copilot/application/services/offer_suggestion_reader.py` (NUEVO):

```python
"""Read-side helper: offer preset flags + incomplete signals for suggestions.

Tenant-scoped. Pure read. No mutation, no transaction boundary.
Consumed by ``offer_section_tools.py`` (existing) AND ``OfferSuggestionProvider`` (new).
"""

class OfferSuggestionReader:
    def __init__(self, db: Session, *, tenant_id: UUID) -> None: ...

    def get_preset_flags(self, offer_id: UUID | None) -> list[str]: ...

    def list_offers(self) -> list[OfferRowVO]: ...   # frozen dataclass, no SQLA leaking

    def detect_lead_magnet_without_core(self) -> bool: ...   # heuristic for #3 above
```

## 9. Eventos / outbox

| Event name | Payload (sanitized) | Producer | Consumer |
|---|---|---|---|
| `copilot_suggestion_shown` | `current_route, suggestion_ids[], provider_breakdown, latency_ms` | (future) API endpoint AFTER `engine.get_suggestions(...)` succeeds | `domain_subscribers.on_suggestion_shown` → `copilot_trace_event(event_type="suggestion_shown")` |
| `copilot_suggestion_accepted` | `suggestion_id, source_module, category` | (future) API endpoint POST `/accept` handler | `domain_subscribers.on_suggestion_accepted` → `copilot_trace_event(event_type="suggestion_accepted")` |

**Outbox flag:** events flow through `EventBusAdapter` (`shared/domain_events/outbox/...`). When `USE_OUTBOX_PATTERN_COPILOT=ON`, both events route to `domain_event_outbox` (PI-1 S0 PR-1 Sub-E migration ya hecha). This PR does NOT toggle the flag — it inherits whatever default copilot already uses.

**Engine emission timing:** because no API endpoint lands in this PR, the engine returns `(suggestions, breakdown, latency_ms)` and **the future API handler** publishes the event. This PR ships unit tests that exercise emission via a fake handler — pattern matches existing test in `test_persist_emitted_blocks.py`.

## 10. Retry / idempotency policy

| Surface | Policy |
|---|---|
| Engine `get_suggestions` | Idempotent; pure function of `(tenant_id, route, message_ids, fields)`. No retry; on exception inside provider → swallowed + logged + `[]`. |
| Subscriber writes | Best-effort (existing `_persist` pattern). Failure → structlog warning, no retry. |
| Provider registration | Idempotent — same `(provider_id, instance)` re-registration = no-op. Different instance with same id = `ValueError` (caught at startup, surfaces as boot failure to admin). |
| Future `POST /accept` | Idempotency key = `suggestion_id` (UUID stable per turn). Duplicate `POST` on same `suggestion_id` returns `accepted=True` and emits at most one event (subscriber dedup via `suggestion_id` + `tenant_id` natural key — implementor adds in PR siguiente). |

## 11. Tenant isolation

- `SuggestionContext.tenant_id` is mandatory (UUID, no default).
- Every `OfferSuggestionReader` query filters `tenant_id` (regla `tenant-isolation.md`).
- Cross-tenant leak protection: provider `get_suggestions` opens its own `SessionLocal()` and closes in `finally` (mirrors `offer_section_tools.py` pattern). Engine never holds DB sessions.
- Trace events inherit `tenant_id` from `DomainEvent.tenant_id` (subscriber persists into `copilot_trace_event.tenant_id` column).
- (Future) API endpoint resolves `tenant_id` from `X-Tenant-ID` header via existing middleware.

## 12. File structure

```
backend/src/modules/copilot/
├── domain/
│   ├── suggestion.py                                 NEW — value objects
│   └── events.py                                     MODIFIED — +SuggestionShown/Accepted
├── application/
│   ├── suggestions/                                  NEW package
│   │   ├── __init__.py                               NEW
│   │   ├── engine.py                                 NEW — SuggestionEngine
│   │   ├── registry.py                               NEW — get_default_engine + register
│   │   └── providers/
│   │       ├── __init__.py                           NEW
│   │       ├── base.py                               NEW — SuggestionProvider Protocol
│   │       └── offer.py                              NEW — OfferSuggestionProvider
│   ├── services/
│   │   └── offer_suggestion_reader.py                NEW — shared reader (offer)
│   └── tools/
│       └── offer_section_tools.py                    MODIFIED (1 helper delegates to reader)
└── observability/
    └── recording/
        └── domain_subscribers.py                     MODIFIED — +2 subscribers

backend/tests/modules/copilot/suggestions/           NEW carpeta
├── __init__.py
├── test_engine_register_provider.py
├── test_engine_score_ranking.py
├── test_offer_suggestion_provider.py
├── test_offer_section_tools_consumes_reader.py
└── test_suggestion_event_recorded.py
```

No FE changes. No frontend FSD slots touched.

## 13. Cross-cutting concerns

| Concern | Decision |
|---|---|
| **Tenant isolation** | `SuggestionContext.tenant_id` mandatory. Every read passes it. (§11) |
| **Currency** | N/A — no monetary fields in `Suggestion`. |
| **Master data** | `SuggestionsResponseDTO.generated_at` uses `DateTime(timezone=True)`-style tz-aware datetime (regla `master-data.md`). FE renders via `formatTenantDate*()` if surfaced (this PR no FE). |
| **Spanish neutro LatAm** | `Suggestion.label` + `prompt` MUST be neutro (sin voseo). `OfferSuggestionProvider` initial chips: "Crea una oferta", "Sugiere 3-tier pricing", "Configura facturación recurrente", "Vincula con oferta core", "Genera variantes de promesa". Voseo-sweep test in `tests/modules/copilot/suggestions/test_offer_suggestion_provider.py::test_no_voseo`. |
| **PII** | `Suggestion.metadata` sanitized via `sanitize_payload(...)` before subscriber writes to `copilot_trace_event.data`. `label`+`prompt` are tenant-authored copy, no PII patterns. Future API DTO (§5) excludes `metadata` and `source_module` from response model — allowlist enforced by `test_api_contracts.py::response_model required` when endpoint lands. |
| **Native-first dev** | `cd backend && .venv/bin/pytest tests/modules/copilot/suggestions/ -v` + `.venv/bin/ruff check src/modules/copilot/`. NEVER `docker exec`. |
| **`structlog` only** | Engine + provider use `structlog.get_logger()`. NO `print` / `logging`. (regla `backend-ddd.md`). |
| **Domain purity** | `domain/suggestion.py` — only `dataclasses`, `enum`, `typing`, `uuid`. Test `test_domain_purity.py` enforces. |
| **Best-effort observability** | Engine catches provider exceptions; subscriber catches DB exceptions. Both log warning, never raise. (regla `copilot-observability.md`). |
| **No `Any`/raw dicts** | `metadata: dict[str, Any]` allowed (provider-private); API DTOs explicit fields. |

## 14. Architecture fitness impact

| Test | Effect | Action |
|---|---|---|
| `test_copilot_anchors.py` | `COPILOT-SUGGESTIONS-ENGINE` already in registry (line 26). Cap 36 pre-existing — stays. | No change. |
| `test_no_new_copilot_module_imports.py` | Ratchet 22 frozen. New `OfferSuggestionProvider` imports through `shared/links/ports/offer.py` (existing port — already counted in `copilot -> offer | copilot/...` entries). | **No new ratchet entry.** Builder MUST verify by running `pytest tests/architecture/test_no_new_copilot_module_imports.py -v` after implementation. |
| `test_copilot_provider_compliance.py` | Suggestion engine NOT a `CopilotProvider` (it's an internal application service, not a module-level provider). Test unaffected. | No change. |
| `test_copilot_registry.py` | Module registry untouched. | No change. |
| `test_ddd_boundaries.py` | `application/suggestions/` consumes `domain/suggestion.py` (allowed) + `shared/links/ports/offer` (allowed). | No change. |
| `test_domain_purity.py` | `domain/suggestion.py` — pure stdlib only. | Builder runs to confirm. |
| `test_api_contracts.py` | No endpoint added → no `response_model` check applies this PR. | No change. |
| `test_pii_sanitization_coverage_*` | New trace events flow through existing `_persist` → `sanitize_payload(...)`. | No new allowlist entry needed. |

**Allowlist updates expected:** none. Allowlists may shrink (no new violations); this PR neither grows nor shrinks them.

## 15. pm-nico/current-state updates required

`docs/pm-nico/current-state/copilot.md` — append to `## Capacidades actuales`:

```
- **Suggestion engine + provider registry** (BE motor): heuristic ranking, route-scoped providers, observability via copilot_trace_event(event_type=suggestion_shown|suggestion_accepted). Inicial: OfferSuggestionProvider (preset-flag-driven). Surface FE smart-chips = PR siguiente (FE swap del stub `useSuggestions`).
  - Introducida: PR-2 (PI-2, S1)
  - Estado: BE motor live, FE consumiendo stub aún
  - Operable copilot: indirecto (alimenta smart chips bajo input chat)
```

Append decisión a `docs/pm-nico/pis/active/PI-2-copilot-improvement/decisions.md` con score-ranking heurística + reuso de `copilot_trace_event` + scope single provider.

## 16. Test surfaces (TDD-mandatory)

> RED → GREEN per layer. Builder WRITES tests FIRST per regla `tdd-mandatory.md`.

### Domain (RED first)
- `tests/modules/copilot/suggestions/test_suggestion_value_object.py` — `Suggestion` invariants (confidence ∈ [0,1], label ≤60 chars, label/prompt non-empty raise `ValueError`).
- (Existing) `test_copilot_events_invariants` — extend with `SuggestionShown.create()` / `SuggestionAccepted.create()` payload shape.

### Application (RED before engine code)
- `test_engine_register_provider.py` — register, no-op idempotent, ValueError on conflict.
- `test_engine_score_ranking.py` — multiple providers, confidence desc, max_total cap, max_per_provider cap.
- `test_engine_handles_provider_exception.py` — provider raises → engine returns other providers' suggestions, logs warning, doesn't propagate.
- `test_engine_route_filter.py` — `applies_to_routes` filters out non-matching routes.

### Infrastructure / cross-module (RED before provider impl)
- `test_offer_suggestion_provider.py`:
  - `test_no_offers_returns_create_chip` (route `offer-studio`, empty offers → 1 suggestion `"Crea una oferta"`).
  - `test_high_ticket_flag_yields_pricing_chip`.
  - `test_recurring_billing_flag_yields_subscription_chip`.
  - `test_lead_magnet_without_core_yields_link_chip`.
  - `test_tenant_isolation` (offers from another tenant → ignored).
  - `test_no_voseo` (regex `_VOSEO_RE` over labels+prompts).
  - `test_provider_returns_empty_on_db_failure` (mock SessionLocal raise → `[]` + warning).

### Observability (RED before subscriber wiring)
- `test_suggestion_event_recorded.py`:
  - `EVENT_SUGGESTION_SHOWN` published → row in `copilot_trace_event` with `event_type="suggestion_shown"`, `name=current_route`, `data` sanitized.
  - `EVENT_SUGGESTION_ACCEPTED` published → row with `event_type="suggestion_accepted"`.
  - DB write fails → publishing succeeds, structlog warning emitted, NO exception bubbles out.

### Refactor preservation (no behavior change)
- `test_offer_section_tools_consumes_reader.py` — verify `_offer_preset_flags` returns same result before/after delegation refactor (snapshot via existing `tests/modules/copilot/test_offer_section_tools.py` mocks).

### Architecture gates (verify post-impl)
- `pytest tests/architecture/test_no_new_copilot_module_imports.py -v` (ratchet 22).
- `pytest tests/architecture/test_copilot_anchors.py -v` (anchor budget 36).
- `pytest tests/architecture/test_domain_purity.py -v`.

### E2E
- N/A (no endpoint, no FE) — E2E vendrá en PR siguiente FE swap.

## 17. Research notes

| Source | Date | Takeaway | Why over alternatives |
|---|---|---|---|
| `docs/domains/copilot/suggestions-engine.md` | existing (pre-PR) | Doc describes Option A (heuristic backend) as one of three real-engine options. Hook surface FE locked. | Aligns BE motor with FE locked contract → zero churn when FE swaps. |
| `docs/pm-nico/research/2026-04-29-copilot-8-recommendations.md` | 2026-04-29 | Item #1 confirmed as DO-S2-propio: "válida pero requiere arq propia + discovery". | Validates this PR's scope as discovery + walking skeleton. |
| `frontend/src/features/copilot/types/suggestions.ts` | locked | TS shape `Suggestion = {id, label, prompt, confidence?, category?}` — domain VO mirrors. | FE locked → BE conforms. |
| `backend/src/modules/copilot/application/orchestrator/block_adapters.py` | existing | Registry-pattern reference (handler registration with ValueError-on-conflict). | Same pattern reused for `SuggestionEngine.register` — consistency. |
| `copilot-expert` skill — "Pattern: Best-effort observability" | always | Recorder never breaks turn (try/except + structlog warning + rollback). | Engine + subscriber use same pattern. |

No new external dependencies. No `pluggy`-style plugin lib (PR.md research already discarded — registry manual ~50 LOC). No LLM ranking lib (postpone).

## 18. Resolved questions (2026-04-29 — PM Chris decisions)

Criterio decisión: pocos clientes ahora, miles pronto. Costo arquitectura correcta ahora < deuda futura. PM eligió "build-right-once" en cada caso.

| # | Question | Decisión PM | Razón |
|---|---|---|---|
| 1 | Refactor `offer_section_tools.py` additive vs expansion | **EXPANSION** — eliminar tool-result `suggestions[]` static (lines 200-215, 270-292), reemplazar con `engine.get_suggestions(context)` call. Goldens deben actualizarse. | Static = SSoT divergente que crece con providers. A escala = bug surface (engine vs static drift). Engine SSoT desde día 1. Deuda goldens ahora < deuda divergencia después. |
| 2 | `SuggestionAccepted` ship sin producer | **SHIP forward-compat** — subscriber best-effort + event class listos en este PR. FE migration PR solo agrega producer (`POST /copilot/suggestions/accept` o similar). | Métricas accept-rate disponibles desde día 1 cuando FE swap. Costo subscriber dummy bajo, beneficio observability inmediato cuando FE land. Patrón ya validado (`EVENT_CARD_EMITTED`). |
| 3 | Provider tie-breaker confidence igual | **EXPLICIT WEIGHT** — registry guarda `provider_priority: int = 0` per provider. Tie-break: confidence DESC, then `provider_priority` DESC, then registration order. | Orden registro opaco frágil cuando lleguen brand/copilot/sales_agent providers. Peso explícito = transparente, A/B-testable, configurable per tenant futuro sin refactor registry. |
| 4 | Doc `suggestions-engine.md` update | **BUILDER UPDATES en este PR** — atomic con código. Doc refleja "Option A IMPLEMENTED" + colapsa Opciones B/C a "future". | Docs co-located con código + builder tiene contexto fresco. Post-merge se olvida. |

---

<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-2 architect done" para review. -->
