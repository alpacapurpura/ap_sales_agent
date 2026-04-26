Iniciar TP10 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP10

Validar F1 (provider pattern + discovery + `MODULE_REGISTRY` descentralizado). Confirmar:

1. Agregar módulo dummy con su `copilot_provider/` se descubre en boot.
2. Tool nuevo aparece en LLM bound tools sin editar `copilot/application/tools/registry.py`.
3. Provider scan NO abre conexiones DB en module-load (heredado F4 gotcha).
4. Arch test `test_no_new_cross_module_imports` no se rompe agregando provider nuevo.
5. Remover módulo dummy → tool desaparece (con/sin restart, documentar).
6. **Schema parity BE↔FE para cualquier card_kind / system prompt section / tool API que el provider exponga** (lección B18-TP9 — schema gaps cross-stack pasan silencioso sin parity test).
7. **Pre-flight schema drift check** — `pip show deepagents` + LLMFactory router boot + Qdrant stats + parent_span_id chains live (lección B12+B14-TP8 + B18-TP9 reforzada).

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP10-provider-pattern.md`
8. `docs/domains/copilot/testing-2026-04/results/TP9-2026-04-26.md` (B18-TP9 fix arquitectónico + recomendaciones + aprendizajes)
9. `docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md`
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md` + `.claude/rules/backend-ddd.md` (cross-module imports + DDD layer order)
11. **TP9 commits (`git log --oneline -8`):** B18-TP9 plan_card schema gap fix dual BE+FE + TP9 results doc + TP10 start prompt.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP10-provider-pattern.md §Research mandate`:
- `python entry_points plugin discovery 2026 best practices`
- `langchain tool registration dynamic 2026`
- `DDD ports adapters provider pattern python 2026`

Tessl tiles: skill `tessl-context` para tile sobre python plugin/entry_points si existe.

Si descubrís escenario crítico no listado en TP10 doc, agregalo a `phases/TP10-*.md` ANTES ejecutar (lección TP6+TP7+TP8+TP9 reforzada).

**Sanity check API real (lección TP3-TP9 reforzada — NO SKIPEAR):** ANTES de ejecutar S10.x, leer la signature real de:
- `backend/src/modules/copilot/application/providers/discovery.py` — `discover_providers()` scan path + caching
- `backend/src/modules/copilot/domain/ports.py` — `CopilotProvider` ABC interface real
- `backend/src/modules/copilot/application/tools/registry.py` — `_build_tool_groups` y route → tools mapping
- `backend/src/modules/copilot/domain/module_registry.py` — `MODULE_REGISTRY` populated dinámica vs estática
- Existing module `copilot_provider/` ejemplos (e.g. `backend/src/modules/brand/copilot_provider/` o `analytics/copilot_provider/` — confirmar shape real vs phase doc TP10 ejemplo dummy)

Confirmar:
1. discovery scan pattern matchea `_test_provider/copilot_provider/manifest.py` (probable case-sensitive convention).
2. CopilotProvider ABC tiene `module_name + tools + workflows + data_access` (per phase doc) o shape diferente.
3. Tool registry _build_tool_groups bind_tools per route — agregar tool nuevo NO debe requerir edit.
4. Span tree post B15-TP8 sigue propagando parent_span_id en TP10 turns.

Si encontrás divergencias vs phase doc TP10, ajustar phase doc PRIMERO antes de correr.

**Sanity check verification deterministic (lección TP6-TP9 reforzada):** TP6 destapó tool_call ≠ tool result usado. TP7 destapó test stub != arquitectura real. TP8 destapó schema drift silent + span tree gap silent. TP9 destapó BE↔FE schema gap silent (B18). Para TP10 provider pattern:
- Contar `discover_providers() returned dummy` NO basta — verificar que el dummy tool efectivamente firea como tool_call con args correctos + output presente en SSE.
- **Schema parity BE↔FE check** — si el dummy provider expone una card_kind / system prompt section / tool API, verificar que FE la mira (BE Literal + registry, FE union + dispatcher). B18-TP9 mostró que schema parcial pasa silencioso si arch test no enforce parity.
- Si discovery encuentra dummy pero tool NO aparece bound, sospechar que `_build_tool_groups` tiene route allowlist que excluye módulos `_test_*`.
- Si `pip show deepagents` muestra version != prod expected, hard fail antes de scenarios — fix infra primero (lección B14-TP8 + TP9 pre-flight).

## Setup heredado (NO rehacer — verificado en TP1+...+TP9 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 + deepagents 0.5.3 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn — TP6+TP7+TP8+TP9 confirmó refresh ~40s necesario)
- `.env`: `CLERK_TEST_SESSION_ID` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` + Sprint 0 vars (DEEPSEEK_API_KEY + KIMI_API_KEY + DASHSCOPE_API_KEY + AI_PROVIDER_<ROLE>)
- Tenants test:
  - **alpaca-2** `c67c9845-6cf7-4aee-beba-7e177e84d167` — brand_summary v2 (580 chars) + 0 ofertas + 6/11 connections + 0 leads. **Tenant primario TP6+TP7+TP8+TP9.**
