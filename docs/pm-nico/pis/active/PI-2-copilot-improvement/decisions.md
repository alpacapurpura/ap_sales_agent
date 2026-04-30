# PI-2-copilot-improvement — Decisiones

> ADR-style. Append-only.

## 2026-04-29 — PI creado

**Decisión:** Crear PI dedicado para mejoras de copilot.

**Razón:** Copilot = interfaz primaria Nicolify (visión). Mejoras continuas deben ir en PI con foco, no como bug-fix-soup.

**Alternativas consideradas:** dejar como bug fixes ad-hoc → descartado (pierde visión coherente).

## 2026-04-29 — Bloque B 8 recomendaciones investigadas

**Decisión:** clasificar las 8 recs en DO/SKIP/DISCARD/DEFER tras research code-level (`research/2026-04-29-copilot-8-recommendations.md`).

| Rec | Veredicto | Razón |
|---|---|---|
| #1 suggestions engine | DO (S2 propio) | Sin motor real; scope mayor requiere arq + discovery propio |
| #2 rate-limit voice | DO (S1 PR-1) | Riesgo abuso Whisper real; `_MAX_AUDIO_BYTES` hardcoded sin throttling |
| #3 refactor `_tool_result_to_block` | SKIP | Ya resuelto 2026-04-22 (`block_adapters.py` registry pattern, DDD-correct) |
| #4 `filename` en `MediaUploadResponse` | DISCARD | Exclusión consciente (`asset_id` canónico, comentario en DTO) |
| #5 `COPILOT_MEDIA_MAX_BYTES` env | DO (S1 PR-1) | DRY violation; constantes media+voice duplicadas hardcoded |
| #6 DB test roundtrip | DO (S1 PR-1, lite) | Tests existen con MagicMock; faltan fixture DB real |
| #7 backfill content→blocks | DEFER (backlog) | Forward-compat funciona; sin urgencia. Backlog opcional |
| #8 doc code-highlighting Shiki | DISCARD | Shiki no integrado; sin caso uso; stack actual cubre |

**Alternativas consideradas:** meter las 8 en sprints separados → descartado (overkill, varias trivial). Forzar #1 a S1 → descartado (scope mayor + diluye foco hardening).

**Próximo paso:** confirmar S1 con Chris → materializar `PR-1-voice-media-hardening`.

## 2026-04-29 — Override Chris: hacer Bloque B completo en S1

**Decisión:** Chris descartó el plan PM de diferir #1 (S2) y #7 (backlog). Override: "hacerlas todas en S1, cerrar las que se terminen".

| Rec | Decisión final | Destino |
|---|---|---|
| #1 suggestions engine | DO en S1 | PR-2 `suggestions-engine` |
| #2 rate-limit voice | DO en S1 | PR-1 `voice-media-hardening` |
| #3 refactor block_adapter | CLOSED definitivo | — (ya resuelto 2026-04-22) |
| #4 filename MediaUploadResponse | CLOSED definitivo | — (decisión consciente) |
| #5 COPILOT_MEDIA_MAX_BYTES env | DO en S1 | PR-1 `voice-media-hardening` |
| #6 DB roundtrip tests | DO en S1 | PR-1 `voice-media-hardening` |
| #7 backfill content→blocks | DO en S1 | PR-3 `backfill-content-blocks` |
| #8 doc Shiki highlighting | CLOSED definitivo | — (sin caso uso) |

**Razón override:** Opus 4.7[1M] permite scope amplio cohesivo. Defer = arrastrar deuda. Cerrar Bloque B completo en S1 libera mente para Bloque A multicanal en S2.

**Alternativas consideradas:** PM propuso S1 chico + S2 con #1 + backlog #7 → Chris descartó por preferir cierre completo Bloque B en S1.

**Estructura S1 resultante:** `sprints/S1-copilot-maintenance-batch/` con 3 PRs (PR-1 voice/media hardening, PR-2 suggestions engine, PR-3 backfill content→blocks).

**Próximo paso:** ejecutar `prompts/01-architect-start.md` de PR-1 (sugerido por boundary técnica + esfuerzo M).

## 2026-04-30 — S2-copilot-cero-deuda-stack iniciado

**Decisión:** abrir S2 con foco "cero deuda técnica" + LLM cost optimization. 3 PRs cohesivos.

**Razón:** Chris explicit "cero deuda" + criterio escalabilidad 1000+ tenants > pragmatic shortcuts. Research LLM landscape 2026-04-30 valida migración parcial agresiva chinos.

