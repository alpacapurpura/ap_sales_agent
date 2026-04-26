Iniciar TP9 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP9

Validar F2 (`langchain-deepagents` harness + `write_todos` tool + scratchpad + subagentes). Confirmar:

1. `write_todos` tool emite `plan_card` con todos visibles cuando tarea es multi-step.
2. Scratchpad (read_file/write_file/edit_file/ls/glob/grep) funciona dentro del turn sin cross-conversation leak.
3. Subagentes (`audit_inspector`, `url_analyzer`, `data_query`) corren aislados y devuelven a parent agent.
4. Tareas chicas NO disparan write_todos (no over-engineering).
5. Spanish neutro LatAm respetado en plan_card content (regla 11).
6. **Span tree TP8-B15 fix sigue vivo** — cada tool call + subagent invocation populée span_id + parent_span_id (sino plan_card progress + subagent isolation no son auditables tree-shaped).
7. **Pre-flight schema drift check** — `pip show deepagents` + smoke test del `write_todos` + `task` tool surface antes de scenario crítico (lección B12+B14-TP8 reforzada).

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP9-deep-agent-planning.md`
8. `docs/domains/copilot/testing-2026-04/results/TP8-2026-04-26.md` (B14+B15+B17 fixes commiteados, span tree wiring vivo, recommendaciones)
9. `docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md`
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`
11. **TP8 commits (`git log --oneline -8`):** B14-TP8 qdrant stats schema fix / B15-TP8 node_trace span tree / B17-TP8 accuracy rubric scope-refusal / TP8 results doc + TP9 start prompt.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP9-deep-agent-planning.md §Research mandate`:
- `langchain deepagents 2026 latest version changelog`
- `agent planning visible plan card UX 2026 patterns`
- `subagent isolation context window 2026 langchain`

Tessl tiles: skill `tessl-context` para tile sobre langchain / langgraph deep agents si existe.

Si descubrís escenario crítico no listado en TP9 doc, agregalo a `phases/TP9-*.md` ANTES ejecutar (lección TP6+TP7+TP8 reforzada).

**Sanity check API real (lección TP3-TP8 reforzada — NO SKIPEAR):** ANTES de ejecutar S9.x, leer la signature real de:
- `backend/src/modules/copilot/application/orchestrator/deep_agent.py::build_deep_agent_graph` (post Sprint 0 — `LLMFactory.get_client(ModelRole.AGENT, temperature=0.6)` directo, no `.bind()`)
- `backend/src/modules/copilot/application/orchestrator/subagents.py` — AUDIT_INSPECTOR_SUBAGENT + URL_ANALYZER_SUBAGENT + DATA_QUERY_SUBAGENT shapes
- `backend/src/modules/copilot/application/observability/node_trace.py::emit_node_trace_event` (post B15-TP8 — propaga run_id/parent_ids)
- `backend/src/modules/copilot/application/orchestrator/chat.py` (`_maybe_emit_plan_card` + `_handle_tool_end_v2` cards de planning)

Confirmar:
1. write_todos tool sigue registrado (deepagents builtin) y emit plan_card via `_maybe_emit_plan_card`.
2. 3 subagentes (`audit_inspector`, `url_analyzer`, `data_query`) registrados en `subagents=[...]` del create_deep_agent.
3. Span tree post B15-TP8 propaga parent_span_id en TODAS las node transitions (incluyendo tool/subagent boundaries).

Si encontrás divergencias vs phase doc TP9, ajustar phase doc PRIMERO antes de correr.

**Sanity check verification deterministic (lección TP6-TP8 reforzada):** TP6 destapó tool_call ≠ tool result usado. TP7 destapó test stub != arquitectura real. TP8 destapó schema drift silent + span tree gap silent. Para TP9 deep-agent:
- Contar `write_todos` invocations NO basta — verificar que `card_emitted card_kind='plan_card'` se emite + payload tiene `todos[]` populated.
- Verificar que subagent task tool emite span tree con parent = main agent run_id (sino isolation no es auditable).
- Si plan_card aparece pero `todos[]` vacío, sospechar que `_maybe_emit_plan_card` extrae mal el payload del tool result.
- Si `pip show deepagents` muestra version != prod expected, hard fail antes de scenarios — fix infra primero.

## Setup heredado (NO rehacer — verificado en TP1+TP2+TP3+TP4+TP5+TP6+TP7+TP8 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn — TP6+TP7+TP8 confirmó refresh ~40s necesario)
- `.env`: `CLERK_TEST_SESSION_ID` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` + Sprint 0 vars (DEEPSEEK_API_KEY + KIMI_API_KEY + DASHSCOPE_API_KEY + AI_PROVIDER_<ROLE>)
- Tenants test:
  - **alpaca-2** `c67c9845-6cf7-4aee-beba-7e177e84d167` — brand_summary v2 (580 chars). **Tenant primario TP6+TP7+TP8.**
