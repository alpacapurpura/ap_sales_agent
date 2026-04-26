# TP4 start prompt

Copy-paste lo siguiente en una conversación nueva de Claude Code (`development`):

```
Iniciar TP4 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP4

Validar F5 (`ask_tenant_data` subgraph: intent → resolve → query → state-check → synthesize, 2 LLM calls FAST). Confirmar:
1. Preguntas naturales devuelven respuesta correcta SIN SQL crudo en prompt.
2. Subgraph resuelve fuzzy matching ("oferta de cocina" → "Curso de Cocina Vegetariana") + fechas relativas ("esta semana", "últimos 30 días").
3. State-check intercepta empty: "no encontré leads…" en vez de inventar número.
4. Latencia ≤1.5s p50 (subgraph + 2 FAST calls).
5. Groundedness ≥4.5: cero alucinaciones de números (DeepEval `FaithfulnessMetric` ≥0.85 avg).

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP4-ask-tenant-data.md`
8. `docs/domains/copilot/testing-2026-04/results/TP3-2026-04-26.md` (este reporte — aprendizajes + bugs heredados + anomalía A1 quota CRÍTICA)
9. `docs/domains/copilot/redesign-2026-04/learnings/F5-ask-tenant-data.md`
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP4-ask-tenant-data.md §Research mandate`:
- `text to SQL agent evaluation 2026 fuzzy matching benchmark`
- `deepagents text-to-sql-agent example 2026`
- `natural language data query LLM hallucination groundedness 2026`

Tessl tiles: skill `tessl-context` para tiles sobre text-to-SQL eval / DeepEval Faithfulness abril 2026.

Si descubrís escenario crítico no listado en TP4 doc, agregalo a `phases/TP4-ask-tenant-data.md` ANTES ejecutar.

**Sanity check API real (lección TP3 S3.7):** ANTES de ejecutar S4.x, leer la signature real de `ask_tenant_data` en `backend/src/modules/copilot/application/tools/ask_tenant_data/__init__.py` y comparar con lo que cada escenario asume. Si difieren, ajustar el phase doc PRIMERO antes de correr.

## Setup heredado (NO rehacer — verificado en TP1+TP2+TP3)

- Migraciones aplicadas hasta `072_copilot_workflow_metric` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn)
- `.env`: `CLERK_TEST_SESSION_ID=sess_3CoDlDaZ9wye8g5OISeyvwsYiRp` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY`
- Tenants test:
  - Lighthouse poblado: `c67c9845-6cf7-4aee-beba-7e177e84d167` (alpaca-2 / Alpaca Púrpura) — brand_summary v2 chars=580
  - Sin brand: `9ba0b29a-8507-424f-a48a-896f93218a25` (visionarias-v4)
- **Fixes ya commiteados (TP1+TP2+TP3, antes de empezar TP4 si quedaron sin push):**
  - TP1: `routing_policy.py short_msg_no_tools` sin `max_tools=0` guard; `chat.py::_build_turn_end_data` persiste cache metrics.
  - TP2: `src/shared/workers/brand_summary_regen.py::regen_brand_summary` ARQ wrapper commitea + rollback en error.
  - **TP3 B1**: nuevo módulo `src/modules/copilot/application/orchestrator/stream_filters.py` con `INTERNAL_LLM_CONFIG` + `is_internal_llm_event`; `chat.py::_process_stream_event` filtra; `url_inspiration_analyzer`, `ask_tenant_data/synthesizer`, `ask_tenant_data/intent_classifier` pasan tag.
  - **TP3 B2**: `inspiration_saved` + `memory_pinned` registrados en `_TYPE_TO_CARD_KIND`, `CardBlock.card_kind` Literal y `CARD_PAYLOAD_MODELS`.
  - **TP3 B3**: helper `chat._parse_tool_payload` desempaqueta `ToolMessage` para que `ui_action` y `block_append` SE EMITAN.
  - **TP3 B4**: filtro de zombie AIMessages en `_serialize_messages` (single-char content sin tool_calls).

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "SELECT version, length(summary), updated_at FROM brand_summary WHERE tenant_id='c67c9845-6cf7-4aee-beba-7e177e84d167';"
# CRÍTICO TP4 — confirmar quota OpenAI antes de arrancar (TP3 A1 bloqueó S3.6+S3.7+S3.8 E2E):
.venv/bin/python -c "
from openai import OpenAI; c=OpenAI();
r=c.chat.completions.create(model='gpt-4o-mini', messages=[{'role':'user','content':'ping'}], max_tokens=5)
print('quota OK', r.choices[0].message.content)
"
```

Si la última línea falla con `insufficient_quota` → resolver billing antes de empezar TP4 (recargar saldo o key alternativa). TP4 dispara 2 LLM internos por turn (`intent_classifier` + `synthesizer`) — quota bloqueado = TP4 entero bloqueado.

## Patrón llamada API + SQL probes

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: c67c9845-6cf7-4aee-beba-7e177e84d167" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"<test>","conversation_id":null,"client_context":{"current_route":"/sales"}}'
```