- TP1+...+TP9 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) façade.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key`.
- TP4-TP9 confirma routing live: REASONING DeepSeek, AGENT Kimi K2.6 (no-thinking + temp 0.6), NANO/FAST OpenAI gpt-4o-mini.

### NUEVO TP6-TP8 fixes
- B7-TP6 voseo cross-channel arch fix (3 capas defensa).
- B8-TP6 SMS overflow arch fix (output_sanitizer enforce_channel_format_if_needed).
- B12-TP7 Qdrant REST fallback en marketing_kb_store.search.
- B13-TP7 judge dynamic prompt builder + `_DIMENSION_RUBRICS` registry.
- B14-TP8 qdrant stats schema fix.
- B15-TP8 node_trace span tree propagación (run_id + parent_ids).
- B17-TP8 accuracy rubric scope-refusal.
- KB seedeado: `nicolify_marketing_kb` 304 chunks / 31 docs.

### NUEVO TP9 fixes
- **B18-TP9 plan_card schema gap BE↔FE** — `domain/message_blocks.py` (CardBlock.card_kind Literal + "plan_card") + `domain/card_payloads.py` (PlanCardPayload model + registry) + FE `types/message-blocks.ts` (CardKind union + PlanCardData/PlanCardTodo) + REWRITE `components/PlanCard.tsx` (deepagents shape sin approval) + `blocks/CardBlock.tsx` (case "plan_card") + 3 vitest tests + 3 BE pytest tests. Fix arquitectónico dual BE+FE TDD RED→GREEN.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}" | head -10
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python -c "import deepagents; print('deepagents', deepagents.__version__ if hasattr(deepagents, '__version__') else 'unknown')"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP10 — confirmar router per-role boot OK + Kimi K2.6 régimen sigue activo:
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

# CRÍTICO TP10 — discover_providers actual + cardinality (baseline S10.1):
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('/home/chris/AISALESHT/.env')
from src.modules.copilot.application.providers.discovery import discover_providers
providers = discover_providers()
for p in providers:
    print(f'{p.module_name}: tools={len(p.tools()) if hasattr(p, \"tools\") else \"?\"}')
"

# CRÍTICO TP10 — span tree wiring sigue vivo post-B15:
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "
SELECT event_type, COUNT(*) total, COUNT(parent_span_id) with_parent
FROM copilot_trace_event
WHERE event_type IN ('node_enter','node_exit') AND created_at >= NOW() - INTERVAL '30 minutes'
GROUP BY event_type;"
# Esperado: total = with_parent. Si hay gap → B15 regression.

# Container env reflect Sprint 0 (CRÍTICO post-restart):
docker exec visionarias_brain_dev env | grep -E "AI_PROVIDER_AGENT|AI_MODEL_AGENT|KIMI_API_KEY"
# Si AI_PROVIDER_AGENT no aparece → docker compose up -d --force-recreate api_dev
```

Si router boot falla, deepagents version mismatch, discover_providers vacío, o parent_span_id NULL en node events recientes → resolver primero, NO arrancar TP10.

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
- `copilot_trace_event` — `event_type='tool_call' name='test_dummy_tool'` post S10.4.
- Postgres connection logs — `docker logs visionarias_postgres --since 1m` durante import S10.5.

SQL probes en `01-tooling.md §Infraestructura interna` + `phases/TP10-provider-pattern.md §Tools / queries`.

## Anomalías heredadas (de TP1+...+TP9 + Sprint 0)

### A1 (heredado TP3, neutralizado TP4-TP9) — OpenAI quota
0 errores TP9. Continúa neutralizado.

