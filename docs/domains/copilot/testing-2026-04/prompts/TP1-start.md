# Prompt TP1 — copy-paste a nueva conversación

> Generado durante setup TP1 (2026-04-25). Para TP{N≥2}, copiar desde `results/TP{N-1}-{fecha}.md §Prompt para TP{N}` (handoff self-contained, ver `04-protocol.md §Anexo A`).

---

```
Iniciar TP1 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP1

Validar F8 (LLMClassifier + cache prefix + 4-tier router) + F11.1 (wire al chat orchestrator) post-redesign 2026-04. Confirmar:
1. Cada turn emite row en `copilot_routing_log`
2. Tier matchea heurísticas (NANO/MINI/REASONING/HEAVY)
3. Cache hit rate ≥60% post-warmup
4. Admin `/copilot-routing` muestra distribución
5. LLMClassifier NO se activa cuando rule classifier matchea

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md` ← endurecido §4.4 + §reglas + §Anexo A (template handoff)
7. `docs/domains/copilot/testing-2026-04/phases/TP1-routing-tier-selection.md`
8. `docs/domains/copilot/redesign-2026-04/learnings/F8-*.md` + `F11-*.md`
9. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 2 web searches del mandate TP1:
- `"openai prompt caching cache_read pricing 2026 minimum tokens"`
- `"intent classification threshold confidence routing 2026"`
- `"langchain usage_metadata cache_read input_token_details 2026"`

Si pricing/threshold cambió → ajustar targets antes de ejecutar.

Tessl tiles: skill `tessl-context` para `tessl__pytest-api-testing` + cualquier tile sobre LLM eval/observability abril 2026.

Si descubrís escenario crítico no listado en TP1 doc, agregalo a `phases/TP1-routing-tier-selection.md` ANTES ejecutar.

## Setup ya hecho (NO rehacer — verificado 2026-04-25)

- Migraciones 071+072 aplicadas (workflow_state JSONB + workflow_metric)
- DeepEval 3.9.7 native venv + docker dev (NO prod)
- `backend/tests/quality/deepeval/__init__.py` + `conftest.py` (skip salvo `RUN_DEEPEVAL=1`)
- Conftest fix: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Bugs arch fixeados: `deep_agent.py` factory.get_client(temperature=) + `trace_recorder.py` set_session_factory
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh)
- `.env`: CLERK_TEST_SESSION_ID=sess_3CoDlDaZ9wye8g5OISeyvwsYiRp + CLERK_SECRET_KEY + OPENAI_API_KEY
- Tenant test: `9ba0b29a-8507-424f-a48a-896f93218a25` (visionarias-v4)

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short  # tree limpio en development
docker compose ps   # api_dev/postgres/client_dev healthy
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"  # 3.9.7
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30  # JWT prefix
```

Si algo falla → resolver infra primero, NO arrancar TP.

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

SQL probes en `01-tooling.md §Infraestructura interna`.

## Anomalías ya detectadas (validar cuando S1.x las toque)

- **A2**: classifier=`llm` para "hola" (3 chars) — debería matchear rule `short_msg_no_tools`. Validar S1.3 + fix root cause.
- **A3**: `turn_end` puede reportar status=ok cuando stream emitió error — recorder no captura. Si reaparece, fix recorder ANTES síntoma (`copilot-resilience.md`).

## Bug latente PROD documentado (NO scope TP1)

`docs/mejoras-proceso/to-do.md` entry "PROD recorder DNS-retry latente" — info para context, no fixear acá.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec`.
7. Stage por nombre en commits (parallel-safety).

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP1-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir secciones obligatorias:
   - **§Aprendizajes para TP2** — 1-3 bullets accionables o omitir si no hay.
   - **§Prompt para TP2** — generado siguiendo template canónico `04-protocol.md §Anexo A`. Adaptado: misión TP2, research mandate de `phases/TP2-brand-summary-lighthouse.md`, anomalías heredadas si las hay.
2. Si `phases/TP1-*.md` cambió → commit incluido.
3. Commits conventional: `test(copilot-tp1): ...` o `fix(copilot-{module}): ... (TP1)`.
4. Push a `origin/development`.
5. Reporte al user: 3 líneas resumen + path al `results/`. NO necesitás generar el prompt TP2 manualmente — ya está en el reporte.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research "porque ya sé el tool".
- Mockear LLM cuando TP1 exige real-LLM (S1.4-S1.7 cost/latency real).
- Cerrar TP con fail abierto sin fix arquitectónico.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar el reporte con info no accionable.
- Generar §Prompt para TP2 sin abrir `phases/TP2-*.md` (misión + research son específicos del TP2).

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- DeepEval falla raro → versión `01-tooling.md`.
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2. Recién después tocás tools.
```
