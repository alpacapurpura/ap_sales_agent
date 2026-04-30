# RESULT — PR-1-fe-swap-suggestions-api

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | 2026-04-30 |
| Commits | `e53b7ef6` (BE+FE main impl) · `824c946a` (FE auditor fixes iter-1) |
| Branch merged a | development |
| Verdicts | BE PASS (1 iter, auditor real) · FE PASS (1 iter, PM main thread post stall S1 learning #8) |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| Voice transcription end-to-end funciona | URL legacy reemplazada | `voice-api.ts` URL swap + D-9 shape adapter implementado | ✅ + adapter shape (D-9 surface > URL swap simple) |
| Smart-chips dinámicas | FE consume motor BE | `useSuggestions` React Query hook live, `ROUTE_SUGGESTIONS` map eliminado | ✅ |
| Producer event SuggestionAccepted | onClick chip → BE subscriber `copilot_trace_event` | `useSuggestionAccept` mutation fire-and-forget + endpoint `POST /accept` emite event | ✅ |
| BE endpoints | 2 endpoints `POST /suggestions` + `POST /suggestions/accept` | Live con response_model declared, tenant isolation, best-effort doble try/except | ✅ |
| Tests TDD | 19+ tests (BE + FE) | 16 BE (8 unit + 5 unit accept + 3 integration) + 21 FE (6 use-suggestions + 4 use-suggestion-accept + 5 voice-api + 6 SuggestedChips) = **37 nuevos tests** | ✅ excede |

Veredicto: ✅ **cumplido**

## Surface entregada (concreta)

| Tipo | Path / nombre | Notas |
|---|---|---|
| API endpoint BE | `POST /api/v1/copilot/suggestions` | response_model SuggestionsResponse, asyncio.to_thread D-3, best-effort returns 200 + suggestions=[] |
| API endpoint BE | `POST /api/v1/copilot/suggestions/accept` | response_model SuggestionAcceptResponse, fire-and-forget producer SuggestionAccepted |
| BE DTOs | `backend/src/modules/copilot/api/suggestions_dto.py` | 5 Pydantic v2 DTOs: SuggestionsRequest, SuggestionDTO, SuggestionsResponse, SuggestionAcceptRequest, SuggestionAcceptResponse |
| BE router | `backend/src/modules/copilot/api/suggestions.py` | 175 líneas; doble try/except (engine + EventBus) |
| BE wiring | `backend/src/main.py` | +1 import + include_router bajo `/api/v1/copilot` |
| FE API client | `frontend/src/features/copilot/api/suggestions-api.ts` | NUEVO 70 líneas (fetchSuggestions + acceptSuggestion) |
| FE API client | `frontend/src/features/copilot/api/voice-api.ts` | URL swap + D-9 shape adapter |
| FE hook | `frontend/src/features/copilot/hooks/use-suggestions.ts` | REWRITE: React Query, drop ROUTE_SUGGESTIONS map, queryKey [route, conversationId] |
| FE hook | `frontend/src/features/copilot/hooks/use-suggestion-accept.ts` | NUEVO 46 líneas, fire-and-forget mutation, NO invalida queries (D-13) |
| FE component | `SuggestedChips.tsx` | onClick wire mutation accept |
| FE component | `SuggestedActions.tsx` | drop static map (D-14) |
| FE types | `types/suggestions.ts` | extend con DTOs coordinados con BE |
| Tests BE | 3 archivos test_suggestions* | 16 tests (8 unit + 5 unit accept + 3 integration) |
| Tests FE | 4 archivos __tests__ | 21 tests (use-suggestions, use-suggestion-accept, voice-api, SuggestedChips) |

Total: **17 archivos modificados/agregados, 37 tests nuevos verde, ZERO migrations DB, ZERO schema changes**.

## Capacidades agregadas (lineage para current-state)

```md
### Cap: Smart-chips dinámicas FE consume engine + producer event
- Introducida: PR-1 (PI-2, S2, commits `e53b7ef6` + `824c946a`, 2026-04-30)
- Estado: live
- Operable copilot: indirecto (chips habilitan exploración rápida bajo input chat)
- Consumer FE: `useSuggestions()` React Query hook (queryKey [route, conversationId], staleTime 5min)
- Producer: `useSuggestionAccept()` mutation fire-and-forget → endpoint `POST /copilot/suggestions/accept` → event `SuggestionAccepted` → subscriber S1 escribe `copilot_trace_event`
- Endpoint motor: `POST /copilot/suggestions` retorna `{suggestions, breakdown, latency_ms}` best-effort 200
- Métricas adopción habilitadas: `SELECT COUNT(*) FILTER (WHERE event_type='suggestion_accepted') / COUNT(*) FILTER (WHERE event_type='suggestion_shown') ratio`

### Cap: Voice transcription endpoint estable (legacy retired live)
- Introducida: PR-1 (PI-2, S2, commit `e53b7ef6`, 2026-04-30)
- Estado: live
- Operable copilot: sí (voice button composer)
- FE migration: `voice-api.ts` llama `/voice/upload-and-transcribe` con D-9 shape adapter (firma pública `TranscriptionResponse` intacta — consumers sin cambios)
- Cierre deuda S1 PR-1 D-5: legacy `/voice/transcribe` 410 Gone ya NO recibe llamadas FE (verificable `grep -rn "voice/transcribe" frontend/src/` = 0 hits activos)
```

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| PR1-D-3 | asyncio.to_thread wraps sync engine | No bloquea event loop FastAPI con engine sync | CONTRACT D-3 |
| PR1-D-6 | SuggestionDTO incluye `source_module`, excluye `metadata` | source_module = slug público necesario para accept event; metadata potencial PII | CONTRACT D-6 |
| PR1-D-9 | Voice migration: URL swap + shape adapter (no solo URL swap simple) | Endpoints shape incompatibles verificados en código real (BE `voice.py:236` vs legacy `voice_dto.py:18`) | CONTRACT D-9 |
| PR1-D-10 | Best-effort returns 200/[] siempre, emite SuggestionShown incluso 0 chips | Resilencia copilot rule + métricas adopción denominador | CONTRACT D-10/D-11 |
| PR1-D-13 | Mutation accept NO invalida queries | Engine no re-rankea por accept individual, evita re-fetch innecesario | CONTRACT D-13 |
| PR1-D-14 | DROP `ROUTE_SUGGESTIONS` duplicado en SuggestedActions.tsx | Cero deuda — fuente única de chips desde engine BE | CONTRACT D-14 |
| PR1-D-15 | Reusar anchor `[COPILOT-SUGGESTIONS-ENGINE]`, NO bumpear cap 36/37 | Anchor budget preservado | CONTRACT D-15 |
| PR1-D-16 | Cero nuevos cross-module imports | Ratchet copilot→módulo 22 frozen | CONTRACT D-16 |

## Métricas medidas (si aplican)

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| Tests BE copilot api | 13 baseline (pre-PR) | 29 (16 nuevos) | +16 |
| Tests FE copilot | 264 baseline | 285 | +21 |
| Cobertura archivos PR-1 BE | 0% (nuevos) | 97.44% | nuevo high coverage |
| Endpoints copilot api | 14 baseline | 16 (+suggestions, +suggestions/accept) | +2 |
| ROUTE_SUGGESTIONS hardcoded chips | 21 chips estáticos en FE | 0 | -21 (cero deuda) |
| FE call legacy `/voice/transcribe` | 1 (line 26 voice-api.ts) | 0 | -1 (cero deuda) |

## Deuda técnica generada

| Item | Razón | Sprint destino |
|---|---|---|
| react-perf warnings (3 inline objects/functions) en SuggestedChips/SuggestedActions | Patrones preexistentes, no introducidos por PR-1 (verificado IMPL-LOG B-1) | Backlog cleanup futuro |
| `Annotated[object, Depends(...)]` en suggestions.py vs `Annotated[User, ...]` | Defensivo pero pierde tipado fuerte (BE auditor B-1) | Próximo PR cuando User type estabilizado |

Cero deuda funcional/arquitectónica nueva. Cero deuda S1 PR-1 D-5 + S1 PR-2 FE swap = ambas cerradas.

## Update obligatorios hechos

- [x] `current-state/copilot.md` actualizado con capability lineage (commit siguiente)
- [x] `decisions.md` PI appendeado (commit siguiente)
- [x] Sprint `learnings.md` appendeado (commit siguiente)
- [ ] Si capability deprecada → bullet en sección `## Capacidades deprecadas` — N/A
- [ ] Si última PR del sprint → handoff.md llenado — N/A (PR-2 + PR-3 pendientes)

## Próximo paso PM

PR-2-pure-expansion-providers ya tiene CONTRACT.md ready (architect-empowered). Spawn builder PR-2 (BE only).

---

PR-1 **shipped**. PM cierra archivo. Loop completo.
