# Suggestions Engine

Smart chips under the chat input. **Option A (heuristic backend) is IMPLEMENTED** as of PR-2 (PI-2 S1).

Anchor: `[COPILOT-SUGGESTIONS-ENGINE]`.

---

## Status: Option A IMPLEMENTED (PR-2, PI-2 S1)

The BE motor is live. FE still consumes the stub `useSuggestions` hook.
FE swap = next PR (PR siguiente, swaps stub to real GET endpoint).

### What shipped (PR-2)

- `SuggestionEngine` — process-singleton that composes registered providers, ranks
  by confidence DESC → provider_priority DESC → registration order, caps at 5 total.
- `SuggestionProvider` Protocol — port for module-scoped sources.
- `OfferSuggestionProvider` — heuristic, route-scoped (`offer-studio`), reads via
  `OfferSuggestionReader` (shared with `offer_section_tools`).
- `registry.py` — `get_default_engine()` lazy-init + `_reset_for_tests()`.
- Domain events `SuggestionShown` / `SuggestionAccepted` + subscribers in
  `domain_subscribers.py` → persisted to `copilot_trace_event`.
- `OfferSuggestionReader` — read-only offer state reader (tenant-scoped).
- 50 tests, 0 new mypy errors, 649 arch tests pass.

### What is NOT shipped yet (FE next PR)

- GET `/api/v1/copilot/suggestions` endpoint.
- POST `/api/v1/copilot/suggestions/{id}/accept` endpoint.
- FE `useSuggestions` swap from stub to real engine.

---

## Contract (stable across stub → real engine)

```typescript
export interface Suggestion {
  id: string;                           // stable UUID
  label: string;                        // user-visible, Spanish neutro LatAm, <=60 chars
  prompt: string;                       // filled into input on click
  confidence?: number;                  // 0..1
  category?: "followup" | "action" | "clarify" | "nav";
}

export function useSuggestions(conversationId: string | null): {
  suggestions: Suggestion[];
  isLoading: boolean;
  refresh: () => void;
};
```

The hook MUST:
- Return <=5 suggestions (FE renders max 5 chips).
- Be idempotent on repeated calls with the same `conversationId`.
- Expose `refresh()` to force re-compute (e.g., after a message send).

---

## Architecture

```
SuggestionEngine (process-singleton, application/suggestions/engine.py)
  |
  +-- register(SuggestionProvider) — idempotent, ValueError on id conflict
  |
  +-- get_suggestions(SuggestionContext)
        -> (list[Suggestion], breakdown: dict[str, int], latency_ms: int)
           |
           Ranking: confidence DESC -> provider_priority DESC -> registration order
           Cap: max_total=5, max_per_provider=5

Providers (application/suggestions/providers/):
  base.py      — SuggestionProvider Protocol (runtime_checkable)
  offer.py     — OfferSuggestionProvider (route: offer-studio, priority=0)

Registry (application/suggestions/registry.py):
  get_default_engine() -> SuggestionEngine (lazy singleton)
  register_provider(p)  -> delegates to default engine
  _reset_for_tests()    -> resets singleton (test isolation)

Reader (application/services/offer_suggestion_reader.py):
  OfferSuggestionReader(db, tenant_id=...)
    .list_offers() -> list[OfferRowVO]
    .get_preset_flags(offer_id) -> list[str]
    .detect_lead_magnet_without_core() -> bool

Domain events (domain/events.py):
  SuggestionShown.create(...) -> EVENT_SUGGESTION_SHOWN
  SuggestionAccepted.create(...) -> EVENT_SUGGESTION_ACCEPTED

Subscribers (observability/recording/domain_subscribers.py):
  on_suggestion_shown  -> copilot_trace_event(event_type="suggestion_shown")
  on_suggestion_accepted -> copilot_trace_event(event_type="suggestion_accepted")
```

---

## OfferSuggestionProvider heuristic rules

| Rule | Trigger | Suggestion |
|---|---|---|
| 1 | Route `offer-studio`, no offers | "Crea tu primera oferta" (confidence 0.85) |
| 2a | Route `offer-studio/{id}`, flag `high_ticket` | "Sugiere estructura de 3 niveles de pricing" (0.82) |
| 2b | Route `offer-studio/{id}`, flag `recurring_billing` | "Configura la facturacion recurrente" (0.80) |
| 2c | Route `offer-studio/{id}`, flag `is_lead_magnet` | "Vincula con oferta core" (0.78) |
| 3 | `incomplete_fields` includes `promise.headline` | "Genera variantes de promesa principal" (0.75) |
| 4 | Lead magnet offer exists, no core offer | "Vincula tu lead magnet con una oferta core" (0.76) |

---

## Extending: adding a new provider

1. Create `application/suggestions/providers/{module}.py` implementing `SuggestionProvider`.
2. In `registry.py::_bootstrap_builtin(engine)`, add `engine.register(NewProvider())`.
3. Set `provider_priority: int` for deterministic tie-breaking.
4. Tests in `tests/modules/copilot/suggestions/test_{module}_suggestion_provider.py`.
5. No changes to `engine.py` or `registry.py` interface (closed for modification, open for extension).

---

## Future options (PI-2 S2+)

### Option B — tool-driven (LLM emits suggestions)

The LLM emits up to 5 `Suggestion` objects as response metadata in `message_end.metadata.suggestions`.
Higher context-awareness at token cost per message.

**Status:** not built. Backlog PI-2 S2+ if heuristic insufficient.

### Option C — new SSE event

After `done`, orchestrator emits `suggestions_ready` SSE event (post-hoc, no latency impact).

**Status:** not built. Backlog if Option B latency unacceptable.

### Hybrid (most likely long-term)

- Option A (heuristic) as default/fallback.
- Option B (LLM-driven) for brand audit / offer design routes.
- Option C (SSE async) if Option B latency causes UX issues.

---

## Observability

Trace events written to `copilot_trace_event` via existing subscriber pattern:

| event_type | name column | data JSONB |
|---|---|---|
| `suggestion_shown` | `current_route` | `{suggestion_ids, provider_breakdown, latency_ms}` |
| `suggestion_accepted` | `source_module` | `{suggestion_id, category}` |

Both are best-effort (DB failure -> structlog warning, no exception propagation).
PII: sanitized via `sanitize_payload()` before persist.

---

## See also

- `frontend/src/features/copilot/types/suggestions.ts` — FE locked TS interface (SSoT FE shape).
- `frontend/src/features/copilot/hooks/use-suggestions.ts` — stub hook (swap target for FE next PR).
- `CONTRACT.md` §18 — resolved design decisions (D1-D4).
- `IMPL-LOG.md` — implementation diary.
