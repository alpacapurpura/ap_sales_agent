```
Iniciar TP8 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP8

Validar F9 (`CopilotJudge` multi-dim + 20 conversational goldens + `copilot_workflow_metric` + ARQ `weekly_copilot_quality_eval` + `node_enter`/`node_exit` traces + admin `/copilot-quality` dashboard) + F11.5 lado dashboard (RAG retrieval section). Confirmar:

1. Manual run `weekly_copilot_quality_eval` produce rows en `copilot_workflow_metric` (no `_rag_eval`, normal workflows).
2. CopilotJudge multi-dim devuelve scores coherentes (no todos 0 ni todos 5).
3. `node_enter`/`node_exit` emiten en cada turn → timeline reconstruible.
4. Admin `/copilot-quality` muestra KPIs + sección RAG retrieval (F11.5 hooked al workflow_metric `_rag_eval` row TP7 dejó).
5. Re-run del judge sobre mismas conversaciones produce scores estables (judge consistency).
6. **Provider routing per-role correcto bajo F9 (heredado TP4-TP7 gate Sprint 0)** — judge en NANO + AGENT en Kimi.
7. **B13-TP7 fix verificación cross-dim:** que judge funcione con cualquier combinación de dims (canonical, RAG, mixto) — no sólo RAG goldens.

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP8-quality-eval-observability.md`
8. `docs/domains/copilot/testing-2026-04/results/TP7-2026-04-26.md` (B12+B13 fixes commiteados, RAG eval row populated, lessons learned)
9. `docs/domains/copilot/redesign-2026-04/learnings/F9-quality-observability.md`
10. `docs/domains/copilot/redesign-2026-04/learnings/F11-router-wire-and-rag-eval.md` (si existe)
11. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`
12. **TP7 commits (`git log --oneline -8`):** B12-TP7 Qdrant REST fallback / B13-TP7 judge dynamic prompt builder + rubric registry / TP7 results doc + TP8 start prompt.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP8-quality-eval-observability.md §Research mandate`:
- `llm judge consistency reliability cronbach alpha 2026`
- `agent observability node trace langgraph 2026 patterns`
- `continuous evaluation production llm regression 2026`

Tessl tiles: skill `tessl-context` para tile sobre LLM eval / observability / langgraph si existe.

Si descubrís escenario crítico no listado en TP8 doc, agregalo a `phases/TP8-*.md` ANTES ejecutar (lección TP6+TP7 reforzada).

**Sanity check API real (lección TP3-TP7 reforzada — NO SKIPEAR):** ANTES de ejecutar S8.x, leer la signature real de:
- `backend/src/shared/workers/copilot_quality_eval.py::run_weekly_quality_eval`
- `backend/src/modules/copilot/application/observability/judge.py::CopilotJudge` (post B13-TP7 — `build_system_prompt(dimensions)` + `_DIMENSION_RUBRICS` registry)
- `backend/src/modules/copilot/application/observability/conversational_goldens.py` (si existe — F9 introdujo 20 goldens)
- `backend/src/modules/copilot/application/observability/trace_recorder.py::record_node_enter / record_node_exit`
- `backend/src/admin/modules/copilot_quality.py` (admin dashboard)

confirmar:
1. F9 efectivamente shipea workflow_metric upsert con rows reales (no solo declarations).
2. `node_enter`/`node_exit` están wired en orchestrator graph (post-TP5 F6 cutover gap NO afectó esto).
3. Hay `weekly_copilot_quality_eval` ARQ task registered en `workers/settings.py`.
4. Admin page `copilot-quality.py` existe + pulls workflow_metric rows.

Si encontrás divergencias vs phase doc TP8, ajustar phase doc PRIMERO antes de correr.

**Sanity check verification deterministic (lección TP6-TP7 reforzada):** TP6 destapó tool_call ≠ tool result usado. TP7 destapó test stub != arquitectura real. Para TP8 quality eval:
- Contar workflow_metric rows NO basta — verificar que `extra_metadata` tiene per-dim scores populated (no nulls como B13-TP7 destapó).
- Verificar que goldens tienen suficiente diversidad (canonical 4 dims COVERED al menos 1 vez por golden) sino judge consistency mide ruido.
- Si judge_avg es flat 4.5 cross-runs, sospechar que stubs siguen activos o judge model está retornando fixed scores.

