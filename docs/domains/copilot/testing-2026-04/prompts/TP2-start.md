# Prompt TP2 — copy-paste a nueva conversación

> Generado al cierre de TP1 (2026-04-25). Misión + research mandate vienen de `phases/TP2-brand-summary-lighthouse.md`. Anomalías heredadas + aprendizajes accionables vienen de `results/TP1-2026-04-25.md`.

---

```
Iniciar TP2 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP2

Validar F3 (brand "lighthouse" always-on en system prompt) post-redesign 2026-04. Confirmar:
1. Brand summary aparece en system prompt sin que el user lo pida (lighthouse).
2. Judge `brand_coherence` ≥4.0 across 20 variations (brand voice/tono/posicionamiento consistente cross-turn).
3. La reorden F8 §5.2 (lighthouse en slot 3 cacheable, no slot 1) no degradó la coherence brand.
4. Tenants sin `brand_summary` populated no rompen el flow (graceful degradation).
5. Lighthouse content respeta Spanish neutro LatAm (regla 11) — sin voseo si el tenant pidió neutro.

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP2-brand-summary-lighthouse.md`
8. `docs/domains/copilot/testing-2026-04/results/TP1-2026-04-25.md` (este reporte — aprendizajes + bugs heredados)
9. `docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary.md` (la fase del redesign que valida)
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 2 web searches del mandate listado en `phases/TP2-brand-summary-lighthouse.md §Research mandate`. Tessl tiles: skill `tessl-context` para cualquier tile sobre brand voice eval / multi-turn coherence eval abril 2026.

Si descubrís escenario crítico no listado en TP2 doc, agregalo a `phases/TP2-*.md` ANTES ejecutar.

## Setup heredado (NO rehacer — verificado en TP1 setup + TP1 fixes)

- Migraciones aplicadas hasta `072_copilot_workflow_metric` (head)
- DeepEval 3.9.7 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh)
- `.env`: `CLERK_TEST_SESSION_ID=sess_3CoDlDaZ9wye8g5OISeyvwsYiRp` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY`
- Tenant test: `9ba0b29a-8507-424f-a48a-896f93218a25` (visionarias-v4)
- **TP1 fixes ya commiteados**:
  - `src/modules/copilot/domain/routing_policy.py` rule short_msg_no_tools sin `max_tools=0` guard
  - `src/modules/copilot/application/orchestrator/chat.py` helper `_build_turn_end_data` que persiste cache metrics

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
```

## Patrón llamada API + SQL probes

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 9ba0b29a-8507-424f-a48a-896f93218a25" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"<test>","conversation_id":null}'
```

DB: `docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "..."`

SQL probes en `01-tooling.md §Infraestructura interna`. Para inspect system prompt fragments use `compose_system_prompt(...)` + assert `lighthouse_block` en posición esperada.

## Anomalías heredadas de TP1

- **B2 — OpenAI tier 1 TPM 30k bloquea batches**: cualquier batch ≥2 turns en <60s gatilla 429. Mitigación: espaciar ≥35s entre turns o disparar en off-peak. Si persiste, escalar tier OpenAI org.
- **F11.1 telemetry-only**: `routing_log.tier_selected` ≠ modelo real bound al graph (siempre gpt-4o). Cualquier assertion sobre cost/latency per tier debe usar `data->>'model'` real, no `routing_log.tier_selected`. Cutover diferido a F-pos.
- **B3 — cost calc no aplica cache discount**: `cost_usd` logged 2x el real. Si TP2 reporta cost, ajustar manualmente con factor `(1 - 0.5 × cache_hit_rate)`.

## Aprendizajes accionables de TP1

- Helper `_build_turn_end_data` persiste cache metrics post-2026-04-25. Filter SQL `created_at >= '2026-04-25T22:00Z'` para data limpia.
- Plan-vs-impl drift: F8 routing keywords NO cubren todos los verbos esperados (`diseña`, `compara` sin tilde). Si TP2 brand work requiere REASONING tier, agregar rule en F-pos.
- TP1 fixes hot-reloaded en uvicorn — confirmar que el container `visionarias_brain_dev` está corriendo el código actualizado al iniciar TP2 (touch `src/main.py` si no).

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec`.
7. Stage por nombre en commits (parallel-safety).

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP2-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP3** (1-3 bullets accionables o omitir si no hay).
2. `docs/domains/copilot/testing-2026-04/prompts/TP3-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP3, research mandate de `phases/TP3-url-contextual-inspirations.md`, anomalías heredadas si las hay.
3. Si `phases/TP2-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP3-start.md`.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research.
- Mockear LLM cuando TP exige real-LLM.
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP3 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP3).
- Embeber el prompt TP3 dentro del reporte `results/TP2-*.md` — vive en `prompts/TP3-start.md`, el reporte sólo referencia el path.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2. Recién después tocás tools.
```
