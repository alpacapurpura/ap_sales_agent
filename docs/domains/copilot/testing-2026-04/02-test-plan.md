# Test Plan — 12 fases mapeadas a F0-F11

## Mapa F# → TP#

| F# (redesign) | TP# (testing) | Capacidad |
|---|---|---|
| F0 (foundation) | TP0 (transversal) | Baseline tests + tooling setup. |
| F1 (provider) | TP10 | Plug-in friendly: agregar tool sin tocar `copilot/`. |
| F2 (deep agent) | TP9 | Planning + scratchpad + subagentes. |
| F3 (brand summary) | TP2 | Lighthouse always-on en system prompt. |
| F4 (URL ctx) | TP3 | URL como inspiración persistente cross-turn. |
| F5 (ask_tenant_data) | TP4 | Q&A natural sobre data del tenant. |
| F6 (workflow) | TP5 | Workflow runtime unificado (guided + procedure + extraction). |
| F7 (channel formatter) | TP6 | Output canal-aware (chat/whatsapp/email/sms). |
| F8 (routing + cost) | TP1 | LLMClassifier NANO + cache prefix + 4 tier router. |
| F9 (quality + obs) | TP8 | CopilotJudge weekly + admin /copilot-quality. |
| F10 (marketing KB) | TP7 | RAG curado + knowledge_search tool. |
| F11.1 (router wire) | TP1 (extiende) | `copilot_routing_log` populated post-turn. |
| F11.5 (RAG eval cron) | TP8 (extiende) | Weekly RAG eval persiste row con metadata expected. |
| (cierre) | TP11 | E2E UX = "feel like Claude Code". |

---

## DAG

```
TP0 (baseline)
   │
   ├──► TP1 (routing, F8/F11.1)
   │    │
   │    └──► TP9 (deep_agent, F2) ──┐
   │                                 │
   ├──► TP2 (brand lighthouse, F3) ──┼─┐
   │                                 │ │
   ├──► TP3 (URL inspirations, F4) ──┤ │
   │                                 │ │
   ├──► TP4 (ask_tenant_data, F5) ───┼─┤
   │                                 │ │
   ├──► TP5 (workflows, F6) ─────────┤ ├──► TP11 (UX e2e)
   │                                 │ │
   ├──► TP6 (channel format, F7) ────┤ │
   │                                 │ │
   ├──► TP7 (marketing KB, F10) ─────┤ │
   │                                 │ │
   ├──► TP8 (quality + obs, F9/F11.5)┤ │
   │                                 │ │
   └──► TP10 (provider, F1) ─────────┘ │
                                       │
                                       ▼
                                   (TP11 sintetiza)
```

- **TP0 secuencial bloqueante**: instala tooling, corrobora infra observability, snapshotea baseline.
- **TP1–TP10 paralelizables tras TP0**: cada uno toca una capacidad ortogonal.
- **TP9 + TP10 fundacionales**: necesitan TP1 pasado (routing telemetría confirmada).
- **TP11 cierre**: heurísticas que solo aplican una vez todo lo anterior pasó.

---

## Recomendación de orden ejecución (single-thread)

Si Chris ejecuta serialmente (una conversación por TP, una por sesión):

1. **TP0** — setup obligatorio.
2. **TP1** — routing es la capa más nueva (F8 + F11.1) y más cuestionada (admin estaba vacío).
3. **TP7** — RAG curado es la promesa de "autoridad" + el corpus se pobló en F10; validar primero antes de UX.
4. **TP2** — brand lighthouse alimenta TP3, TP4, TP6 (todos consumen brand).
5. **TP4** — ask_tenant_data es el "salto cualitativo grande" (F5 learnings); validar temprano.
6. **TP3** — URL inspirations depende de TP2 + brand summary populated.
7. **TP5** — workflows runtime touches TP4 (data) + TP6 (channels).
8. **TP6** — channel formatter es output-stage; valida sobre todo lo anterior.
9. **TP8** — quality + observability es meta-validación: el judge ya corrió contra todo lo anterior.
10. **TP9** — deep_agent harness sobrevive a todo (F2 es base de F4-F8).
11. **TP10** — provider extension prueba que el patrón aguanta agregando algo nuevo.
12. **TP11** — síntesis UX final.

