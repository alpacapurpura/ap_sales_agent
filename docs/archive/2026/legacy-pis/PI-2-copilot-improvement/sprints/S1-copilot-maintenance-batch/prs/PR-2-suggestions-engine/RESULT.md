# RESULT — PR-2-suggestions-engine

> Owner: `/pm` (main thread Opus 4.7). Cierre del loop.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | 2026-04-29 |
| Commits principales | `b363a440` (CONTRACT) · `0ea0f48e` (feat motor + 50 tests + doc) |
| Branch merged a | development |
| Verdict auditor | PASS (1 WARN no-bloqueante cat 12) |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| Motor real suggestions con context | `SuggestionEngine` recibe context + ranking | `SuggestionEngine` con register_provider + get_suggestions(context) heurística (confidence DESC → provider_priority DESC → registration order, cap 5) | ✅ cumplido |
| Provider pattern | Cada módulo registra `SuggestionProvider` | `SuggestionProvider` Protocol + `OfferSuggestionProvider` (route `offer-studio`, priority 0) | ✅ cumplido |
| Adapter consume engine desde tools | Reemplazar `offer_section_tools.py` hardcoded | Híbrido — engine_hints mezclado con brand_hints fallback (W-1 partial expansion). Tests validan contract preserved | ⚠️ parcial — pure expansion diferida S2+ cuando lleguen brand/sales-agent providers |
| Métricas observables | `suggestion_shown` + `suggestion_accepted` events | Ambos event classes en `domain/events.py` + subscribers `on_suggestion_shown`/`on_suggestion_accepted` en `domain_subscribers.py` (best-effort) | ✅ cumplido |
| Forward-compat FE swap | TS shape locked | Domain VO `Suggestion` mirrorea `(id, label, prompt, confidence?, category?)` exacto FE locked | ✅ cumplido |

Veredicto general: ✅ cumplido (1 WARN partial expansion documentada como deuda).

## Surface entregada

| Tipo | Path | Notas |
|---|---|---|
| Domain VO | `backend/src/modules/copilot/domain/suggestion.py` | NEW frozen dataclass + invariantes |
| Domain events | `backend/src/modules/copilot/domain/events.py` | MODIFY append-only — `SuggestionShown`, `SuggestionAccepted`, constants |
| Application engine | `backend/src/modules/copilot/application/suggestions/engine.py` | NEW process-singleton + ranking |
| Application registry | `backend/src/modules/copilot/application/suggestions/registry.py` | NEW con `provider_priority` |
| Provider base | `backend/src/modules/copilot/application/suggestions/providers/base.py` | NEW Protocol + `provider_priority: int = 0` |
| Provider offer | `backend/src/modules/copilot/application/suggestions/providers/offer.py` | NEW heurística route-scoped |
| Application reader | `backend/src/modules/copilot/application/services/offer_suggestion_reader.py` | NEW shared reader (preset flags) |
| Tool refactor | `backend/src/modules/copilot/application/tools/offer_section_tools.py` | MODIFY (Q1 híbrido) |
| Subscriber | `backend/src/modules/copilot/observability/recording/domain_subscribers.py` | MODIFY append-only — 2 subscribers nuevos |
| Tests | `backend/tests/modules/copilot/suggestions/` (6 files, 50 tests verde) | TDD layered |
| Doc técnico | `docs/domains/copilot/suggestions-engine.md` | UPDATE — "Option A IMPLEMENTED" + B/C colapsadas |
| current-state lineage | `docs/pm-nico/current-state/copilot.md` | APPEND — "Suggestion engine + provider registry" |

## Capacidades agregadas (lineage para current-state)

```md
### Cap: Suggestion engine + provider registry
- Introducida: PR-2 (PI-2, S1, commit `0ea0f48e`, 2026-04-29)
- Estado: BE motor live, FE consumiendo stub `useSuggestions` aún
- Operable copilot: indirecto (alimenta smart chips bajo input chat)
- Providers registrados: `offer` (route `offer-studio`, priority 0)
- Providers pendientes: brand, sales_agent, copilot (PRs siguientes S2+)
- Heuristic rules: 6 (no offers→create, high_ticket→pricing, recurring_billing→billing, is_lead_magnet→link core, incomplete promise.headline→variants, lead_magnet sin core→link)
- Observability: `copilot_trace_event` con `event_type=suggestion_shown|suggestion_accepted` (forward-compat — `SuggestionAccepted` sin producer hasta FE swap PR)
```