## Setup heredado (NO rehacer — verificado en TP1+TP2+TP3+TP4+TP5+TP6+TP7 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn — TP6+TP7 confirmó refresh ~40s necesario)
- `.env`: `CLERK_TEST_SESSION_ID` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` + Sprint 0 vars (DEEPSEEK_API_KEY + KIMI_API_KEY + DASHSCOPE_API_KEY + AI_PROVIDER_<ROLE>)
- Tenants test:
  - **alpaca-2** `c67c9845-6cf7-4aee-beba-7e177e84d167` — brand_summary v2 (580 chars). **Tenant primario TP6+TP7** (Visionarias `6347e21e-…` SIN brand_summary).
- TP1+TP2+TP3+TP4+TP5+TP6+TP7 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) façade.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key`.
- TP4+TP5+TP6+TP7 confirma routing live: REASONING DeepSeek, AGENT Kimi K2.6 (no-thinking + temp 0.6), NANO/FAST OpenAI gpt-4o-mini.

### NUEVO TP6 fixes
- B7-TP6 voseo cross-channel arch fix (3 capas defensa: static.j2 + synthesizer.py fallbacks + output_sanitizer.correct_voseo_in_text 50+ formas).
- B8-TP6 SMS overflow arch fix (output_sanitizer detect_channel_in_user_msg + enforce_channel_format_if_needed).
- copilot_system_tools_hint.j2 — channel formatter section.

### NUEVO TP7 fixes
- **B12-TP7 Qdrant REST fallback** — `marketing_kb_store.search` try `client.query_points` → on UnexpectedResponse 404, fallback `_search_via_rest` (httpx POST `/collections/{name}/points/search`). Helpers `_hit_to_dict` + `_rest_point_to_dict` module-level. Comentario inline `B12-TP7` para F-pos cleanup. **Razón:** dev Qdrant pinned `qdrant/qdrant:v1.7.3` while qdrant-client>=1.13.3 emite endpoint v1.10+. Cross-module impact (sales_agent + brand stores también usan query_points) deferred.
- **B13-TP7 judge dynamic prompt builder** — `_DIMENSION_RUBRICS: dict[str, str]` registry con 8 entries (4 canonical + 4 RAG). `build_system_prompt(dimensions: Sequence[str]) -> str` rendera prompt dinámico, alfabetiza dims, valida unknown raise ValueError. `evaluate()` llama builder en vez de constante estática. `_SYSTEM_PROMPT_ES` removido. **Razón:** F11.5 weekly_rag_eval pasaba `dimensions=RAG_DIMENSIONS` pero prompt estático seguía pidiendo canonical → judge devolvía canonical → parser RAG missed all dims → todas NULL. 4 nuevos tests cubren regresión.
- **KB seedeado:** `nicolify_marketing_kb` collection 304 chunks / 31 docs. Seedear de nuevo solo si TP8 dropea collection.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}" | head -10
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP8 — confirmar router per-role boot OK + Kimi K2.6 régimen B8 sigue activo:
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

# Output esperado (idem TP5+TP6+TP7):
# NANO       -> openai     (gpt-4o-mini)
# REASONING  -> deepseek   (deepseek-reasoner)
# FAST       -> openai     (gpt-4o-mini)
# VISION     -> openai     (gpt-4o)
# AGENT      -> kimi       (kimi-k2.6)
# EMBEDDING  -> openai     (text-embedding-3-large)
# AGENT temp = 0.6
# AGENT extra_body = {'thinking': {'type': 'disabled'}}

# CRÍTICO TP8 — Qdrant collection nicolify_marketing_kb sigue poblada (TP7 dejó 304 pts):
QDRANT_URL=http://localhost:6333 .venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('/home/chris/AISALESHT/.env')
import os; os.environ['QDRANT_URL']='http://localhost:6333'
from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import MarketingKbStore
print(MarketingKbStore().stats())
"
# Esperado: points_count=304 status=green. Si vacío → re-seedear con scripts/seed_nicolify_marketing_kb.py.

