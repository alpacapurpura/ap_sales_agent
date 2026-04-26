```
Iniciar TP11 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP11

Validar que el copilot completo se SIENTE como Claude Code para marketing, no solo que cada componente teste OK aislado. Esta fase es la única que pesa heavy en juicio humano + Chrome DevTools live. 8 heurísticas (H1-H8) × 5 user journeys (J1-J5) = score X/8 final del plan F0-F11.

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP11-end-to-end-ux.md`
8. `docs/domains/copilot/testing-2026-04/results/TP10-2026-04-26.md` (B20-TP10 fix arquitectónico ROUTE_TOOL_MAP merge + recomendaciones + aprendizajes)
9. `docs/domains/copilot/redesign-2026-04/learnings/F0-baseline-observability.md` + cualquier F-summary final si existe.
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md` + `.claude/rules/backend-ddd.md` + `.claude/rules/frontend-fsd.md`.
11. **TP10 commits (`git log --oneline -10`):** B20-TP10 ROUTE_TOOL_MAP routes() merge + 3 regression tests + TP10 results doc + phase doc TP10 update + TP11 start prompt.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP11-end-to-end-ux.md §Research mandate`:
- `claude code UX design principles 2026 agent feel`
- `conversational AI usability heuristic evaluation 2026`
- `streaming SSE UI perception latency under 1500ms 2026`

Tessl tiles: skill `tessl-context` para tile sobre Chrome DevTools MCP heuristic eval si existe.

Si descubrís escenario crítico no listado en TP11 doc, agregalo a `phases/TP11-*.md` ANTES ejecutar (lección TP6+TP7+TP8+TP9+TP10 reforzada).

**Sanity check API + UI shell real (lección TP3-TP10 reforzada — NO SKIPEAR):** ANTES de ejecutar J1-J5, leer la signature/shape real de:
- `frontend/src/features/copilot/components/blocks/CardBlock.tsx` — dispatcher actualizado post-B18-TP9 (case "plan_card" debe estar)
- `frontend/src/features/copilot/components/PlanCard.tsx` — componente deepagents shape post-B18-TP9
- `frontend/src/features/copilot/types/message-blocks.ts` — CardKind union completa
- `backend/src/modules/copilot/api/chat.py::_write_todos_to_plan_card` + `_maybe_emit_plan_card` — emisor live
- `backend/src/modules/copilot/application/orchestrator/deep_agent.py::_DEEP_AGENT_SUFFIX_ES` — system prompt vivo
- `backend/src/modules/copilot/application/tools/registry.py::_BASE_ROUTE_TOOL_MAP + _build_route_tool_map` post-B20-TP10
- Tenant alpaca-2 state actual: brand_summary v2 + offer + leads + connections (revisar cardinality vs targets J1-J5)

**Phase doc validation gate (lección B21-TP10):** confirmar que `phases/TP11-*.md` no está stale vs source code. Si encuentra divergencias (paths obsoletos, métodos renombrados, UI shells movidas), ajustar phase doc PRIMERO antes de correr.

**Sanity check verification deterministic (lección TP6-TP10 reforzada):**
- TP6 destapó tool_call ≠ tool result usado.
- TP7 destapó test stub != arquitectura real.
- TP8 destapó schema drift silent + span tree gap silent.
- TP9 destapó BE↔FE schema gap silent (B18).
- TP10 destapó ROUTE_TOOL_MAP estático ignorando provider.routes() (B20).

Para TP11 (e2e UX), agregar checks deterministicos por journey:
- **J1 (setup brand):** SQL probe `brand_identity WHERE tenant=alpaca-2` antes/después → confirmar fields populated post-T7.
- **J2 (URL inspiration):** `inspiration_*` table o trace event `card_emitted card_kind='inspiration_saved'` post-T2.
- **J3 (data Q&A):** trace event tool_call name='ask_tenant_data' + output_preview con números.
- **J4 (audit):** plan_card payload con todos[] populated + status transitions completed visible en SSE.
- **J5 (KB citation):** trace event tool_call name='knowledge_search' + citation in final markdown.

Sin probe deterministic, juicio humano "se sintió bien" = unverifiable.

