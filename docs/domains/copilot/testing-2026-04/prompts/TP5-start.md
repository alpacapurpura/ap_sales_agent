# TP5 Start Prompt

Copy-paste el fenced block debajo en una conversación nueva de Claude Code.

```
Iniciar TP5 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP5

Validar F6 (`Workflow` declarative + `WorkflowEngine` + dual-read fallback `procedure_state ↔ workflow_state`). Confirmar:
1. Pilots `setup_brand_minimal` + `design_offer_from_url` corren end-to-end sin crash.
2. State persiste en `workflow_state` JSONB (con dual-read fallback `procedure_state` legacy).
3. Coexistencia 4 sistemas (guided + procedure + extraction_card_flow + Workflow nuevo) no se pisan.
4. Reanudar conv interrumpida levanta del nodo correcto.
5. UX consistency entre 2 pilots (timing/wording/render).
6. Workflow handler error → graceful trace+message, NO crash silencioso.
7. **Provider routing per-role correcto bajo F6 (heredado TP4 gate Sprint 0).**

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP5-workflows-runtime.md`
8. `docs/domains/copilot/testing-2026-04/results/TP4-2026-04-26.md` (aprendizajes + B5/B6 deferred + 4 fixes commiteados)
9. `docs/domains/copilot/redesign-2026-04/learnings/F6-workflow-runtime.md` (F6 source)
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`
11. **TP4 commits (`git log --oneline -10`):** B1 date_parser regex / B3 tool_call duration_ms / B4 Kimi K2.6 temp clamp / stub fix integration test / phase doc + report.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP5-workflows-runtime.md §Research mandate`:
- `langgraph multi-step workflow state persistence resume 2026`
- `agent workflow declarative vs imperative tradeoffs 2026`
- `workflow engine python lazy handler resolution 2026`

Tessl tiles: skill `tessl-context` para tile sobre LangGraph workflow checkpointing si existe.

Si descubrís escenario crítico no listado en TP5 doc, agregalo a `phases/TP5-workflows-runtime.md` ANTES ejecutar.

**Sanity check API real (lección TP3+TP4 reforzada):** ANTES de ejecutar S5.x, leer la signature real del WorkflowEngine + handler resolver en `backend/src/modules/copilot/application/workflow/` y comparar con lo que cada escenario asume. Si difieren, ajustar el phase doc PRIMERO antes de correr. TP4 detectó 3 divergencias (NANO no FAST + tenant sin data + S4.5 unsupported) — TP5 puede tener parecidas (handler signature, workflow_state schema, fallback `procedure_state` semantics).

## Setup heredado (NO rehacer — verificado en TP1+TP2+TP3+TP4 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn)
- `.env`: `CLERK_TEST_SESSION_ID=sess_3CoDlDaZ9wye8g5OISeyvwsYiRp` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` (recargado) + Sprint 0 vars (DEEPSEEK_API_KEY + KIMI_API_KEY + DASHSCOPE_API_KEY + AI_PROVIDER_<ROLE>)
- Tenants test:
  - **Visionarias** `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` — 12 products + 15 leads recientes (post seed TP4) + 4 enrollments. Brand_summary: 0 rows. **Tenant primario TP5 si workflows necesitan offer/lead data.**
  - **alpaca-2** `c67c9845-6cf7-4aee-beba-7e177e84d167` — brand_summary v2 (580 chars), 0 productos, 0 leads. **Tenant para "tenant fresco" en S5.1 setup_brand_minimal.**
  - **visionarias-v4** `9ba0b29a-8507-424f-a48a-896f93218a25` — heredado TP1+TP2 sin productos.
- TP3 fixes commiteados (B1+B2+B3+B4): internal LLM stream tag + card_kind extension + ToolMessage parse + zombie filter.
- TP1+TP2 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 nuevos providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) façade resuelve provider per-role.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key`.
- **Sprint 1 smoke confirmado live + TP4 valida runtime:**
  - REASONING DeepSeek deepseek-reasoner OK (no invocado en F5).
  - AGENT Kimi K2.6 OK runtime (post B4 clamp). Verificado via 400-error vanish + container env diff.
  - NANO/FAST OpenAI gpt-4o-mini OK (intent + synth ask_tenant_data).
  - Qwen 401 (cuenta sin verificar — A6 anomaly heredada, NO bloquea TP5).

