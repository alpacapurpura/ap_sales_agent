# Prompt copy-paste — Iniciar TP3

Abre una conversación NUEVA de Claude Code y pega el bloque fenced abajo. Single fenced block, self-contained. La conversación arranca leyendo este prompt → ejecuta paso 1 (pre-lectura) y paso 2 (pre-research) ANTES de tocar tools.

---

```
Iniciar TP3 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP3

Validar F4 (URL contextual + inspirations persistence) post-redesign 2026-04. Confirmar:
1. `fetch_url` extrae + persiste como `copilot_inspiration` row.
2. Inspiración referenciable cross-turn sin re-pegar URL (turn 7 igual que turn 2).
3. Card `inspiration_saved` aparece en UI ≤5s sin parpadeo.
4. Múltiples inspiraciones acumulan independientes en mismo conversation_id.
5. URL inválida/paywalled fail gracefully (sin exception bubbleada al user).
6. `pin_to_memory` tool persiste content + lo inyecta en próximos turns.
7. `brand_relevance_score` populated cuando brand_summary existe (F4 hook — soft fail si null).

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP3-url-contextual-inspirations.md`
8. `docs/domains/copilot/testing-2026-04/results/TP2-2026-04-25.md` (este reporte — aprendizajes + bugs heredados)
9. `docs/domains/copilot/redesign-2026-04/learnings/F4-*.md` (la fase del redesign que valida — buscarlo si no existe el path exacto)
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 2 web searches del mandate listado en `phases/TP3-url-contextual-inspirations.md §Research mandate` (trafilatura 2026 / persistent context window agent memory 2026 / web scraping ethics rate limit user-agent 2026). Tessl tiles: skill `tessl-context` para cualquier tile sobre web extract / agent memory abril 2026.

Si descubrís escenario crítico no listado en TP3 doc, agregalo a `phases/TP3-url-contextual-inspirations.md` ANTES ejecutar.

## Setup heredado (NO rehacer — verificado en TP1 + TP2 setup)

- Migraciones aplicadas hasta `072_copilot_workflow_metric` (head)
- DeepEval 3.9.7 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn — ver TP2 script `tp2_brand_coherence_eval.py`)
- `.env`: `CLERK_TEST_SESSION_ID=sess_3CoDlDaZ9wye8g5OISeyvwsYiRp` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY`
- Tenants test:
  - `c67c9845-6cf7-4aee-beba-7e177e84d167` (alpaca-2 / Alpaca Púrpura) — brand_summary populated v2 chars=580 (regenerado TP2-S2.4)
  - `9ba0b29a-8507-424f-a48a-896f93218a25` (visionarias-v4) — sin brand
- **TP1 fixes ya commiteados**:
  - `src/modules/copilot/domain/routing_policy.py` rule short_msg_no_tools sin `max_tools=0` guard
  - `src/modules/copilot/application/orchestrator/chat.py` helper `_build_turn_end_data` que persiste cache metrics
- **TP2 fixes ya commiteados** (incluir en próximo commit si todavía no commiteados al iniciar TP3):
  - `src/shared/workers/brand_summary_regen.py::regen_brand_summary` ARQ wrapper ahora commitea explícito + rollback en error
  - `tests/shared/workers/test_brand_summary_regen.py` 3 nuevos tests `_SessionCommitSpy`
  - `backend/scripts/tp2_brand_coherence_eval.py` driver script (reusable pattern para multi-turn judge en TP3+)

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "SELECT version, length(summary), updated_at FROM brand_summary WHERE tenant_id='c67c9845-6cf7-4aee-beba-7e177e84d167';"
```

Brand_summary debe estar populated (TP2 fix dependió de eso). Si está vacío, regenerar ANTES de arrancar TP3 (no debería pasar — TP2 dejó row v2):
```bash
docker exec -w /app visionarias_brain_dev bash -c "PYTHONPATH=/app python -c 'import src.main; from sqlalchemy.orm import configure_mappers; configure_mappers(); from uuid import UUID; from src.core.database import SessionLocal; from src.shared.workers.brand_summary_regen import regen_brand_summary_sync;
with SessionLocal() as db:
    regen_brand_summary_sync(db=db, tenant_id=UUID(\"c67c9845-6cf7-4aee-beba-7e177e84d167\"))
    db.commit()'"
```