# CRÍTICO TP8 — workflow_metric tiene row _rag_eval del TP7:
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "SELECT period_start::date, judge_avg_score, judge_sample_size FROM copilot_workflow_metric WHERE workflow_id='_rag_eval' ORDER BY created_at DESC LIMIT 2;"
# Esperado: 2 rows. La latest tiene judge_avg_score=4.84 (post-B13 fix). Si nula → B13 regression.

# Container env reflect Sprint 0 (CRÍTICO post-restart):
docker exec visionarias_brain_dev env | grep -E "AI_PROVIDER_AGENT|AI_MODEL_AGENT|KIMI_API_KEY"
# Si AI_PROVIDER_AGENT no aparece → docker compose up -d --force-recreate api_dev
```

Si router boot falla o Qdrant collection vacía → resolver primero, NO arrancar TP8.

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
- `copilot_workflow_metric` — workflow_id + tenant_id + judge_avg_score + extra_metadata (jsonb dim scores).
- `copilot_trace_event` — `event_type='node_enter'/'node_exit'` para timeline.
- `copilot_conversations.messages` — assistant outputs para feed al judge.

SQL probes en `01-tooling.md §Infraestructura interna` + `phases/TP8-quality-eval-observability.md §Tools / queries`.

## Anomalías heredadas (de TP1+TP2+TP3+TP4+TP5+TP6+TP7 + Sprint 0)

### A1 (heredado TP3, neutralizado TP4-TP7) — OpenAI quota
0 errores TP6+TP7. Continúa neutralizado.

### A2 (heredado TP3+TP4) — Voseo en strings user-facing copilot module
**RESUELTO TP6** vía B7-TP6. Cierra A2.

### A3 (heredado TP2 design) — Lighthouse route-gated
TP7 confirmó lighthouse activo en `/copilot` ruta (S7.8 referencia "tu Brand Studio").

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k
NANO/FAST/EMBEDDING OpenAI siguen vulnerables. Spacing recomendado.

### A5 (heredado TP1 B3) — `cost_usd` log no aplica cache discount + Kimi/DeepSeek pricing missing
Sigue pendiente. AGENT Kimi reportará $0.

### A6 (heredado Sprint 1) — Qwen DashScope 401
NO bloquea TP8.

### TP4-B5 (heredado TP4, deferred) — Provider routing observability gaps
TP6+TP7 confirmaron routing via `tool_call` rows directos. Sigue deferred.

### TP4-B6 (heredado TP4, deferred) — intent_classifier miscalsifica cross-tabla
NO afectó TP6+TP7.

### TP5-B9 (heredado TP5, deferred) — F6 cutover gap
NO afecta TP8 quality (F9 + F11.5 son output-stage independientes).

### TP5-B10 (heredado TP5, deferred) — `awareness.py` other `_check_*` funcs same narrow except
NO afectó TP6+TP7. Trivial sweep posible.

### TP6-B11 (heredado TP6, REFRAMED TP7) — Kimi K2.6 thinking-disabled compliance ~50% para "use tool result verbatim"

**Update TP7:** S7.8 e2e contradice parcialmente. Compliance es ALTA cuando tool pide synthesis ("cita el método"); BAJA cuando pide copia exacta ("usa exactamente el campo content"). Channel format (B8-TP6) ya mitigado por sanitizer. RAG (TP7) no requirió safety net.

**TP8 hint:** medir si judge consistency está afectada por compliance variance — si AGENT reformula tool output, judge_avg podría ser ruidoso turn-to-turn. Considerar baseline (mismo input, 5 runs) en S8.5.

### B12-TP7 (NUEVO TP7, deferred infra) — Qdrant server v1.7.3 vs client v1.17.1

**Síntoma:** dev Qdrant container pinned a `qdrant/qdrant:v1.7.3` (docker-compose.yml line 345) pero qdrant-client `>=1.13.3` instala 1.17.1 que emite `query_points` v1.10+ → 404. Mitigado en `marketing_kb_store.search` via httpx REST fallback.

**Riesgo TP8:** Si TP8 toca otros Qdrant stores (`sales_agent/vector_store.py`, `brand/style_anchor_store.py`), van a fallar igual. Si TP8 introduce nuevo Qdrant store, debe seguir pattern del fallback o esperar bump infra.

**Plan F-pos:** docker-compose `qdrant/qdrant:v1.16.x` (sequential 1.7→1.8→...→1.16 OR drop+recreate dev collections). Cross-module sales_agent + brand stores también requieren validación post-bump.

### B13-TP7 (NUEVO TP7, RESUELTO) — CopilotJudge prompt hardcoded canonical dims

Fix arquitectónico aplicado. Cierra issue. **TP8 verificación:** correr judge con dim combinations (canonical only / RAG only / mixto canonical+RAG) y confirmar scores != 0 + alphabetical order en prompt.

## Aprendizajes accionables de TP7

- **Tool result usage tipo-dependiente (Kimi K2.6 thinking-disabled):** S7.8 destapó que el AGENT cumple bien cuando el tool pide synthesis ("cita el método aplicado") y mal cuando pide copia exacta ("usa exactamente el campo content"). Para TP8 quality eval, validar que las weekly samples efectivamente incluyen turns donde AGENT consumió tool results — sino no estamos midiendo redacción real, solo el draft inicial.
- **Test stub coverage no garantiza arquitectura correcta:** B12 (Qdrant API) + B13 (judge dim mismatch) ambos pasaron CI todo el redesign porque tests usan `QdrantClient(":memory:")` + `CopilotJudge` mock. F10 + F11.5 cerraron quality gates internos sin nunca exercise live infra. TP8 debe agregar arch test o weekly cron que VERIFIQUE infra real (Qdrant version + judge dim coverage) sino seguimos shipping arquitectura "funcionando" que falla en prod.
- **F11.5 quality cron es el primer escalón de monitoreo continuo:** El row `copilot_workflow_metric._rag_eval` ahora está populated end-to-end (judge_avg + per-dim scores + recall + latency). TP8 puede usar este row + analogous F9 quality_eval row para construir dashboard `/copilot-quality` con trends weekly. Sin TP7 fix B13, ese dashboard mostraría NULL.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) — todos outputs user-facing tocados deben verificarse.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + recreate.
7. Stage por nombre en commits (parallel-safety).
8. Tools que ejecuten SQL/external calls dentro de un tool deben usar broad `except Exception` + `logger.exception` (pattern B7-TP5 establecido).
9. **Verification deterministic > tool_call count** (pattern B8-TP6 + B12+B13-TP7 establecido). Si target SLO depende de "X result populated", agregar SQL probe que confirme nullable=False columns no NULL.

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP8-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP9** (1-3 bullets accionables o omitir si no hay) + sección **§Cost split per-provider**.
2. `docs/domains/copilot/testing-2026-04/prompts/TP9-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP9 (deep_agent planning F2), research mandate de `phases/TP9-deep-agent-planning.md`, anomalías heredadas (incluir TP4-B5 obs gap si sigue sin fix + B12 si sigue + cualquier nueva).
3. Si `phases/TP8-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP9-start.md` + judge_avg quality vs target.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o router boot check.
- Mockear LLM cuando TP exige real-LLM (judge consistency necesita real NANO calls).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP9 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP9).
- Embeber el prompt TP9 dentro del reporte `results/TP8-*.md` — vive en `prompts/TP9-start.md`, el reporte sólo referencia el path.
- **Lección TP6+TP7**: contar workflow_metric rows como prueba de "judge funcionando". Validar que `extra_metadata.judge_dimensions` tiene per-dim scores != null + judge_avg_score populated.
- **Lección TP7**: asumir que F9/F11.5 está integrado solo porque archivos existen — verificar workflow runs end-to-end + dashboard renders rows reales (lección TP3-TP7).

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn (~40s TTL).
- Judge devuelve null scores → `build_system_prompt(self.dimensions)` invocation broken; recheck B13-TP7 fix vivo en `judge.py::evaluate`.
- Qdrant collection vacía → `python scripts/seed_nicolify_marketing_kb.py`.
- workflow_metric row no aparece → repo `WorkflowMetricRepository.upsert` puede tener tenant constraint. Verificar UUID(int=0) sentinel for `_rag_eval` (nullable=False).
- Container env stale (post `.env` edit) → `docker compose up -d --force-recreate api_dev`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check + Qdrant collection check + workflow_metric row check + sanity-check F9 source code wiring. Recién después tocás tools.
```