### NUEVO TP4 fixes (commits incluidos en este push)
- **B1 date_parser regex** — `date_parser.py:140` regex tolera prefijo Spanish "los/las/el/la" para "últimos N días". Test parametrizado 4 cases.
- **B3 tool_call duration_ms** — `_StreamAccumulator.tool_started_at` + on_tool_start time stamp + on_tool_end elapsed → recorder. Pattern reusable cualquier evento con duration en TP5.
- **B4 Kimi K2.6 temp clamp** — `KimiService._get_chat_model` coerce temperature=1.0 cuando model contiene "k2". Crítico: si TP5 workflows construyen su propio LLM client (NO via `LLMFactory`), evaden el clamp y reproducen el 400.
- Stub `_ScriptedLLM.invoke` acepta `**_kwargs` (config TP3 B1 ahora compatible).
- `test_deep_agent_factory_wire` actualizado: temperature override tests usan `ModelRole.REASONING` (DeepSeek) para evitar clamp; nuevo `test_kimi_k2_temperature_clamped_for_agent_role` documenta invariante.
- TP4 phase doc actualizado (tenant Visionarias + intent NANO + S4.2 fuzzy real catálogo + S4.5 unsupported reframe).

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}" | head -10  # daemon healthy + brain_dev/postgres/redis up
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP5 — confirmar router per-role boot OK con keys reales:
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('/home/chris/AISALESHT/.env')
from src.core.config import Settings; import src.core.config as cfg; cfg.settings = Settings()
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory
LLMFactory._instance = None
r = LLMFactory.get_service()
for role in ModelRole:
    print(f'{role.name:10s} -> {r.get_provider_for_role(role).value:10s} ({cfg.settings.get_model(role)})')
"

# Output esperado (idem TP4):
# NANO       -> openai     (gpt-4o-mini)
# REASONING  -> deepseek   (deepseek-reasoner)
# FAST       -> openai     (gpt-4o-mini)
# VISION     -> openai     (gpt-4o)
# AGENT      -> kimi       (kimi-k2.6)
# EMBEDDING  -> openai     (text-embedding-3-large)

# Container env reflect Sprint 0 (CRÍTICO post-restart):
docker exec visionarias_brain_dev env | grep -E "AI_PROVIDER_AGENT|AI_MODEL_AGENT|KIMI_API_KEY"
# Si AI_PROVIDER_AGENT no aparece → docker compose up -d --force-recreate api_dev (recreate, no solo restart)

# Visionarias tenant data still poblada (TP4 seed):
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "SELECT COUNT(*) FROM products WHERE tenant_id='6347e21e-8112-4aa1-80d3-6adaa73bf6f9' AND deleted_at IS NULL; SELECT COUNT(*) FROM leads WHERE tenant_id='6347e21e-8112-4aa1-80d3-6adaa73bf6f9' AND last_interaction_date >= NOW() - INTERVAL '7 days';"
```

Si router boot falla → resolver Sprint 0 setup primero, NO arrancar TP5. Si Kimi 400 vuelve → confirmar B4 clamp aplicado (`grep "_get_chat_model" backend/src/shared/infrastructure/llm/providers/kimi.py`). Si Visionarias 0 leads → re-correr seed `.venv/bin/python /tmp/seed_tp4.py` (o equivalente nuevo en TP5 si el script fue limpiado).

## Patrón llamada API + SQL probes

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 6347e21e-8112-4aa1-80d3-6adaa73bf6f9" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"<test>","conversation_id":null,"client_context":{"current_route":"/brand-studio"}}'
```

**Importante TP5:** F6 workflows pueden ser route-gated (e.g., setup_brand_minimal en `/brand-studio`, design_offer_from_url en `/offer-studio`). Verificar en F6 source qué route activa cada workflow.

DB:
- `copilot_conversations.workflow_state` (jsonb) — F6 SSoT
- `copilot_conversations.procedure_state` (jsonb) — legacy fallback
- `copilot_trace_event` con `event_type='node_enter'/'node_exit'` para timeline F6

SQL probes en `01-tooling.md §Infraestructura interna` + `phases/TP5-workflows-runtime.md §Tools / queries`.

**Per-role tracing (post-TP4-B5 deferred, validar igual):**
```sql
-- Nota: turn_end.data->>'model' refleja LAST chat_model_end del turn (B5 obs gap).
-- Para TP5 confirmar AGENT=Kimi: si workflow NO falla con 400 + Kimi corre, AGENT routing OK.
SELECT data->>'model' AS last_model, COUNT(*)
FROM copilot_trace_event
WHERE event_type='turn_end' AND created_at >= NOW() - INTERVAL '15 minutes'
GROUP BY data->>'model';
```

## Anomalías heredadas (de TP1+TP2+TP3+TP4 + Sprint 0)

### A1 (heredado TP3, neutralizado TP4) — OpenAI quota
TP4 corrió 0 errores quota. Sprint 0 dejó NANO+FAST+VISION+EMBED en OpenAI; REASONING+AGENT en chinos. Continuar monitoreo en TP5 (workflows pueden invocar más calls que TP4).

### A2 (heredado TP3 + TP4) — Voseo en strings user-facing copilot module
TP4 detectó nuevas instancias en `synthesizer.py:74,81` (`_empty_window_reply` y `_unknown_intent_reply` con "querés/podés"). NO bloqueante TP5 a priori, pero si TP5 toca handler errores user-facing, aplicar regla 11.

### A3 (heredado TP2 design) — Lighthouse route-gated
`/brand-studio` está en `_INJECTION_SEGMENTS`. TP5 desde brand-studio mantiene lighthouse. Para TP5 sí relevante porque setup_brand_minimal lee/escribe brand_identity (consume lighthouse).

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k
NANO/FAST en OpenAI siguen vulnerables. Spacing ≥1s recomendado entre scenarios.

