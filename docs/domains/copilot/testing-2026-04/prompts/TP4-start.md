# TP4 start prompt (post Sprint 0 multi-provider)

Copy-paste lo siguiente en una conversación nueva de Claude Code (`development`):

```
Iniciar TP4 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP4

Validar F5 (`ask_tenant_data` subgraph: intent → resolve → query → state-check → synthesize, 2 LLM calls FAST). Confirmar:
1. Preguntas naturales devuelven respuesta correcta SIN SQL crudo en prompt.
2. Subgraph resuelve fuzzy matching ("oferta de cocina" → "Curso de Cocina Vegetariana") + fechas relativas ("esta semana", "últimos 30 días").
3. State-check intercepta empty: "no encontré leads…" en vez de inventar número.
4. Latencia ≤2.5s p50 (subgraph + 2 LLM calls; bumped from 1.5s post Sprint 0 — DeepSeek REASONING desde LATAM).
5. Groundedness ≥4.5: cero alucinaciones de números (DeepEval `FaithfulnessMetric` ≥0.85 avg).
6. **Provider routing per-role correcto vía `copilot_trace_event` (nuevo gate post Sprint 0).**

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md` (cost table actualizada per-provider)
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP4-ask-tenant-data.md` (incluye sección "Setup multi-provider")
8. `docs/domains/copilot/testing-2026-04/results/TP3-2026-04-26.md` (aprendizajes + anomalías heredadas — A1 OpenAI quota YA NO bloquea: REASONING+AGENT en chinos)
9. `docs/domains/copilot/redesign-2026-04/learnings/F5-ask-tenant-data.md`
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`
11. **Sprint 0 commits (`git show 9d63c0da ae30d4f9 98d6fe7a 3d306c60 d4699642`):** multi-provider per-role routing + tenant keys + Kimi temp fix + TP4 doc update + plan cost update.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP4-ask-tenant-data.md §Research mandate`:
- `text to SQL agent evaluation 2026 fuzzy matching benchmark`
- `deepagents text-to-sql-agent example 2026`
- `natural language data query LLM hallucination groundedness 2026`

Tessl tiles: skill `tessl-context` para tiles sobre text-to-SQL eval / DeepEval Faithfulness abril 2026.

Si descubrís escenario crítico no listado en TP4 doc, agregalo a `phases/TP4-ask-tenant-data.md` ANTES ejecutar.

**Sanity check API real (lección TP3 S3.7):** ANTES de ejecutar S4.x, leer la signature real de `ask_tenant_data` en `backend/src/modules/copilot/application/tools/ask_tenant_data/__init__.py` y comparar con lo que cada escenario asume. Si difieren, ajustar el phase doc PRIMERO antes de correr.

## Setup heredado (NO rehacer — verificado en TP1+TP2+TP3 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn)
- `.env`: `CLERK_TEST_SESSION_ID=sess_3CoDlDaZ9wye8g5OISeyvwsYiRp` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` (recargado)
- Tenants test:
  - Lighthouse poblado: `c67c9845-6cf7-4aee-beba-7e177e84d167` (alpaca-2 / Alpaca Púrpura) — brand_summary v2 chars=580
  - Sin brand: `9ba0b29a-8507-424f-a48a-896f93218a25` (visionarias-v4)
- **TP3 fixes ya commiteados (B1+B2+B3+B4):** internal LLM stream tag + card_kind extension + ToolMessage parse + zombie filter.
- TP1+TP2 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 nuevos providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService` en `backend/src/shared/infrastructure/llm/providers/`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) — façade ``BaseLLMService`` que resuelve provider per-role vía `settings.AI_PROVIDER_<ROLE>` con fallback `AI_PROVIDER` global.
- `AIProvider` enum extendido: + DEEPSEEK / KIMI / QWEN.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key` (alembic 073 idempotent + applied a DB).
- 24 unit tests verde + 4865 broader suite verde + arch fitness verde.
- `.env` Sprint 0 vars en lugar:
  ```
  AI_PROVIDER_NANO=openai
  AI_PROVIDER_FAST=openai
  AI_PROVIDER_REASONING=deepseek
  AI_PROVIDER_AGENT=kimi
  AI_PROVIDER_VISION=openai
  AI_PROVIDER_EMBEDDING=openai
  AI_MODEL_REASONING=deepseek-reasoner
  AI_MODEL_AGENT=kimi-k2.6
  DEEPSEEK_API_KEY=...
  KIMI_API_KEY=...
  DASHSCOPE_API_KEY=... (set pero cuenta sin verificar — Qwen 401)
  ```