### A2 (heredado TP3+TP4, RESUELTO TP6) — Voseo en strings user-facing copilot module
Cierra A2.

### A2.1 (NUEVA TP9, deferred — voseo en LLM system prompts internos)
- **Síntoma:** `subagents/url_analyzer.py` + `subagents/data_query.py` + `deep_agent.py::_DEEP_AGENT_SUFFIX_ES` usan formas voseadas en imperativos (`llamá`, `reportá`, `devolvele`, `Marcá`, `respondé`, `Usá`, `recibís`).
- **Por qué deferred:** son INPUT al LLM, NO output user-facing. Outputs LLM en TP9 fueron neutro correcto. Pero contradicen al editor humano. F-pos cleanup (~30min). NO bloquea TP10.

### A3 (heredado TP2 design) — Lighthouse route-gated
TP10 corre en `/copilot` o equivalente.

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k
NANO/FAST/EMBEDDING OpenAI siguen vulnerables. Spacing recomendado.

### A5 (heredado TP1 B3) — `cost_usd` log no aplica cache discount + Kimi/DeepSeek pricing missing
**Persiste.** TP9 confirmó S9.x Kimi K2.6 turns logean `cost_usd=0.0`. Manual estimate ~$0.014/turn HEAVY. F-pos: agregar Kimi K2.6 + DeepSeek + Qwen pricing en `usage_tracking.calculate_cost`.

### A6 (heredado Sprint 1) — Qwen DashScope 401
NO bloquea TP10.

### TP4-B5 (heredado TP4, REFORZADO TP8+TP9) — `llm_call` event no emitido
**Persiste.** Plan agregar `record(event_type='llm_call', model=..., tokens=..., duration_ms=...)` después de cada `astream_events.on_chat_model_end` en chat orchestrator.

### TP4-B6 (heredado TP4, deferred) — intent_classifier miscalsifica cross-tabla
NO afectó TP9.

### TP5-B9 (heredado TP5, deferred) — F6 cutover gap
NO afecta TP10 (provider pattern es F1 base).

### TP5-B10 (heredado TP5, deferred) — `awareness.py` other `_check_*` funcs same narrow except
NO afectó TP9.

### TP6-B11 (heredado TP6, REFRAMED TP7+TP9) — Kimi K2.6 thinking-disabled compliance ~50% phrasing-sensitive
**Manifestación TP9:** S9.9-2 "diseñá landing completa" (5 items implícito) → 0 write_todos. S9.9-3 "audit paso por paso, usá write_todos" (explícito) → fired. F-pos: bumpear suffix con few-shot ejemplos.

### B12-TP7 (heredado TP7, deferred infra) — Qdrant server v1.7.3 vs client v1.17.1
NO bloquea TP10 (provider pattern no toca Qdrant directamente).

### B14-TP8 + B15-TP8 + B17-TP8 + B18-TP9 (RESUELTOS)
TP10 verificación pre-flight requerida (parent_span_id chain live).

### B16-TP8 (heredado TP8, deferred — F9 docstring scaling underestima)
NO bloquea TP10.

### B19-TP9 (NUEVA TP9, deferred — S9.9 latency target unrealistic)
- **Síntoma:** TP9 §S9.9 target p50 ≤8s falla en multi-step Kimi K2.6 chains. Real p50 ~25s.
- **Por qué deferred:** No es regresión — es performance baseline real de Kimi K2.6 thinking-disabled para sequential tool chains. Decisión propuesta: bump phase doc TP9 §S9.9 a `p50 ≤25s, p95 ≤35s, hard fail >60s`.
- **Lección TP10:** NO heredar latency targets de phase docs sin recalibrar contra el provider mix actual. Confirmar empíricamente con 2-3 turns reales antes de declarar fail.

## Aprendizajes accionables de TP9