Si Chris ejecuta en paralelo (multi-instance): TP1 → TP7 → todo lo demás en paralelo → TP11 al final.

---

## Una página por TP

| TP | Path doc | Tiempo estimado (real-LLM) | Pre-req hard | Output principal |
|---|---|---|---|---|
| TP0 | `phases/TP0-baseline-observability.md` | 30 min | — | Tooling instalado, baseline dataset, dashboards verificados. |
| TP1 | `phases/TP1-routing-tier-selection.md` | 2-3 hs | TP0 | Routing log populated, cache hit rate medido, tier distribution per route. |
| TP2 | `phases/TP2-brand-summary-lighthouse.md` | 1-2 hs | TP0 + tenant test con brand_summary populated | Brand_coherence score ≥4.0, lighthouse aparece en system prompt invariant. |
| TP3 | `phases/TP3-url-contextual-inspirations.md` | 2 hs | TP2 | Inspiration referenciable turn 7, scratchpad persiste, fetch_url robusto. |
| TP4 | `phases/TP4-ask-tenant-data.md` | 3-4 hs | TP0 + tenant test con data en CRM/Offer/Connections | 10 preguntas naturales devuelven correcta sin SQL crudo, latencia ≤1.5s. |
| TP5 | `phases/TP5-workflows-runtime.md` | 2 hs | TP4 + TP6 | Setup brand minimal + design offer from URL completan sin discrepancia UX. |
| TP6 | `phases/TP6-channel-formatter.md` | 2 hs | TP2 | 4 canales × 4 contenidos: 16 outputs sin markdown roto + judge ≥4.0. |
| TP7 | `phases/TP7-marketing-kb-rag.md` | 1-2 hs | TP0 + KB seedeado | 8/8 RAG goldens recall ≥0.8, citation_accuracy ≥4.0, latencia search ≤500ms. |
| TP8 | `phases/TP8-quality-eval-observability.md` | 1-2 hs | TP1, TP7 | Manual run weekly_quality_eval + weekly_rag_eval producen rows; admin tabs ven data. |
| TP9 | `phases/TP9-deep-agent-planning.md` | 3 hs | TP1 | Plan card aparece, write_todos progresa, subagent task isolation OK. |
| TP10 | `phases/TP10-provider-pattern.md` | 1-2 hs | TP1 | Add tool dummy en módulo nuevo via provider sin tocar `copilot/`. |
| TP11 | `phases/TP11-end-to-end-ux.md` | 4-6 hs | Todo lo anterior | Heurísticas Claude Code 8/8 + 5 user journeys reales completos. |

**Total estimado:** ~25-35 hs serial, ~12-15 hs paralelizado.

---

## Outputs cross-fase

Cada `results/TP{#}-{YYYY-MM-DD}.md` debe incluir:

```markdown
# TP{N} — {fecha}

## Pre-research
- Queries ejecutadas + insights nuevos vs `01-tooling.md`.

## Scenarios run
| ID | Descripción | Pass/Fail | Cost ($) | Latencia (ms) | Judge avg | Notas UX |

## Diff vs baseline
- Métricas observadas vs `03-metrics-and-targets.md`.

## Failures + root cause
- Para cada fail: síntoma → trace_event evidencia → root cause → fix aplicado o plan separado.

## Recomendaciones
- Para próximas corridas / TPs siguientes / redesign próximo.

## Métricas agregadas
- Cost total run, latencia p50/p95, judge avg.
```

Reportes commiteados en `results/`. Plan vive: si descubrís escenario nuevo, **actualizás** `phases/TP#-*.md` antes de cerrar.