### A5 (heredado TP1 B3) — `cost_usd` log no aplica cache discount + amplificado por providers chinos
Kimi/DeepSeek pricing NO en `usage_tracking.calculate_cost`. Logs reportan $0 para AGENT en Kimi. Reportar cost real estimado manualmente (~$0.001-0.005 / turn full).

### A6 (heredado Sprint 1) — Qwen DashScope intl 401 cuenta sin verificar
NO bloquea TP5. Default OFF.

### A7 (heredado Sprint 1, cubierto TP4-B4) — Kimi K2.6 temperature=1 only
RESUELTO en B4. Verificar pre-flight TP5 que el clamp sigue activo (test arch en place).

### TP4-B5 (deferred) — Provider routing observability gaps

3 gaps en recorder NO fixeados en TP4:
1. `tool_call.data` no incluye `provider`.
2. `turn_end.data->>'model'` se sobrescribe por LAST LLM call (oculta AGENT model real).
3. NO `event_type='llm_call'` events emitidos.

**Acción TP5:** si F6 workflows necesitan validar routing per-step, usar el patrón "force 400 error → check disappearance" hasta que B5 fixee. Plan separado: cubrir en TP8 (quality+observability) o nuevo TP4.5 dedicado.

### TP4-B6 (deferred) — intent_classifier miscalsifica cross-tabla questions
S4.5 mostró `lead_count` con confidence 0.9 para "top 3 ofertas". Empty_window short-circuit lo cubrió downstream pero el classifier mismo está confundido. NO afecta TP5 directly (workflows tienen su propia intent layer).

## Aprendizajes accionables de TP4

- **Kimi K2.6 clamp pattern (B4)**: cualquier callsite que pase `temperature` explícita a `LLMFactory.get_client(role=AGENT, ...)` se beneficia del clamp. F6 workflows que construyan sus propios LLM clients (si lo hacen) deben usar `LLMFactory` y NO instanciar `ChatOpenAI` directo — sino el clamp se evade. Verificar pre-flight en TP5.
- **Date parser tolerance pattern (B1)**: el LLM intent_classifier preserva artículos Spanish verbatim ("los/las/el/la"). Cualquier regex futuro de date_parser o slot extraction debe anticipar prefijos de artículos. Aplicable a TP5 si workflows tienen período capture.
- **Tool latency observability (B3)**: el patrón "store start in acc → compute elapsed in handler" es replicable para cualquier nuevo evento que requiera duration_ms. F6 workflows pueden reusar `acc.tool_started_at` para sub-step timing si emiten su propio `event_type`.
- **Sanity-check ANTES ejecutar (lección TP3 reforzada)**: TP4 phase doc tenía 3 divergencias vs F5 real. TP5 debe leer F6 source code pre-research. Workflow engine signature, handler resolver lazy importlib, fallback semantics.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + recreate (env propagation).
7. Stage por nombre en commits (parallel-safety).
8. **NUEVO TP5**: workflows construyen LLM clients via `LLMFactory.get_service().get_client(role)`. Si encuentran `ChatOpenAI(...)` direct instantiation, refactor + arch test (Kimi clamp evade detector).

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP5-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP6** (1-3 bullets accionables o omitir si no hay) + sección **§Cost split per-provider** mostrando cost real workflows.
2. `docs/domains/copilot/testing-2026-04/prompts/TP6-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP6 (channel formatter, F7), research mandate de `phases/TP6-channel-formatter.md`, anomalías heredadas (incluir B5 obs gap pendiente + B6 intent classifier si siguen sin fix).
3. Si `phases/TP5-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP6-start.md` + cost saved vs baseline.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o router boot check.
- Mockear LLM cuando TP exige real-LLM (workflows multi-step necesitan real-LLM para validar wiring + UX).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP6 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP6).
- Embeber el prompt TP6 dentro del reporte `results/TP5-*.md` — vive en `prompts/TP6-start.md`, el reporte sólo referencia el path.
- **NUEVO TP5**: asumir que routing OK porque TP4 lo validó — F6 puede tener su propio LLM client path. Re-validar via 400-vanish pattern + container env spot-check.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn.
- Kimi 400 only-1-allowed vuelve → grep `kimi_k2_temperature_clamped` en BE logs. Si NO aparece, alguien instanció `ChatOpenAI(...)` directo → refactor a `LLMFactory.get_service().get_client(...)`.
- DeepSeek 429 quota → confirmar billing dashboard https://platform.deepseek.com/usage. Fallback `AI_PROVIDER_REASONING=openai AI_MODEL_REASONING=gpt-4o` en `.env` y restart container.
- Container env stale (post `.env` edit) → `docker compose up -d --force-recreate api_dev` (NO solo restart — env vars no se re-aplican).
- ARQ task no corre tras enqueue → `arq:result:{job_id}` stale + `docker logs visionarias_worker`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check + Visionarias data check. Recién después tocás tools.
```
