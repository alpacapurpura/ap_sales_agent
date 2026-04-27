# Prompt — FP3 start

Copy-paste el fenced block siguiente en una conversación nueva de Claude Code.

```
Iniciar FP3 plan fpos-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión FP3

Cerrar B25-TP11: routing classifier NANO call corre sequencial al model warm-up + bind tools, agregando ~2.7s al TTFB block_start (J1.T1 medido 2.77s vs target 1500ms 2026 conversational breaking point). Refactor `chat.py::stream_chat` para ejecutar `_record_routing_decision` en paralelo con build_deep_agent_graph + first model invocation. Race condition guard si tier change cambia tools binding mid-flight (broad superset bind eager + filter dynamically). H1 inmediatez PASS (TTFB ≤800ms p50, ≤2000ms p95).

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/fpos-2026-04/README.md`
2. `docs/domains/copilot/fpos-2026-04/02-fpos-plan.md`
3. `docs/domains/copilot/fpos-2026-04/04-protocol.md`
4. `docs/domains/copilot/fpos-2026-04/phases/FP3-routing-parallel-ttfb.md`
5. `docs/domains/copilot/fpos-2026-04/results/FP2-2026-04-27.md` (aprendizajes corrida previa, especialmente §Aprendizajes para FP3)
6. `docs/domains/copilot/fpos-2026-04/results/FP1-2026-04-26.md` (contexto FP1 cerrado — port pattern + handler registry)
7. `docs/domains/copilot/testing-2026-04/results/TP11-2026-04-26.md` (origen B25 §B25-TP11)
8. `docs/domains/copilot/testing-2026-04/04-protocol.md` (protocolo padre)
9. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md` + `.claude/rules/backend-ddd.md` + `.claude/rules/parallel-safety.md`
10. `backend/src/modules/copilot/application/orchestrator/chat.py` (`stream_chat` + `_record_routing_decision` + `_run_graph_stream`)
11. `backend/src/modules/copilot/application/router/__init__.py` + `routing/router_factory.py` (LLMClassifier + `build_default_router`)
12. `backend/src/modules/copilot/application/orchestrator/deep_agent.py` (post-FP2: `_build_combined_system_prompt` ya wirea `_build_channel_intent_hint`)
13. `backend/src/modules/copilot/infrastructure/repositories/routing_log_repository.py`

## Pre-research obligatorio

Mínimo 2 web searches del Research mandate listado en `phases/FP3-routing-parallel-ttfb.md §Research mandate`:
- `asyncio gather race condition LLM streaming agent 2026`
- `langgraph speculative tool binding 2026 swap mid-stream`
- `llm tier classifier eager vs lazy decision 2026`

Tessl tiles: `tessl__langgraph` (concurrency hooks) — deepagents 0.5.3 sobre langgraph 0.6+.

## Setup heredado (NO rehacer — verificado en FP2)

- TP11 cerrado, B23-TP11 voseo system prompts fix vivo (commit `ed18daef`).
- **FP1 cerrado:** `MutationApplyService` + `BrandFieldApplyPort` + ProposalCard fallback + idempotency live (migration 074).
- **FP2 cerrado:** `channel_intent_detector` + `state["channel_intent"]` + `_build_channel_intent_hint` en `deep_agent.py`. Tool `format_for_channel` triggers 100% post-fix con prompts de contexto razonable.
- Tenant test primario: visionarias-v4 `9ba0b29a-8507-424f-a48a-896f93218a25` (tenant_profile completo, brand_summary 0).
- Sprint 0 routing: AGENT=Kimi K2.6 (no-thinking, temp 0.6) + REASONING=DeepSeek + NANO/FAST=OpenAI.
- deepagents 0.5.3.
- Span tree B15-TP8 vivo + plan_card B18-TP9 vivo + ROUTE_TOOL_MAP B20-TP10 wired + channel_intent middleware FP2 wired.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepagents; print(deepagents.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:3000
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs

# CRÍTICO FP3 — verificar baseline timing pre-refactor:
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
TENANT="9ba0b29a-8507-424f-a48a-896f93218a25"
CONV=$(.venv/bin/python -c "import uuid; print(uuid.uuid4())")
time curl -sS -N -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" -H "X-Tenant-ID: $TENANT" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\":\"hola\",\"conversation_id\":\"$CONV\",\"context\":{\"current_route\":\"/${TENANT}\",\"selected_fields\":[],\"form_data\":{},\"locale\":\"es\"}}" \
  --max-time 30 | grep -E "block_start|message_start" | head -3

# SQL probe baseline:
docker exec visionarias_postgres psql -U postgres -d visionarias_logs --pset=pager=off \
  -c "SELECT name, duration_ms FROM copilot_trace_event WHERE conversation_id = '$CONV' ORDER BY created_at;"
```

## Aprendizajes accionables de FP2

1. **`detect_channel_in_user_msg` patrón regex normalizada vive ahora en `channel_intent_detector.py`** como SSoT con AC7 URL guard. Cualquier middleware FP3 que necesite distinguir "user wants something specific" vs "URL mention" puede reusar el lookbehind `://` + lookahead `\.com|/` pattern.