- **Schema gaps cross-stack BE↔FE pasan silencioso si no hay parity test.** B18-TP9 destapó que F2 redesign emitía `card_kind:"plan_card"` raw dict bypassing Pydantic CardBlock validación, y FE caía a default NavigationCard sin error console. Backend tests verde + FE tests verde individualmente. Para TP10, **chequear simétricamente que cualquier salida observable cross-layer (cards, system prompt sections, tools API) esté tipada en ambos lados + tiene test que ejercise el dispatch end-to-end** (no solo el emit). Sino `add tool dummy` puede pasar BE test + romper user-visible silenciosamente.
- **Sample variance LLM compliance amerita 2-3 phrasing variants por escenario "trigger".** S9.2 (audit explícito) → write_todos. S9.9-2 (diseño implícito) → 0 write_todos. S9.9-3 (audit + "Usá write_todos") → write_todos. Para TP10, cuando valides "tool dispatch", probá ≥2 phrasings que conceptualmente activen el mismo tool — Kimi K2.6 thinking-disabled es phrasing-sensitive.
- **Latency targets pre-Sprint-0 son optimistas para Kimi K2.6 sequential tool chains.** S9.9 target ≤8s heredado de cuando AGENT=gpt-4o. Post Sprint 0 Kimi K2.6 = ~25s p50 multi-step real. Para TP10, NO heredar targets de phase docs sin recalibrar contra el provider mix actual.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) — todos outputs user-facing tocados deben verificarse.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + recreate.
7. Stage por nombre en commits (parallel-safety).
8. Tools que ejecuten SQL/external calls dentro de un tool deben usar broad `except Exception` + `logger.exception` (pattern B7-TP5 establecido).
9. **Verification deterministic > tool_call count** (pattern B8-TP6 + B12+B13-TP7 + B14+B15+B17-TP8 + B18-TP9 establecido). Si target SLO depende de "X result populated", agregar SQL probe que confirme nullable=False columns no NULL.
10. **Schema parity BE↔FE = test against both sides, no per-side tests aisladas.** Lección B18-TP9. BE tests + FE tests pueden estar verde pero el cross-layer dispatch silenciosamente roto. Cualquier card_kind / system prompt section / tool API que cruce capa requiere arch test BE↔FE parity.
11. **Cleanup obligatorio módulos test post-TP10.** El dummy `_test_provider/` se borra al cerrar TP10. NO commitear.

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP10-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP11** (1-3 bullets accionables o omitir si no hay) + sección **§Cost split per-provider**.
2. `docs/domains/copilot/testing-2026-04/prompts/TP11-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP11 (end-to-end UX heurística Claude Code feel) + research mandate de `phases/TP11-end-to-end-ux.md` + anomalías heredadas (incluir TP4-B5 obs gap si sigue sin fix + B12 + B16 + B19 + cualquier nueva).
3. Si `phases/TP10-*.md` cambió → commit incluido.
4. Cleanup `_test_provider/` removido (verificar con git status).
5. Commits conventional + push a `origin/development`.
6. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP11-start.md` + provider discovery / tool dispatchable veredicto + schema parity BE↔FE check.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o router boot check.
- Mockear LLM cuando TP exige real-LLM (TP10 dummy tool dispatch debe ser real Kimi K2.6 para validar tool selection genuina).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes Claude Code para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP11 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP11).
- Embeber el prompt TP11 dentro del reporte `results/TP10-*.md` — vive en `prompts/TP11-start.md`, el reporte sólo referencia el path.
- **Lección TP6+TP7+TP8+TP9**: contar tool_call rows como prueba de "X funcionando". Validar deterministic verification + schema parity cross-layer.
- **Lección TP9**: dejar `_test_provider/` en commit final. Cleanup obligatorio.
- **Lección TP9**: heredar phase doc targets sin recalibrar empíricamente contra provider mix actual.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn (~40s TTL).
- Discovery no encuentra dummy → check `discover_providers()` glob pattern vs `_test_provider/copilot_provider/manifest.py` path.
- Tool no aparece bound → check `_build_tool_groups` route allowlist excluye `_test_*`.
- Import abre DB → check side effects en `manifest.py` o `tools.py` import chain.
- Arch test rompe → `KNOWN_CROSS_MODULE_IMPORTS` allowlist en `test_ddd_boundaries.py` con justificación.
- Span tree NULL en TP10 turns → B15-TP8 regression. Verificar `node_trace.py::emit_node_trace_event` propaga run_id/parent_ids.
- BE↔FE schema gap (lección B18-TP9) → verificar BE Literal + registry + FE union + dispatcher case + render component + parity test.
- Container env stale (post `.env` edit) → `docker compose up -d --force-recreate api_dev`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check + discover_providers baseline + parent_span_id chain check + deepagents version check + sanity-check F1 source code wiring. Recién después tocás tools.
