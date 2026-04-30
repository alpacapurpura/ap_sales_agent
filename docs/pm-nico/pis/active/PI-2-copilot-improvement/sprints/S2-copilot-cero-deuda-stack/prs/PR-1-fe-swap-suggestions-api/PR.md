# PR-1-fe-swap-suggestions-api

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-fe-swap-suggestions-api |
| Sprint padre | S2-copilot-cero-deuda-stack |
| PI padre | PI-2-copilot-improvement |
| Estado | in-progress |
| Tipo | feature (cross-stack: BE endpoints + FE swap) |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | 2026-04-30 sesión PI-2 S2 (módulo copilot) |

## Problema (user-facing)

Smart-chips bajo input chat hoy son **estáticas hardcoded** (no responden a estado real del tenant). El motor BE suggestion engine + provider registry shipped S1 PR-2 está sin consumir desde FE. Adicionalmente, FE llama legacy `/voice/transcribe` que retorna `410 Gone` desde S1 PR-1 — **voice transcription rota en runtime**.

JTBD: "Cuando empiezo a usar Nicolify quiero que las sugerencias del copilot reflejen lo que necesito hoy según mi estado real (módulos vacíos, gaps cross-módulo), no chips genéricos."

## Outcome esperado

- **Voice transcription funciona end-to-end** (FE no hace llamados a endpoint deprecado).
- **Smart-chips dinámicas** reflejan motor BE: provider `OfferSuggestionProvider` (heurísticas live S1) + nuevos providers PR-2 cuando lleguen.
- **Producer event `SuggestionAccepted`** dispara cuando user clickea chip → BE subscriber graba en `copilot_trace_event` → métricas adopción smart-chips desde día 1.

Métrica medible: % de turnos que usuario acepta una smart-chip (`suggestion_accepted` / `suggestion_shown`). Baseline 0% (stub no emite eventos). Target post-PR: tracking funcional, cifra real visible en `copilot_trace_event`.

## Walking skeleton (mínimo viable cohesivo)

1. **BE endpoint `POST /api/v1/copilot/suggestions`** — recibe `{conversation_id, route, recent_message_ids[], incomplete_fields[]}`, retorna `{suggestions: Suggestion[], breakdown: {provider_id: count}, latency_ms: int}`. Tenant-scoped via `X-Tenant-ID`. Llama `engine.get_suggestions(ctx)`. Emite `SuggestionShown` event vía bus para observability. Best-effort: returns `[]` on internal failure.
2. **BE endpoint `POST /api/v1/copilot/suggestions/accept`** — recibe `{suggestion_id, conversation_id, route, accepted_at}`. Emite `SuggestionAccepted` event. Subscriber forward-compat S1 ya escribe en `copilot_trace_event`.
3. **FE `voice-api.ts`** — replace `/copilot/voice/transcribe` → `/copilot/voice/upload-and-transcribe` en línea 26. Verificar request shape sigue compatible (FormData con `file` field) o ajustar.
4. **FE `useSuggestions()`** — drop static `ROUTE_SUGGESTIONS` map. React Query hook llamando `POST /copilot/suggestions` con context (route, conversation_id desde store). Cache 5min stale-time. Empty `[]` graceful render (no chips visibles).
5. **FE hook nuevo `useSuggestionAccept()`** — mutation hook. `SuggestedChips.tsx` onClick chip → `accept.mutate({suggestion_id, ...})` → fire-and-forget (no UI blocking).
6. **FE `SuggestedActions.tsx`** — mismo refactor (consume hook real, drop ROUTE_SUGGESTIONS duplicado).

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Endpoint POST con body context | Cleanest semantics; recent_message_ids permite re-rank futuro; idempotente | Slightly más verbose que GET con query params | **ELEGIDA** — alineado con interface ya documentada en stub `use-suggestions.ts` line 9 |
| B — GET con query params solo | Simpler; cache-friendly browsers | No permite recent_message_ids ni incomplete_fields fácil; refactor cuando lleguen providers más complejos | descartada — deuda futura |
| C — SSE streaming chips | Real-time updates si state cambia mid-conversation | Sobre-engineered para 5 chips estáticas-por-snapshot; engine ya retorna lista | descartada — escala sin justificación |

## Validación técnica preliminar

- **Modules afectados:**
  - BE: `copilot/api/` (router nuevo o agregar a existente), `copilot/application/suggestions/` (engine ya existe), `shared/events/` (`SuggestionAccepted` ya class definido).
  - FE: `frontend/src/features/copilot/api/`, `frontend/src/features/copilot/hooks/`, `frontend/src/features/copilot/components/composer/`.
- **Blockers conocidos:** ninguno bloqueante. PR-2 sprint actual agregará providers que enriquecerán payload — endpoint debe ser forward-compat (no schema change).
- **Tiempo estimado:** 1 ejecución architect + 2 ejecuciones builder paralelas (BE + FE) con auto-loop audit. Total ~3 ejecuciones.
- **Alternativas técnicas:** ninguna — interface stub explícito y motor BE existe.