- TP1+TP2+TP3+TP4+TP5+TP6+TP7+TP8 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) façade.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key`.
- TP4-TP8 confirma routing live: REASONING DeepSeek, AGENT Kimi K2.6 (no-thinking + temp 0.6), NANO/FAST OpenAI gpt-4o-mini.

### NUEVO TP6 fixes
- B7-TP6 voseo cross-channel arch fix (3 capas defensa: static.j2 + synthesizer.py fallbacks + output_sanitizer.correct_voseo_in_text 50+ formas).
- B8-TP6 SMS overflow arch fix (output_sanitizer detect_channel_in_user_msg + enforce_channel_format_if_needed).
- copilot_system_tools_hint.j2 — channel formatter section.

### NUEVO TP7 fixes
- B12-TP7 Qdrant REST fallback en marketing_kb_store.search (httpx httpx POST `/collections/{name}/points/search`). Cross-module sales_agent + brand stores también requieren bump server o fallback.
- B13-TP7 judge dynamic prompt builder + `_DIMENSION_RUBRICS` registry. RAG dim coverage funciona end-to-end.
- KB seedeado: `nicolify_marketing_kb` 304 chunks / 31 docs.

### NUEVO TP8 fixes
- **B14-TP8 qdrant stats schema** — `MarketingKbStore.stats()` drop `vectors_count` (qdrant-client 1.17 dropped field). Admin marketing_kb.py col layout 4→3. Comentario inline `B14-TP8`.
- **B15-TP8 span tree propagation** — `emit_node_trace_event` propaga `event.run_id` como span_id + `event.parent_ids[-1]` como parent_span_id. node_enter/exit pares ahora comparten span_id. Tree reconstruible. Comentario inline `B15-TP8`.
- **B17-TP8 accuracy rubric scope-refusal** — `_DIMENSION_RUBRICS["accuracy"]` extendido para reconocer "redirect honesto cuando la pregunta queda fuera del rol del asistente" como score 5. Goldens `error_recovery_003_off_topic` upgradeado a redirect accionable con 3 anclas concretas.
- F9 weekly_quality_eval verificado live: 1 row alpaca-2 `_no_workflow` (sample=50, judge_avg=3.94, real gpt-4o-mini, stub_mode=false).
- 20/20 goldens pass real LLM judge (post B17). Judge consistency stddev 0.047 global / 0.312 per-conv max.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}" | head -10
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python -c "import deepagents; print('deepagents', deepagents.__version__ if hasattr(deepagents, '__version__') else 'unknown')"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP9 — confirmar router per-role boot OK + Kimi K2.6 régimen sigue activo:
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('/home/chris/AISALESHT/.env')
from src.core.config import Settings; import src.core.config as cfg; cfg.settings = Settings()
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory
LLMFactory._instance = None
r = LLMFactory.get_service()
for role in ModelRole:
    print(f'{role.name:10s} -> {r.get_provider_for_role(role).value:10s} ({cfg.settings.get_model(role)})')
client = r.get_client(role=ModelRole.AGENT)
print(f'AGENT temp = {client.temperature}')
print(f'AGENT extra_body = {client.model_kwargs.get(\"extra_body\", {})}')
"

# Output esperado (idem TP5+TP6+TP7+TP8):
# NANO       -> openai     (gpt-4o-mini)
# REASONING  -> deepseek   (deepseek-reasoner)
# FAST       -> openai     (gpt-4o-mini)
# VISION     -> openai     (gpt-4o)
# AGENT      -> kimi       (kimi-k2.6)
# EMBEDDING  -> openai     (text-embedding-3-large)
# AGENT temp = 0.6
# AGENT extra_body = {'thinking': {'type': 'disabled'}}

# CRÍTICO TP9 — Qdrant collection nicolify_marketing_kb sigue poblada (TP7 dejó 304 pts) + stats() funciona post B14:
QDRANT_URL=http://localhost:6333 .venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('/home/chris/AISALESHT/.env')
import os; os.environ['QDRANT_URL']='http://localhost:6333'
from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import MarketingKbStore
print(MarketingKbStore().stats())
"
# Esperado: {'collection': 'nicolify_marketing_kb', 'points_count': 304, 'status': 'green'}

# CRÍTICO TP9 — span tree wiring vivo post B15. Sample existing recent turn:
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "
SELECT event_type, COUNT(*) total, COUNT(parent_span_id) with_parent
FROM copilot_trace_event
WHERE event_type IN ('node_enter','node_exit') AND created_at >= NOW() - INTERVAL '1 hour'
GROUP BY event_type;"
# Esperado: total = with_parent (todos node events tienen parent_span_id post-fix). Si total > with_parent → B15 regression.

# Container env reflect Sprint 0 (CRÍTICO post-restart):
docker exec visionarias_brain_dev env | grep -E "AI_PROVIDER_AGENT|AI_MODEL_AGENT|KIMI_API_KEY"
# Si AI_PROVIDER_AGENT no aparece → docker compose up -d --force-recreate api_dev
```