2. **Hint strength = phrasing-sensitive con Kimi K2.6.** Drafts con tono blando los ignora ~30% del tiempo. Tono "REGLA OBLIGATORIA + NUNCA … antes de …" trigger 100% en re-runs. Pattern replicable: cualquier nudge al LLM debe ser **imperativo + explícito + ejemplo**. Pre-research insight 2026: "agentic prompts work like contracts, not suggestions."

3. **System prompt hint = wiring barato (~400 tokens), latency cero.** Alternativa `tool_choice="required"` requeriría refactor invasive. Para FP3 routing parallel, considerar mismo pattern: **bind eager superset de tools + dynamic routing decisión via state mutation**, en lugar de swap del graph compilado mid-flight. Patrón "fail-fast en wiring, decide-late en runtime" que FP1+FP2 confirman replicable.

## Anomalías heredadas FP2

- **Sub-FP2.1 (DEFERRED):** hint strength con zero-context prompts ("armame copy WhatsApp" sin extras) puede aún disparar clarification request. Mitigación post FP2 = monitor logs; si rate "ask-clarification antes de generar" > 20%, considerar `tool_choice="required"` cuando intent detectado. NO bloquea FP3.

## Anomalías heredadas FP1 (siguen aplicables)

- **Sub-FP1.1 (DEFERRED):** offer + buyer_persona handlers requieren `entity_id` extension. Brand domain solo en FP1. FP3 no lo destraba.
- **Sub-FP1.3 (HEREDADO TP4):** 3 tests pre-existentes flaky (`test_conversation_count_question`, `test_lead_count_question_returns_number`, `test_route_tool_selection_matches_baseline`). NO bloquean FP3.

## Reglas non-negotiables

1. Acceptance criteria mandatorio (no scenarios+5 ejes — eso es TP).
2. TDD obligatorio: test RED → fix → GREEN.
3. Root cause obligatorio. NO `# noqa`, NO `pytest.skip`, NO mock-tape-error.
4. Before/After evidence en results — sin TTFB ms numbers, AC no se cierra. Medir con `time.monotonic_ns()` deltas + Chrome DevTools network panel.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native-first WSL — lint/tests/eval native, NUNCA `docker exec` para lint/tests/type-check.
7. Stage por nombre commits (parallel-safety §Scope commits).
8. Tenant isolation en cualquier nuevo middleware (regla `tenant-isolation.md`).
9. F1 ratchet — NO direct cross-module imports desde copilot. Port pattern obligatorio si necesitás otro module.
10. **AC4 race condition guard CRÍTICO:** si tier change cambia tools binding mid-flight, NO permitir missing tools en bound set. Test integración con simulated tier change debe PASS.
11. **AC6 quality regression check:** judge avg ≥4.0 mantained post-refactor. Sample mínimo 10 turns.

## Output esperado al cerrar FP3 (ÚLTIMO del batch F-pos)

1. `docs/domains/copilot/fpos-2026-04/results/FP3-{YYYY-MM-DD}.md` con:
   - Pre-research insights
   - AC1-AC6 checklist con before/after evidence (TTFB ms numbers)
   - Tests added (count + paths)
   - Sub-bugs descubiertos (si los hubo)
   - Métricas: TTFB delta + tokens delta + cost delta + judge avg sample
   - **§Cierre F-pos batch:** resumen agregado de FP1-FP4 + score post-fixes (target 8/8) + recomendación de re-run TP11 selectivo (J1, J2, J4) para confirmar score sí alcanzado.
2. **NO se genera `prompts/FP4-start.md`** — FP3 cierra el batch (FP4 ya ejecutado en paralelo con FP1, OR ejecutar FP4 después si pendiente).
3. Si re-run TP11 confirma score 8/8, archivar plan `fpos-2026-04/` + actualizar `redesign-2026-04/learnings/F-pos-summary.md`.
4. Commits conventional + push origin/development:
   - `perf(copilot-fpos3): routing classifier parallel a model warm-up (B25)`
   - Tests + docs en su commit propio si crece mucho.
5. Reporte al user: 3 líneas resumen + score H1 mejora + paths a results/.

## Anti-patrones (no caer)

- Reportar AC sin TTFB ms numbers concretos (medir con `time.monotonic_ns` o Chrome DevTools network panel).
- Mockear LLM para evitar medir TTFB real — el bug es perceptual del usuario.
- Cerrar FP3 con sub-bug abierto sin TDD (sub-FP3.X).
- Spawnear sub-agentes para AC paralelos (FP necesita context completo + fix iteration).
- Bind narrow tools eager esperando swap perfecto — race condition guaranteed. Bind superset mejor.
- Llenar reporte con info no accionable.

## Si te trabás

- Routing log row no aparece → SQL probe `copilot_routing_log WHERE message_id = '$MSG_ID'` ver si insert falló.
- Quality regression sospechosa → re-run J3+J4+J5 selectivos TP11 mismas prompts; comparar judge dim scores.
- Race condition tools binding → test debe simular `await asyncio.sleep(0.5)` en classifier mock + assert tools coherentes en bound set.
- Build deep agent graph heavy + síncrono → si dominates latency, lazy graph compile (sub-FP3.X).
- TTFB no baja a target → revisar si NANO call es realmente el bottleneck (puede ser routing log DB write, prompt build, o LLM connect TTFB).

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + baseline TTFB measurement. Recién después tocás tools.
```