## Decisiones diferidas (explícitas)

- **Reranking LLM-based** suggestions: backlog. Heurístico actual <10ms p99. Reabrir si métricas adopción <5%.
- **Persistencia durable suggestions** (tabla dedicada vs `copilot_trace_event`): mantener trace_event hasta volumen >1M events/día.

## Out of scope

- Agregar nuevos providers (sales_agent, brand, copilot) — eso es PR-2.
- Cambiar shape engine internal — engine intacto.
- Migrar voice endpoint signature (multipart/form-data shape) — solo URL swap.
- E2E playwright voice flow — ya cubierto smoke existente; verify no regressión.

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? — **sí indirecto** (smart-chips habilitan conversación rápida)
- [x] ¿Qué tools nuevos requiere? — ninguno
- [x] ¿Cards/UI nueva? — no (refactor `SuggestedChips.tsx` + `SuggestedActions.tsx` existentes)
- [x] Si NO copilot → razón documentada — N/A

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` | `prompts/01-architect-start.md` | `CONTRACT.md` |
| Implementation BE | `nicolify-backend` + `copilot-expert` | `prompts/02-builder-start.md` (sección BE) | `IMPL-LOG.md` BE + tests + commit |
| Implementation FE | `nicolify-frontend` + `frontend-expert` + `copilot-expert` | `prompts/02-builder-start.md` (sección FE) | `IMPL-LOG.md` FE + tests vitest + commit |
| Audit BE | `nicolify-backend-auditor` (auto-spawn por builder) | `prompts/03-auditor-start.md` (BE) | `REVIEW-backend.md` |
| Audit FE | `nicolify-frontend-auditor` (auto-spawn por builder) | `prompts/03-auditor-start.md` (FE) | `REVIEW-frontend.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` update |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| API endpoint BE | `POST /api/v1/copilot/suggestions` | nuevo |
| API endpoint BE | `POST /api/v1/copilot/suggestions/accept` | nuevo |
| Domain event | `SuggestionShown` | emitter agregado en endpoint |
| Domain event | `SuggestionAccepted` | emitter agregado en endpoint |
| FE module | `frontend/src/features/copilot/api/voice-api.ts` | URL swap |
| FE module | `frontend/src/features/copilot/api/suggestions-api.ts` | nuevo |
| FE module | `frontend/src/features/copilot/hooks/use-suggestions.ts` | rewrite stub→React Query |
| FE module | `frontend/src/features/copilot/hooks/use-suggestion-accept.ts` | nuevo |
| FE component | `SuggestedChips.tsx` | wire mutation onClick |
| FE component | `SuggestedActions.tsx` | drop static, consume hook |
| current-state/ | `current-state/copilot.md` | append cap "Smart-chips live" + "Voice migration done" |

## Tests requeridos (TDD)

**Backend:**
- `backend/tests/modules/copilot/api/test_suggestions_endpoint.py`: happy/empty/tenant-isolation/missing-header/engine-failure/event-emission
- `backend/tests/modules/copilot/api/test_suggestions_accept_endpoint.py`: happy/invalid-id/tenant-isolation/subscriber-write
- `backend/tests/modules/copilot/api/test_suggestions_endpoint_integration.py`: e2e con `OfferSuggestionProvider` real
- arch test: nuevos endpoints declaran `response_model=` y filtran `tenant_id`

**Frontend:**
- `use-suggestions.test.ts`: chips from API/loading/error-graceful/re-fetch-on-route-change
- `use-suggestion-accept.test.ts`: mutation/fire-and-forget
- `voice-api.test.ts`: nueva URL/FormData shape
- `SuggestedChips.test.tsx`: render from hook + onClick mutation

## Aceptación

- [ ] Tests verdes (BE + FE)
- [ ] Lint/type check verdes (ruff + mypy + eslint + tsc)
- [ ] `IMPL-LOG.md` BE + FE completos
- [ ] `REVIEW-backend.md` + `REVIEW-frontend.md` PASS
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/copilot.md` actualizado con lineage
- [ ] Decisiones registradas en `decisions.md` PI-2
- [ ] Verificación manual: dev up + seed offer + ver chips dinámicas + accept event en `copilot_trace_event`

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Endpoint `/voice/upload-and-transcribe` shape diferente a legacy | Architect verifica shape en CONTRACT (Read endpoint actual antes definir) |
| Race deploy FE→BE chips vacías brevemente | Empty state graceful ya existe |
| React Query cache invalidation cross-route | Hook key incluye `route` — re-fetch automatic |
| Subscriber procesa eventos out-of-order | `SuggestionAccepted` subscriber best-effort async; no orden requerido |