## Setup heredado (NO rehacer — verificado en TP1+...+TP10 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 + deepagents 0.5.3 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn — TP6+TP7+TP8+TP9+TP10 confirmó refresh ~40s necesario)
- `.env`: `CLERK_TEST_SESSION_ID` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` + Sprint 0 vars (DEEPSEEK_API_KEY + KIMI_API_KEY + DASHSCOPE_API_KEY + AI_PROVIDER_<ROLE>)
- Tenants test:
  - **alpaca-2** `c67c9845-6cf7-4aee-beba-7e177e84d167` — brand_summary v2 (580 chars) + 0 ofertas + 6/11 connections + 0 leads. **Tenant primario TP6+TP7+TP8+TP9+TP10.** Para TP11 J1 + J3 + J4 alpaca-2 sirve. Para J2 + J5 podría requerir tenant con offers + leads — confirmar con Chris.
- TP1+...+TP10 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) façade.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key`.
- TP4-TP10 confirma routing live: REASONING DeepSeek, AGENT Kimi K2.6 (no-thinking + temp 0.6), NANO/FAST OpenAI gpt-4o-mini.

### NUEVO TP6-TP10 fixes
- B7-TP6 voseo cross-channel arch fix (3 capas defensa).
- B8-TP6 SMS overflow arch fix (output_sanitizer enforce_channel_format_if_needed).
- B12-TP7 Qdrant REST fallback en marketing_kb_store.search.
- B13-TP7 judge dynamic prompt builder + `_DIMENSION_RUBRICS` registry.
- B14-TP8 qdrant stats schema fix.
- B15-TP8 node_trace span tree propagación (run_id + parent_ids).
- B17-TP8 accuracy rubric scope-refusal.
- B18-TP9 plan_card schema gap BE+FE (CardBlock Literal + registry + FE union + dispatcher + PlanCard rewrite + 6 tests).
- B20-TP10 ROUTE_TOOL_MAP routes() merge fix arquitectónico (`_BASE_ROUTE_TOOL_MAP` + `_build_route_tool_map()` + 3 regression tests). Cierra F1 plug-and-play promise end-to-end.
- KB seedeado: `nicolify_marketing_kb` 304 chunks / 31 docs.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}" | head -10
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python -c "import deepagents; print('deepagents', deepagents.__version__ if hasattr(deepagents, '__version__') else 'unknown')"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP11 — confirmar router per-role boot OK + Kimi K2.6 régimen sigue activo:
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

# CRÍTICO TP11 — F1 plug-and-play funcionando post-B20:
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('/home/chris/AISALESHT/.env')
from src.modules.copilot.application.discovery import discover_providers
import src.modules.copilot.application.tools.registry as reg
print('providers:', sorted(discover_providers().keys()))
print('TOOL_GROUPS keys:', sorted(reg.TOOL_GROUPS.keys()))
print('ROUTE_TOOL_MAP[*]:', reg.ROUTE_TOOL_MAP['*'])
"

# CRÍTICO TP11 — span tree wiring sigue vivo post-B15 + plan_card schema post-B18:
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "
SELECT event_type, COUNT(*) total, COUNT(parent_span_id) with_parent
FROM copilot_trace_event
WHERE event_type IN ('node_enter','node_exit') AND created_at >= NOW() - INTERVAL '30 minutes'
GROUP BY event_type;"
# Esperado: total = with_parent. Si hay gap → B15 regression.

# Container env reflect Sprint 0 (CRÍTICO post-restart):
docker exec visionarias_brain_dev env | grep -E "AI_PROVIDER_AGENT|AI_MODEL_AGENT|KIMI_API_KEY"
# Si AI_PROVIDER_AGENT no aparece → docker compose up -d --force-recreate api_dev