## Patrón llamada API + SQL probes

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: c67c9845-6cf7-4aee-beba-7e177e84d167" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"<test>","conversation_id":null,"client_context":{"current_route":"/offer-studio"}}'
```

**Importante:** TP3 testea inspiraciones cargadas via URL — usar route `/offer-studio` (allowlisted lighthouse) para mantener brand context. SI la misión es probar inspirations en otra superficie, valida primero que el route esté en `_INJECTION_SEGMENTS` o documentá la decisión.

DB: `docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "..."`

SQL probes en `01-tooling.md §Infraestructura interna`. Tablas TP3: `copilot_inspiration`, `copilot_pinned_memory`, `copilot_trace_event`.

## Anomalías heredadas

### De TP1 (sin fix arquitectónico, infra-bound)

- **B2 — OpenAI tier 1 TPM 30k bloquea batches**: cualquier batch ≥2 turns en <60s gatilla 429. Mitigación: espaciar ≥35-40s entre turns o disparar en off-peak. TP3 fetch_url + LLM combo aprieta más TPM (más tokens en context post-extract). Confirmar si org tier OpenAI fue bumpeado antes de TP3.
- **F11.1 telemetry-only**: `routing_log.tier_selected` ≠ modelo real bound al graph (siempre gpt-4o). Cualquier assertion sobre cost/latency per tier debe usar `data->>'model'` real, no `routing_log.tier_selected`. Cutover diferido a F-pos.
- **B3 — cost calc no aplica cache discount**: `cost_usd` logged 2x el real. Si TP3 reporta cost, ajustar manualmente con factor `(1 - 0.5 × cache_hit_rate)`.

### De TP2 (sin fix — design observation)

- **A1 — Lighthouse route-gated por design**: `_INJECTION_SEGMENTS = ("offer-studio", "landing", "campaign", "sales", "growth-studio")`. `/dashboard` y `/brand-studio` excluidas. TP3 que ejecute desde routes fuera del allowlist no verá lighthouse — esperado, NO es bug.

## Aprendizajes accionables de TP2

- **B1 commit gap pattern**: cualquier ARQ wrapper que delega a un sync helper que sólo hace `flush()` necesita commit explícito en el wrapper. F3 expuso el pattern; TP3 debe verificar que `pin_to_memory`, `fetch_url` worker (si hay) y cualquier nuevo persist path siguen el contrato. El test `_SessionCommitSpy` en `tests/shared/workers/test_brand_summary_regen.py` es reutilizable como patrón.
- **Lighthouse route-gated**: cualquier scenario TP3 que asuma "el copilot ya conoce la marca" debe correr en route allowlisted (`/offer-studio /landing /sales /growth-studio`). Si TP3 dispara desde `/dashboard`, brand_coherence va a degradar — testear desde superficies productivas.
- **ARQ result key dedupe stale**: cuando se fixea un worker bug y se quiere re-disparar la misma tenant_id+task, hay que limpiar `arq:result:{job_id}` manualmente o esperar `keep_result` expiry (~1h default). Sin esto, el re-enqueue es silently rejected. Para TP3, si tocás workers, agregar al playbook: `docker exec visionarias_redis redis-cli -n 0 DEL "arq:result:..."` antes de re-test.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + boot full app (mappers).
7. Stage por nombre en commits (parallel-safety).

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP3-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP4** (1-3 bullets accionables o omitir si no hay).
2. `docs/domains/copilot/testing-2026-04/prompts/TP4-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP4 (ask_tenant_data, F5), research mandate de `phases/TP4-ask-tenant-data.md`, anomalías heredadas si las hay.
3. Si `phases/TP3-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP4-start.md`.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research.
- Mockear LLM cuando TP exige real-LLM (S3.3 Chrome DevTools obligatorio para card UI).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP4 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP4).
- Embeber el prompt TP4 dentro del reporte `results/TP3-*.md` — vive en `prompts/TP4-start.md`, el reporte sólo referencia el path.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn (TP2 script driver patrón).
- ARQ task no corre tras enqueue → check `arq:result:{job_id}` stale + `docker logs visionarias_worker`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2. Recién después tocás tools.
```