Si router boot falla, deepagents version mismatch, Qdrant collection vacía, o parent_span_id NULL en node events recientes → resolver primero, NO arrancar TP9.

## Patrón llamada API + SQL probes

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: c67c9845-6cf7-4aee-beba-7e177e84d167" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: text/event-stream" \
  -d '{"message":"<test>","conversation_id":null,"client_context":{"current_route":"/copilot"}}'
```

DB:
- `copilot_trace_event` — `event_type='card_emitted'` con `card_kind='plan_card'`, `event_type='tool_call' name='write_todos'`, `event_type='tool_call' name='task'` (subagent dispatch).
- `copilot_conversations.messages` — assistant outputs + tool_calls JSONB.

SQL probes en `01-tooling.md §Infraestructura interna` + `phases/TP9-deep-agent-planning.md §Tools / queries`.

## Anomalías heredadas (de TP1+TP2+TP3+TP4+TP5+TP6+TP7+TP8 + Sprint 0)

### A1 (heredado TP3, neutralizado TP4-TP8) — OpenAI quota
0 errores TP8. Continúa neutralizado.

### A2 (heredado TP3+TP4) — Voseo en strings user-facing copilot module
**RESUELTO TP6** vía B7-TP6. Cierra A2.

### A3 (heredado TP2 design) — Lighthouse route-gated
TP9 corre en `/copilot` ruta. Brand summary alpaca-2 visible.

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k
NANO/FAST/EMBEDDING OpenAI siguen vulnerables. Spacing recomendado entre escenarios.

### A5 (heredado TP1 B3) — `cost_usd` log no aplica cache discount + Kimi/DeepSeek pricing missing
Sigue pendiente. AGENT Kimi en S9.x reportará $0.

### A6 (heredado Sprint 1) — Qwen DashScope 401
NO bloquea TP9.

### TP4-B5 (heredado TP4, REFORZADO TP8) — Provider routing observability gaps + `llm_call` event no emitido
TP8 destapó que `trace_recorder.py` documenta `llm_call` event_type pero NUNCA se emite por chat orchestrator. Solo routing_decision + node_enter/exit + tool_call + card_emitted aparece. Sin `llm_call`, debug "qué LLM corrió este turn" requiere inferir desde routing_decision + node names. **TP9 hint:** medir si la falta del `llm_call` impide debugger planning multi-step (el plan card emite en model node — saber qué LLM corrió ahí ayuda al debug).

### TP4-B6 (heredado TP4, deferred) — intent_classifier miscalsifica cross-tabla
NO afectó TP8.

### TP5-B9 (heredado TP5, deferred) — F6 cutover gap
NO afecta TP9 deep-agent (F2 base es independent).

### TP5-B10 (heredado TP5, deferred) — `awareness.py` other `_check_*` funcs same narrow except
NO afectó TP8.

### TP6-B11 (heredado TP6, REFRAMED TP7) — Kimi K2.6 thinking-disabled compliance ~50% para "use tool result verbatim"
TP9 hint: `write_todos` resultado debería ser usado verbatim (la lista de todos). Si AGENT reformula el plan, el plan_card del UI puede divergir del state interno. Validar S9.2 que plan_card.payload.todos == write_todos invocation arg literal.

### B12-TP7 (heredado TP7, deferred infra) — Qdrant server v1.7.3 vs client v1.17.1
TP8 confirmó scope expansion: bump cliente también dropeó `vectors_count`. NO bloquea TP9 (deep-agent no toca Qdrant directamente — solo via knowledge_search tool si user query lo dispara).

### B14-TP8 (NUEVO TP8, RESUELTO) — qdrant stats schema
Fix arquitectónico aplicado. Cierra issue.

### B15-TP8 (NUEVO TP8, RESUELTO) — node_trace span tree
Fix arquitectónico aplicado. Cierra issue. **TP9 verificación:** span tree depende de este fix. Ver pre-reqs infra check.

### B16-TP8 (NUEVO TP8, deferred — F9 docstring scaling underestima)
Cost guard 7x underestimado. F9 weekly cron a 30 tenants gasta ~$0.79/mo (sobre hard fail $0.50/mo). NO bloquea TP9.

### B17-TP8 (NUEVO TP8, RESUELTO) — accuracy rubric scope-refusal
Fix arquitectónico aplicado. Cierra issue.

## Aprendizajes accionables de TP8

- **Las promesas del docstring no son contratos — verificar que el caller cumpla.** B15-TP8 destapó que `trace_recorder.py:7-8` prometía span tree reconstruction y el recorder tenía la API correcta, pero el único caller del recorder (`emit_node_trace_event`) no propagaba run_id/parent_ids. Para TP9 deep-agent planning, validar que cada tool call + subagent invocation efectivamente populée span_id + parent_span_id (sino el plan_card progress + subagent isolation no son auditables tree-shaped). Probar: trigger S9.6 audit_inspector + verificar que el subagent task tool emite tree con parent = main agent run.
- **Schema drift de deps externas pasa silencioso bajo `:memory:` mocks.** B14-TP8 (qdrant 1.17 dropped vectors_count) + B12-TP7 (qdrant 1.17 changed query_points endpoint) ambos pasaron CI todo el redesign porque tests usan in-memory client. TP9 debe validar que `langchain-deepagents` v latest no rompió `write_todos` + `task` tool surface vs version pinneada. `pip show deepagents` + smoke test antes scenario crítico.
- **Judge rubrics ambiguous = false negatives en goldens nuevos.** B17-TP8 destapó que accuracy rubric pre-fix era ambiguo cuando user pregunta off-scope. Para TP9, los goldens "audit completo" pueden tener mismo problema con utility rubric (¿el plan completa el audit o solo lista items?). Validar antes de S9.2 que `utility` rubric reconoce "produce executable plan" como score 5, no solo "ejecuta el plan completo".

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) — todos outputs user-facing tocados deben verificarse.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + recreate.
7. Stage por nombre en commits (parallel-safety).
8. Tools que ejecuten SQL/external calls dentro de un tool deben usar broad `except Exception` + `logger.exception` (pattern B7-TP5 establecido).
9. **Verification deterministic > tool_call count** (pattern B8-TP6 + B12+B13-TP7 + B14+B15+B17-TP8 establecido). Si target SLO depende de "X result populated", agregar SQL probe que confirme nullable=False columns no NULL.
10. **Schema drift external deps = test against real client surface, no mocks.** Lección B14-TP8 + B12-TP7. `:memory:` Qdrant ≠ live Qdrant. `pip show <dep>` + smoke before scenarios.

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP9-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP10** (1-3 bullets accionables o omitir si no hay) + sección **§Cost split per-provider**.
2. `docs/domains/copilot/testing-2026-04/prompts/TP10-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP10 (provider pattern F1), research mandate de `phases/TP10-provider-pattern.md`, anomalías heredadas (incluir TP4-B5 obs gap si sigue sin fix + B12 + B16 si siguen + cualquier nueva).
3. Si `phases/TP9-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP10-start.md` + plan_card render veredicto + write_todos triggering correctness.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o router boot check.
- Mockear LLM cuando TP exige real-LLM (TP9 deep-agent loop debe ser real Kimi K2.6 para validar plan + subagent dispatch genuinos).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes Claude Code para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP10 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP10).
- Embeber el prompt TP10 dentro del reporte `results/TP9-*.md` — vive en `prompts/TP10-start.md`, el reporte sólo referencia el path.
- **Lección TP6+TP7+TP8**: contar tool_call rows como prueba de "X funcionando". Validar deterministic verification (write_todos count + plan_card payload populated + span tree parent_span_id != NULL).
- **Lección TP8**: asumir que F# está integrado solo porque archivos existen — verificar workflow runs end-to-end + dashboard renders + parent_span_id chains live.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn (~40s TTL).
- write_todos no dispara cuando debería → check `_DEEP_AGENT_SUFFIX_ES` reglas en `deep_agent.py` + Kimi K2.6 compliance (B11-TP6).
- plan_card no renderea → check `_maybe_emit_plan_card` en chat.py + `card_emitted` event en trace.
- Subagent task no dispara → confirmar `subagents=[AUDIT_INSPECTOR_SUBAGENT, URL_ANALYZER_SUBAGENT, DATA_QUERY_SUBAGENT]` en `create_deep_agent` call.
- parent_span_id NULL en node events recientes → B15-TP8 regression. Verificar `node_trace.py::emit_node_trace_event` propaga run_id/parent_ids.
- `pip show deepagents` version mismatch → fix infra ANTES scenarios.
- Container env stale (post `.env` edit) → `docker compose up -d --force-recreate api_dev`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check + Qdrant stats post-B14 check + parent_span_id chain check + deepagents version check + sanity-check F2 source code wiring. Recién después tocás tools.