- **Sprint 1 smoke confirmado live:**
  - REASONING (DeepSeek deepseek-reasoner): invoke 1254ms / tool_call OK 1639ms / streaming 29 chunks 1136ms.
  - AGENT (Kimi kimi-k2.6): invoke 1735ms / tool_call OK 1795ms / streaming 101 chunks 3391ms.
  - NANO (OpenAI gpt-4o-mini): invoke 1512ms.
  - Qwen: 401 (cuenta sin verificar — A6 anomaly heredada, NO bloquea TP4).

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP4 — confirmar router per-role boot OK con keys reales:
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

# Output esperado:
# NANO       -> openai     (gpt-4o-mini)
# REASONING  -> deepseek   (deepseek-reasoner)
# FAST       -> openai     (gpt-4o-mini)
# VISION     -> openai     (gpt-4o)
# AGENT      -> kimi       (kimi-k2.6)
# EMBEDDING  -> openai     (text-embedding-3-large)

# Brand summary v2 lighthouse populated:
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "SELECT version, length(summary), updated_at FROM brand_summary WHERE tenant_id='c67c9845-6cf7-4aee-beba-7e177e84d167';"
```

Si router boot falla → resolver Sprint 0 setup primero, NO arrancar TP4. Si DeepSeek 429 → ver A1 abajo (chinos pueden rate-limitarse igual que OpenAI; menos probable pero posible). Si Kimi rate limit → A1 mismo tratamiento.

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

**Per-role tracing (nuevo gate Sprint 0):**
```sql
SELECT data->>'model' AS model, data->>'provider' AS provider, COUNT(*)
FROM copilot_trace_event
WHERE event_type='llm_call' AND turn_id=:turn_id
GROUP BY data->>'model', data->>'provider';
```
Esperado en S4.x: `intent_classifier` → DeepSeek deepseek-reasoner; `synthesizer` → DeepSeek deepseek-reasoner; `agent_node` (si data_query subagent invocado) → Kimi kimi-k2.6. Si NANO/FAST → OpenAI gpt-4o-mini.

## Anomalías heredadas (de TP1+TP2+TP3 + Sprint 0)

### A1 (heredado TP3, neutralizado parcial Sprint 0) — OpenAI quota agotada en cuenta

NEUTRALIZADO: REASONING + AGENT ahora corren en DeepSeek + Kimi. Si OpenAI 429 vuelve, solo NANO/FAST/VISION/EMBEDDING fallan. Mitigación temporal: `unset AI_PROVIDER_NANO AI_PROVIDER_FAST` y setear globalmente otro provider, OR agregar `OPENAI_API_KEY` alternativa. Confirmado recargado al arrancar TP4.

### A2 (TP3) — Voseo en strings user-facing F4

10+ strings detectados en `src/modules/copilot/application/tools/{fetch_url,pin_to_memory}.py`, `infrastructure/web/trafilatura_client.py`, `application/orchestrator/inspirations_layer.py`. NO bloqueante TP4 directamente, pero si TP4 toca prompts de F5 (intent_classifier, synthesizer), aplicar regla 11 antes commit.

### A3 (heredado TP2 design) — Lighthouse route-gated `/dashboard /brand-studio` excluidos

`_INJECTION_SEGMENTS = ("offer-studio", "landing", "campaign", "sales", "growth-studio")`. TP4 desde `/sales` o `/growth-studio` mantiene lighthouse en system prompt; desde `/dashboard` no. NO es bug.

### A4 (heredado TP1 B2, neutralizado Sprint 0) — OpenAI tier TPM 30k

NEUTRALIZADO para REASONING+AGENT. Si NANO/FAST agarra 429 → spacing 35-40s sigue aplicando para roles OpenAI. DeepSeek + Kimi rate limits separados (consultar dashboards si aparece 429 chino).

### A5 (heredado TP1 B3) — `cost_usd` en `turn_end` no aplica cache discount

Sigue activo PERO afecta menos tras Sprint 0: DeepSeek cache discount es 90% (vs OpenAI 50%) — el log overestima ~10x si hay cache hit. Reportar cost ajustado: `cost_real ≈ cost_log × (1 - 0.9 × cache_hit_rate)` para REASONING. Para AGENT Kimi: `(1 - 0.5 × cache_hit_rate)`.

### A6 (NUEVO Sprint 1) — Qwen DashScope intl 401 (cuenta sin verificar)

Key `DASHSCOPE_API_KEY` configurada pero cuenta Alibaba en proceso de verificación (KYC intl). Direct invoke retorna `AuthenticationError: 401 Incorrect API key`. NO bloquea TP4 — Qwen está integrado en arquitectura (`QwenService`) con default OFF (AI_PROVIDER_VISION=openai, AI_PROVIDER_EMBEDDING=openai). Cuando Chris confirme que la cuenta quedó verificada, smoke `python -c "from src.shared.infrastructure.llm.providers.qwen import QwenService; QwenService().get_client(role=ModelRole.VISION).invoke('ping')"`.

### A7 (NUEVO Sprint 1) — Kimi K2.6 requiere `temperature=1.0` (FIXED)

Resuelto en commit `98d6fe7a` — `KimiService._DEFAULT_TEMPERATURE = 1.0`. Si TP4 invoca Kimi con explicit temperature ≠ 1.0 (raro), API retorna `invalid_request_error: only 1 is allowed for this model`. Override solo si tarea legítima lo requiere; default OK.

## Aprendizajes accionables de TP3

- **Internal LLM tag pattern (B1)**: cualquier tool que invoca un LLM como parte de su pipeline DEBE pasar `INTERNAL_LLM_CONFIG` desde `src/modules/copilot/application/orchestrator/stream_filters.py`. Sin la tag, `astream_events` filtra los tokens al canal user-visible. F5 ya hereda en sus 2 tools post-B1.
- **ToolMessage parsing (B3)**: graph tools devuelven `ToolMessage` objects. Cualquier orquestador downstream que necesite leer payload usar `chat._parse_tool_payload(tool_output)`. F5 va a emitir cards (`metric_summary` o equivalente data-snippet); precisa este unwrap.
- **Phase doc sanity check pre-ejecución**: TP3 S3.7 asumía `pin_to_memory(content="...")` pero la API real es `pin_to_memory(slug=...)`. Antes de cada S4.x: leer signature real del subgraph + ajustar phase doc si difiere.
- **NUEVO Sprint 0**: multi-provider routing transparent. Callsites NO cambian (`LLMFactory.get_service().get_client(role)`). Tracing debe capturar `data->>'provider'` + `data->>'model'` para validar el routing per-role per-turn. Si NO aparece el provider correcto en trace para un role → bug del trace recorder, NO de la arquitectura.

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + boot full app (mappers).
7. Stage por nombre en commits (parallel-safety).
8. **NUEVO Sprint 0**: cualquier turn de TP4 debe trace mostrar provider correcto per-role. Si REASONING usa OpenAI cuando debería ser DeepSeek → bug routing, fix YA.

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP4-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP5** (1-3 bullets accionables o omitir si no hay) + sección **§Cost split per-provider** mostrando ahorro real vs all-OpenAI baseline.
2. `docs/domains/copilot/testing-2026-04/prompts/TP5-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP5 (workflows-runtime, F6), research mandate de `phases/TP5-workflows-runtime.md`, anomalías heredadas (incluir A6 Qwen pendiente si sigue sin verificarse).
3. Si `phases/TP4-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP5-start.md` + cost saved vs baseline.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o router boot check.
- Mockear LLM cuando TP exige real-LLM (S4.8 DeepEval Faithfulness obligatorio para groundedness).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP5 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP5).
- Embeber el prompt TP5 dentro del reporte `results/TP4-*.md` — vive en `prompts/TP5-start.md`, el reporte sólo referencia el path.
- **NUEVO**: asumir que un fail con un provider es bug del provider sin verificar primero arch routing. Cross-check con OpenAI baseline si hay diff sospechoso.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn.
- DeepSeek 429 quota → confirmar billing dashboard https://platform.deepseek.com/usage. Si plan agotado, fallback temporal: `AI_PROVIDER_REASONING=openai AI_MODEL_REASONING=gpt-4o` en `.env` y restart.
- Kimi 429 → `AI_PROVIDER_AGENT=openai AI_MODEL_AGENT=gpt-4o` fallback.
- Routing rompe inesperado → `LLMFactory._instance = None; r = LLMFactory.get_service(); print(r.get_provider_for_role(ModelRole.X))` confirmar settings vs runtime.
- ARQ task no corre tras enqueue → `arq:result:{job_id}` stale + `docker logs visionarias_worker`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check. Recién después tocás tools.
```