(Ya appendeado por builder a `current-state/copilot.md` líneas 84-92.)

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| D-1 | Heurística simple (no LLM ranking) | Latencia <10ms, costo cero. LLM ranking → backlog si heurística no alcanza | CONTRACT §18 (architect) |
| D-2 | Reuse `copilot_trace_event` (no tabla nueva) | Zero migración. Tabla dedicada premature; backfill posible si volume justifica | CONTRACT §18 (architect) |
| D-3 | Q1 EXPANSION pure (delete static) | Engine SSoT día 1. Static = SSoT divergente que crece con providers | PM Chris |
| D-4 | Q2 forward-compat ship `SuggestionAccepted` | Subscriber + event listos sin producer. FE migration agrega producer. Métricas accept-rate desde día 1 | PM Chris |
| D-5 | Q3 explicit `provider_priority` weight | Tie-break transparente A/B-testable cuando lleguen brand/SA providers | PM Chris |
| D-6 | Q4 doc update este PR atomic | Co-located con código + builder contexto fresco | PM Chris |
| D-7 | Builder híbrido Q1 (engine + brand_hints fallback) | Preserva goldens + brand_hints contextual no cubierta por engine actual. Pure expansion → S2+ cuando providers cubran casos | Builder pragmatic + PM acepta como deuda |

## Métricas medidas

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| Tests copilot/suggestions PR-2 | 0 | 50 verde | +50 |
| Arch fitness | 649 | 649 | 0 (sin regresión) |
| Mypy errors PR-2 files | 0 | 0 | 0 |
| Ratchet copilot→módulo | 22 | 22 | 0 (frozen) |
| Cap copilot anchors | 36 | 36 | 0 (sin bump) |
| Iteraciones auto-fix | — | 0 (verdict PASS first audit) | — |

## Deuda técnica generada

| Item | Razón | Sprint destino |
|---|---|---|
| Pure expansion `offer_section_tools.py` (eliminar static `suggestions[]` líneas 163, 173, 257, 374) | Builder hizo híbrido. Pure expansion requiere providers brand+SA cubrir casos brand_hints | S2+ cuando land brand-provider + sales-agent-provider |
| FE swap stub `useSuggestions` → real GET endpoint | BE motor live, FE consume stub. Endpoint API + producer `SuggestionAccepted` faltan | Cross-stack PR siguiente (S1 PR-3 o S2) |
| Voseo regex extension (`ayudame`/`sugiereme`) | Edge case ambiguo (también coloquial MX) | Backlog spanish-text rule |

## Update obligatorios hechos

- [x] `current-state/copilot.md` actualizado con capability lineage (líneas 84-92)
- [ ] `decisions.md` PI append (siguiente turno PM)
- [ ] Sprint `learnings.md` append (siguiente turno PM)
- [x] Doc `docs/domains/copilot/suggestions-engine.md` updated "Option A IMPLEMENTED"
- [ ] Última PR del sprint: NO (S1 tiene PR-3 backfill-content-blocks pendiente)

## Lecciones para process-learnings

1. **Auto-loop builder→auditor truncó dos veces seguidas** (PR-2 builder cap tokens en spawn auditor; PR-2 auditor cap tokens mid-categories). PM main thread completó manualmente. Mejora futura: builder/auditor con pre-cocido más compacto, o split en 2 sub-agents (gates run + verdict synthesize).
2. **Q1 expansion vs additive trade-off real** — builder eligió híbrido pragmático que preserva goldens. PM Chris aceptó como deuda. Lección: decisiones architect "build-right-once" no siempre traducen a "delete legacy ahora" si tests goldens dependientes.
3. **Filosofía Chris paralelas relajada (M8 nueva)** — tocar archivos ajenos OK con regla "extend no destroy". Reduce fricción agente sin colisiones reales (módulos distintos default).

## Próximo paso PM

PR-3-backfill-content-blocks → ¿architect spawn ahora o pausamos?

---

PR-2 **shipped**. PM cierra archivo. Loop completo.