**Importante TP4:** TP3 A3 confirmó lighthouse route-gated. Para data Q&A puede convenir route `/sales` o `/growth-studio` (ambas allowlisted). Para preguntas de offers usar `/offer-studio`.

DB: `docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "..."`

SQL probes en `01-tooling.md §Infraestructura interna` + `phases/TP4-ask-tenant-data.md §Tools / queries`. Tablas TP4: `crm_leads`, `offers`, `enrollments` para ground truth + `copilot_trace_event` para per-node duration.

## Anomalías heredadas (de TP1+TP2+TP3)

### CRÍTICA TP4 — A1 (TP3): OpenAI quota agotada cortó TP3 mid-corrida

`insufficient_quota` HTTP 429 (account-level, NO tier rate limit). Bloqueó S3.6+S3.7+S3.8 E2E. TP4 hace 2 LLM calls por turn — confirmar recarga billing ANTES.

### A2 (TP3) — Voseo en strings user-facing F4 (sweep separado pendiente)

10+ strings detectados en `src/modules/copilot/application/tools/{fetch_url,pin_to_memory}.py`, `infrastructure/web/trafilatura_client.py`, `application/orchestrator/inspirations_layer.py`. NO bloqueante TP4 directamente, pero si TP4 toca prompts de F5 (intent_classifier, synthesizer), aplicar regla 11 antes commit.

### A3 (heredado TP2 design) — Lighthouse route-gated `/dashboard /brand-studio` excluidos

`_INJECTION_SEGMENTS = ("offer-studio", "landing", "campaign", "sales", "growth-studio")`. TP4 desde `/sales` o `/growth-studio` mantiene lighthouse en system prompt; desde `/dashboard` no. NO es bug.

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k → spacing ≥35-40s entre turns

Sigue activo. TP4 con 10 turns (S4.7) requiere ~7 min wall-clock mínimo. Considerar bumpear tier antes si quota A1 también se ataca.

### A5 (heredado TP1 B3) — `cost_usd` en `turn_end` no aplica cache discount

Reportar cost ajustado: `cost_real ≈ cost_log × (1 - 0.5 × cache_hit_rate)`.

## Aprendizajes accionables de TP3

- **Internal LLM tag pattern (B1)**: cualquier tool que invoca un LLM como parte de su pipeline DEBE pasar `INTERNAL_LLM_CONFIG` desde `src/modules/copilot/application/orchestrator/stream_filters.py`. Sin la tag, `astream_events` filtra los tokens al canal user-visible. F5 ya hereda en sus 2 tools post-B1; cualquier helper LLM nuevo en TP4 (e.g. fuzzy resolver con LLM) repetir el patrón.
- **ToolMessage parsing (B3)**: graph tools devuelven `ToolMessage` objects. Cualquier orquestador downstream que necesite leer payload usar `chat._parse_tool_payload(tool_output)`. F5 va a emitir cards (`metric_summary` o equivalente data-snippet); precisa este unwrap.
- **Phase doc sanity check pre-ejecución**: TP3 S3.7 asumía `pin_to_memory(content="...")` pero la API real es `pin_to_memory(slug=...)`. Ejecutar el escenario primero hubiera quemado tokens. Antes de cada S4.x: leer signature real del subgraph + ajustar phase doc si difiere.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + boot full app (mappers).
7. Stage por nombre en commits (parallel-safety).

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP4-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP5** (1-3 bullets accionables o omitir si no hay).
2. `docs/domains/copilot/testing-2026-04/prompts/TP5-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP5 (workflows-runtime, F6), research mandate de `phases/TP5-workflows-runtime.md`, anomalías heredadas.
3. Si `phases/TP4-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP5-start.md`.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o quota probe.
- Mockear LLM cuando TP exige real-LLM (S4.8 DeepEval Faithfulness obligatorio para groundedness).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP5 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP5).
- Embeber el prompt TP5 dentro del reporte `results/TP4-*.md` — vive en `prompts/TP5-start.md`, el reporte sólo referencia el path.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn.
- OpenAI 429 quota → confirmar billing recargado (TP3 A1 documenta).
- ARQ task no corre tras enqueue → `arq:result:{job_id}` stale + `docker logs visionarias_worker`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + quota probe. Recién después tocás tools.
```
