# Sprint S2 — copilot-cero-deuda-stack

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S2-copilot-cero-deuda-stack |
| PI padre | PI-2-copilot-improvement |
| Estado | done |
| Inicio | 2026-04-30 |
| Cierre estimado | 2026-04-30 |
| Cierre real | 2026-04-30 |
| Owner PM | /pm |

## Objetivo (1 línea)

Cerrar todas las deudas técnicas del S1 (FE voice migration + FE suggestions live + pure expansion offer_section_tools) + ejecutar swap LLM stack chinos (classifier + summarizer → DeepSeek V4-Flash) con eval gate para validar 4-9x cost reduction sin pérdida calidad.

## Pre-handoff (input desde sprint anterior)

- **Decisiones:** `../S1-copilot-maintenance-batch/handoff.md` (12 decisiones D-1..D-12).
- **Surface disponible:**
  - BE motor suggestions (`engine.py`, `registry.py`, providers/base.py, providers/offer.py)
  - BE event `SuggestionAccepted` + subscriber forward-compat (sin producer ni endpoint público)
  - BE `_engine_suggestions_for_context()` helper en `offer_section_tools.py` (parcial — 1 static `"suggestions": [hint]` queda line 163)
  - BE legacy `/voice/transcribe` retorna 410 Gone con `X-Deprecation-Notice` header
  - FE `useSuggestions()` stub estático con map `ROUTE_SUGGESTIONS` per route
  - FE `voice-api.ts:26` llama legacy roto
- **Riesgos abiertos:** FE call /voice/transcribe rompe en runtime (410). FE consume stub no real engine. Pure expansion offer_section_tools híbrido pragmatic deuda.
- **Skills/agentes:** `nicolify-architect`, `nicolify-backend`, `nicolify-frontend`, `nicolify-backend-auditor`, `nicolify-frontend-auditor`, `copilot-expert`, `frontend-expert`, `brand-expert`, `sales-agent-expert`.
- **Research adicional 2026-04-30:** `docs/pm-nico/research/2026-04-30-llm-landscape-chinese-models.md` — input PR-3.

## Plan PRs (folders)

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-1 | `prs/PR-1-fe-swap-suggestions-api/` | Cross-stack: BE expone `POST /copilot/suggestions` + `POST /copilot/suggestions/accept`. FE swap stub `useSuggestions` → React Query real. FE migra voice-api.ts. | `nicolify-architect` → `nicolify-backend` + `nicolify-frontend` paralelo → auditors | L | **shipped PASS** (1 iter c/u) |
| PR-2 | `prs/PR-2-pure-expansion-providers/` | BE: 3 providers nuevos + pure expansion offer_section_tools. Cierra deuda S1 #3. | `nicolify-architect` → `nicolify-backend` → auditor + skills | M | **shipped PASS** (1 iter PM main thread) |
| PR-3 | `prs/PR-3-llm-cost-optimization/` | BE: LLM stack swap classifier+summarizer + eval gate framework + rollback env-flag. | `nicolify-architect` → `nicolify-backend` → auditor + skills | L | **shipped PASS PARTIAL** (wiring DEFERRED PR-4) |

Detalle de cada PR vive en `prs/PR-N-{slug}/PR.md`. Prompts pre-cocidos en `prompts/`.

## Criterio éxito sprint

- [ ] FE call `voice/transcribe` reemplazada (verificar grep frontend = 0 hits legacy)
- [ ] FE `useSuggestions` consume `POST /copilot/suggestions` con React Query (sin stub estático)
- [ ] FE producer `useSuggestionAccept` dispara `POST /copilot/suggestions/accept` y BE subscriber recibe evento
- [ ] `offer_section_tools.py` 0 static `"suggestions": [...]` literales (grep = 0 hits que no sean helper signature)
- [ ] 3 nuevos providers registrados (`brand`, `sales_agent`, `copilot`) + tests cobertura por provider
- [ ] Classifier + summarizer ejecutan DeepSeek V4-Flash en prod path con env flag rollback
- [ ] Eval gate framework: ≥50 goldens por uso (classifier + summarizer) running CI con threshold ≥95% calidad
- [ ] Cero refactor necesario en sprint siguiente (verificable: handoff S2 NO lista deuda técnica)
- [ ] Todos los PRs tienen `RESULT.md` escrito (loop cerrado)
- [ ] `current-state/copilot.md` actualizado con capabilities lineage de los 3 PRs shipped

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| Migrar specialist (extraction/auto-fill) → DeepSeek V4-Pro o GLM-5 | Eval gate calidad-crítico requiere set goldens >100 + comparación blind | S3 o PI-3 |
| Migrar embeddings → Qwen3-Embedding-8B | Re-index Qdrant ventana mantenimiento + rollback plan dedicado | S3 o PI dedicado |
| Migrar sales_agent voice → chino | Voice fidelity grader Chinese pendiente (sales-agent-brand-voice rule) | Q3 2026 según rule |
| Telegram bridge copilot (Bloque A) | Discovery formal pendiente PI separado | PI-3+ |
| LLM ranking suggestions (vs heurístico) | Backlog si motor heurístico no alcanza | PI futuro condicional |
| ML feedback loop suggestions (migrar de copilot_trace_event a tabla) | Backlog si volumen lo justifica | PI futuro condicional |

## Decisiones a tomar durante sprint

(append-only conforme aparezcan)

| Fecha | Decisión | PR |
|---|---|---|

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| FE swap rompe runtime UX (smart-chips vacíos durante deploy) | Endpoint engine returns `[]` graceful + FE empty-state ya existe (no chips renderizados) | PR-1 builder |
| 3 providers nuevos data joins lentos (>10ms p99 engine SLA) | Best-effort: providers async + cache 5min per tenant+route | PR-2 architect |
| Eval gate goldens insuficientes / sesgo | 50 mínimo + cobertura: 5 categorías × 10 ejemplos cada + adversarial 10% | PR-3 architect |
| DeepSeek V4-Flash TTFT 1.03s rompe SLO classifier hot path <200ms | A/B test paralelo + fallback Claude Haiku 4.5 vía env flag (`COPILOT_CLASSIFIER_FALLBACK`) | PR-3 builder |
| Sesión paralela PI-1 toca módulos solapados | Regla M8: extend no destroy. Builders prompt explicit path-restriction PI-2 | PM (este sprint) |

## Cierre

Al cerrar:
1. Llenar `learnings.md` (qué funcionó, qué no, sorpresas).
2. Llenar `handoff.md` (decisiones, surface, agentes recomendados S{N+1}).
3. Marcar sprint `done` en este `sprint.md`.
4. Verificar todos los `prs/PR-*/RESULT.md` escritos (loop cerrado).
5. Si learnings impactan proceso global → append `../../../../process/process-learnings.md`.
6. Si último sprint del PI → escribir `retro.md` + mover PI completo a `pis/archive/`.