# Frontend reachable + Clerk session active:
curl -sS -o /dev/null -w "%{http_code}" http://localhost:3000
# Esperado: 200. Si 500 → docker logs visionarias_client_dev | grep "Module not found"
```

Si router boot falla, deepagents version mismatch, F1 wiring incompleto, parent_span_id NULL en node events recientes, frontend 500, o container env stale → resolver primero, NO arrancar TP11.

## Patrón Chrome DevTools por journey

J1-J5 son flows UX live, no eval-as-code puro. Skill `chrome-devtools-verify` para repro + capture:

```
1. mcp__chrome-devtools__new_page → http://dev-app.nicolify.com (CF tunnel local)
2. Performance trace start (label J{N})
3. Por cada turn: type_text en chat input + wait_for response stream + take_snapshot DOM final + list_console_messages errors + list_network_requests TTFB
4. Performance trace stop → reportar TBT/LCP/INP en results
5. take_screenshot final state
```

SQL probes per journey en `phases/TP11-*.md §Procedimiento por journey`.

## Anomalías heredadas (de TP1+...+TP10 + Sprint 0)

### A1 (heredado TP3, neutralizado TP4-TP10) — OpenAI quota
0 errores TP10. Continúa neutralizado.

### A2 (RESUELTO TP6) — Voseo en strings user-facing copilot module
Cierra A2. Pero **mantener vigilancia TP11** porque journeys son user-facing.

### A2.1 (heredado TP9, deferred — voseo en LLM system prompts internos)
**Persiste.** TP10 no agregó nuevos prompts voseados. Si TP11 detecta voseo en outputs LLM cuyo prompt source está en `subagents/url_analyzer.py` etc, fix arquitectónico inline TP11 (TDD).

### A3 (heredado TP2 design) — Lighthouse route-gated
TP11 corre journeys multi-route — Lighthouse aplica.

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k
NANO/FAST/EMBEDDING OpenAI siguen vulnerables. Spacing recomendado entre journeys (J1→J2 espera 30s).

### A5 (heredado TP1 B3) — `cost_usd` log no aplica cache discount + Kimi/DeepSeek pricing missing
**Persiste.** TP11 estimar manualmente con tokens.

### A6 (heredado Sprint 1) — Qwen DashScope 401
NO bloquea TP11.

### TP4-B5 (heredado TP4, REFORZADO TP8+TP9+TP10) — `llm_call` event no emitido
**Persiste.** Plan agregar `record(event_type='llm_call', model=..., tokens=..., duration_ms=...)` después de cada `astream_events.on_chat_model_end` en chat orchestrator. Para TP11, sin esto el debug "qué LLM corrió este turn" requiere SQL inferences desde routing_decision + node names.

### TP4-B6 (heredado TP4, deferred) — intent_classifier miscalsifica cross-tabla
NO afectó TP10. Si J3 destapa, fix inline.

### TP5-B9 (heredado TP5, deferred) — F6 cutover gap
NO afectó TP10. J1 (setup brand) puede destapar — verificar.

### TP5-B10 (heredado TP5, deferred) — `awareness.py` other `_check_*` funcs same narrow except
NO afectó TP10.

### TP6-B11 (heredado TP6, REFRAMED TP7+TP9) — Kimi K2.6 thinking-disabled compliance ~50% phrasing-sensitive
**Manifestación TP11 esperada:** J4 audit explícito → write_todos disparado. Si user phrasing es implícito (e.g. J2 "armame copy WhatsApp" sin "paso por paso"), Kimi puede no dispararla. Documentar.

### B12-TP7 (heredado TP7, deferred infra) — Qdrant server v1.7.3 vs client v1.17.1
NO bloquea TP11 directamente, pero J5 (KB citation) usa Qdrant — verificar que knowledge_search responde live.

### B14-TP8 + B15-TP8 + B17-TP8 + B18-TP9 + B20-TP10 (RESUELTOS)
TP11 verificación pre-flight requerida (parent_span_id chain live + plan_card render OK + ROUTE_TOOL_MAP merged).

### B16-TP8 (heredado TP8, deferred — F9 docstring scaling underestima)
NO bloquea TP11.

### B19-TP9 (heredado TP9, deferred — S9.9 latency target unrealistic)
- **Síntoma:** S9.9 target p50 ≤8s falla en multi-step Kimi K2.6 chains. Real p50 ~25s.
- **Lección TP11 H1 inmediatez:** target H1 ≤1500ms TTFB es para ARRANCO del stream (block_start), NO para completar turn. Multi-step chain real puede tardar 25s+ para terminar pero el TTFB inicial sigue ≤1500ms si el primer token textual sale rápido. Validar empíricamente — si TTFB se rompe en chains largas (cache invalidation), heredado de pre-Sprint 0 calibración.

### B21-TP10 (heredado TP10, deferred — phase doc validation gate)
- **Síntoma:** phase doc TP10 original tenía paths obsoletos + Protocol shape wrong + dummy naming gotcha. Actualizado durante TP10.
- **Lección TP11:** validar `phases/TP11-end-to-end-ux.md` contra UI shell live + redesign learnings F11 antes de ejecutar — UX heuristics + journey copy rotan más rápido que docs. Especial atención a routes (`/copilot` vs `/[tenantId]/copilot` post-multitenant changes), URL `dev-app.nicolify.com` reachability, brand_summary state alpaca-2 (¿580 chars sigue vigente o cambió post-TPs?).

## Aprendizajes accionables de TP10

- **Phase doc validation gate.** B21-TP10 destapó que phase doc TP10 tenía paths obsoletos (`application/providers/discovery.py` no existía), Protocol shape wrong (4 plain attrs vs 8 métodos), gotcha de naming invisible (`_test_provider` skipped por convention scan). Para TP11, validar phase doc contra UI shell live + redesign learnings F11 antes de ejecutar.
- **F1 plug-in pattern requiere ambos: tool_groups merge + routes merge.** B20-TP10 destapó que `provider.routes()` era port sin consumer en `ROUTE_TOOL_MAP`. Fix: `_build_route_tool_map()` analogous to `_build_tool_groups()`. Para TP11 si se descubre otro port-sin-consumer (e.g. summary_provider, context_injector), aplicar mismo patrón TDD inline.
- **Boot-time discovery + lru_cache implican restart obligatorio para module add/remove.** Documentar en J1 si journey toca admin enable/disable de feature flag — el user puede esperar hot-reload pero realidad requiere restart. Surface en UI o copy.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra. **TP11 agrega 8 heurísticas** evaluadas por journey — UX se mide con score X/8.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando. Score 8/8 = plan F0-F11 cumplió.
5. Spanish neutro LatAm (regla 11) — todos outputs user-facing tocados deben verificarse.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + recreate.
7. Stage por nombre en commits (parallel-safety).
8. Tools que ejecuten SQL/external calls dentro de un tool deben usar broad `except Exception` + `logger.exception` (pattern B7-TP5 establecido).
9. **Verification deterministic > tool_call count** (pattern B8-TP6 + B12+B13-TP7 + B14+B15+B17-TP8 + B18-TP9 + B20-TP10 establecido). Si target SLO depende de "X result populated", agregar SQL probe que confirme.
10. **Schema parity BE↔FE = test against both sides, no per-side tests aisladas.** Lección B18-TP9. Cualquier card_kind / system prompt section / tool API que cruce capa requiere arch test BE↔FE parity.
11. **NO sub-agentes Claude Code para journeys paralelos.** Cada journey requiere context completo + iteración fix — sub-agentes pierden context.

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP11-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Score final 8 heurísticas** (X/8 + breakdown per H1-H8 con evidence) + **§Cost split per-provider** + **§Cierre del plan** (resumen agregado de los 12 TPs + decisión sobre TP repeat / nueva ronda / archivo del plan).
2. Si `phases/TP11-*.md` cambió → commit incluido.
3. **NO se genera `prompts/TP12-start.md`** — TP11 es el último de la serie.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + score X/8 + recomendación de cierre o ronda siguiente.

## Anti-patrones (no caer)

- Reportar "se sintió bien" sin números/evidence.
- Saltar pre-research o sanity-check UI shell.
- Mockear LLM cuando TP exige real-LLM (TP11 journeys son real-LLM end-to-end).
- Cerrar TP con heurística fail abierta sin fix arquitectónico intentado primero.
- Spawnear sub-agentes Claude Code para journeys paralelos.
- Llenar reporte con info no accionable.
- **Lección TP10**: trust que el phase doc está actualizado — validar contra source primero.
- **Lección TP9**: dejar `_test_provider/` o tp10_dummy/ en commit final (TP10 ya cleaned). Verificar `git status` no muestra restos.
- **Lección TP9**: heredar latency targets sin recalibrar empíricamente contra provider mix actual. **Lección TP10:** turns simple ~7.5s; multi-step Kimi K2.6 ~25s — TP11 H1 mide TTFB, no full turn.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn (~40s TTL).
- Frontend 500 → `docker logs visionarias_client_dev | grep "Module not found"` + `npm install <missing>` + restart client_dashboard_dev.
- Chrome DevTools MCP no conecta → verificar WSL2↔Windows bridge via `chrome-wsl` portproxy IPv6 (`feedback_chrome_devtools_verify_fe.md` heredado).
- Span tree NULL en TP11 turns → B15-TP8 regression. Verificar `node_trace.py::emit_node_trace_event` propaga run_id/parent_ids.
- BE↔FE schema gap (lección B18-TP9) → verificar BE Literal + registry + FE union + dispatcher case + render component + parity test.
- Provider tool no llega a LLM (lección B20-TP10) → verificar `provider.routes()` declarada + `_build_route_tool_map` corre + `'X' in ROUTE_TOOL_MAP[prefix]`.
- Container env stale (post `.env` edit) → `docker compose up -d --force-recreate api_dev`.
- Tenant alpaca-2 state vacío para J2/J5 → preguntar a Chris por tenant alternativo con offers + leads + KB poblado.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check + F1 wiring check + parent_span_id chain check + frontend 200 check + UI shell sanity (CardBlock dispatcher case "plan_card" + ROUTE_TOOL_MAP merged). Recién después abrís Chrome DevTools para J1.
```