**PRs:**
- PR-1 fe-swap-suggestions-api (cross-stack L) — cierra deudas S1 #1 (FE voice migration) + #2 (FE swap suggestions)
- PR-2 pure-expansion-providers (BE M) — 3 providers nuevos + drop static suggestions[] residual (cierra deuda S1 #3)
- PR-3 llm-cost-optimization (BE L) — DeepSeek V4-Flash classifier+summarizer + eval gate framework

**Research input:** `docs/pm-nico/research/2026-04-30-llm-landscape-chinese-models.md` veredicto migración parcial agresiva.

## 2026-04-30 — PR-1 shipped

**Decisión:** cierra deuda S1 PR-1 D-5 (FE legacy voice/transcribe call) + deuda S1 PR-2 FE swap stub suggestions. Verdicts BE PASS · FE PASS (post fix iter-1 prettier + display-name).

**Decisiones técnicas relevantes (vienen de CONTRACT 16 D-numbered, top 5):**
- D-3: asyncio.to_thread wraps sync engine — no bloquea event loop
- D-9: voice migration NO solo URL swap — D-9 adapter shape mandatorio (shapes incompatibles verificados código real)
- D-10/D-11: best-effort doble try/except (engine + EventBus), SuggestionShown emitido siempre (denominator métrica)
- D-13: mutation accept NO invalida queries (engine no re-rankea por accept individual)
- D-14: drop ROUTE_SUGGESTIONS map duplicado en SuggestedActions.tsx (cero deuda)

**Surface entregada:** 17 archivos, 37 tests nuevos, 0 migrations DB, 0 schema changes. 2 endpoints nuevos `POST /copilot/suggestions` + `POST /copilot/suggestions/accept`.

**Aprendizaje proceso:** S1 learning #8 confirmado en S2 — FE auditor stalled 600s. PM main thread completó manualmente quality gates + REVIEW-frontend.md. Patrón consistente — para FE PRs L+ planear main thread takeover audit por default.

## 2026-04-30 — PR-2 shipped

**Decisión:** cierra deuda S1 PR-2 D-9 (Q1 expansion vs additive pragmatic). Verdict PASS (PM main thread audit post builder truncation S1 learning #8 confirmado).

**Decisiones técnicas relevantes (CONTRACT 16 D-numbered, top 5):**
- D-2: `SalesAgentObservabilityPort` cross-module via `shared/links/ports/` (preserva ratchet copilot→sales_agent 0 entries — sin direct imports)
- D-6: `EnrollmentSummaryDTO` PII-stripped (sin contact_id, payment_link_url, pricing) — boundary §3 sales_agent
- D-7: `_no_data_response` + `_ok_response` refactor — `suggestions: list[str]` (engine) vs `next_step_hint: str | None` (LLM guidance) separados
- D-9: registry `_bootstrap_builtin` 4 providers orden estable (offer→brand→sales_agent→copilot)
- D-13: ratchet copilot→módulo 22 frozen — port-mediated cross-module preserva

**Surface entregada:** 26 archivos, 54 tests nuevos, 0 migrations DB, 0 schema changes. 3 providers nuevos + 1 port + 1 adapter + 2 abstract methods extension.

**Aprendizaje proceso:** S1 learning #8 confirmado segunda vez (PR-2 builder truncó mid-fix iter 1). PM main thread completó: lazy imports → module level (test mocking), 6 type ignores defensivos documentados, test design alignment para resilience pattern. Patrón cementado — para PRs M+ planear PM main thread takeover post primer trunc.

## 2026-04-30 — PR-3 shipped PARTIAL

**Decisión:** ship PARTIAL — infra LLM ready (model_config + DeepSeek provider + factory + eval gate framework + migration) sin wiring upstream. Wiring + tests T-2..T-8 + `.env.example` + Settings DEFERRED PR-4 cohesivo.

**Razón override "cero deuda":** builder truncó early (~170s, 81 tool uses). PM main thread takeover encontró bloque arquitectónico LLMProvider factory upstream NO ubicable sin discovery profundo. Trade-off: ship infra ready (auto-contenida funcional via CLI runner) + DEFERRED documentado vs forzar wiring sin verificación profunda + arriesgar regresión runtime classifier/summarizer en prod.

**Decisiones técnicas relevantes (CONTRACT 15 D-numbered, top 5):**
- D-1: env override layer model_config — cero modificación enum SSoT TIER_METADATA
- D-2: DeepSeekLLMProvider OpenAI-compatible directo (NO Together/Fireworks) — lower latency + adapter pattern preserva swap futuro
- D-9: migration alembic 114 idempotente ON CONFLICT WHERE NOT EXISTS pattern (natural-key valid_to=NULL)
- D-10: arch test sales_agent isolation guard — 0 imports sales_agent en copilot/llm + copilot/evals
- D-MAIN-1: PARTIAL ship justificado — cohesive auto-contained infra + explicit DEFERRED PR-4

**Surface entregada:** 21 archivos, 6 smoke tests verde, 1 migration idempotente, 100 goldens versionados.

**Aprendizaje proceso:** S1 learning #8 confirmado **TERCERA vez en S2** (todos los builders L+ truncan). Patrón CEMENTADO — para PRs L con scope ~25+ archivos, default plan = main thread takeover post-truncate (ya NO sorpresa). Considerar splittear PR-3 retrospectivamente en PR-3a (infra) + PR-3b (wiring) hubiera evitado PARTIAL ship.

**Decisión PI-2 next:** abrir S3-copilot-llm-wiring-runtime con PR-1 wiring (cierra deuda PR-3 PARTIAL). Si Chris autoriza, considerar también PR-2 multicanal (Bloque A Telegram bridge) o cerrar PI-2 y abrir PI-3 dedicado multicanal. Evaluación post handoff S2.

## Pendientes registrar

_Aquí se irán registrando decisiones tomadas durante discovery + ejecución._
