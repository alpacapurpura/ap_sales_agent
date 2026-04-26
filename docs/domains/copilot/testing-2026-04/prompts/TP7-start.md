```
Iniciar TP7 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP7

Validar F10 (`MarketingKbStore` + `nicolify_marketing_kb` Qdrant collection + `knowledge_search` tool + 31 docs curados) + F11.5 (`weekly_copilot_rag_eval` cron). Confirmar:

1. 8/8 RAG goldens recall ≥0.875 contra KB real (no stub).
2. `knowledge_search` tool emite output con methodology label citable + latencia search ≤500ms p50.
3. Citation_accuracy + answer_groundedness ≥4.0 (judge multi-dim).
4. Cross-tenant determinism: KB es global tenant-agnóstico.
5. Manual run de `weekly_copilot_rag_eval` produce row en `copilot_workflow_metric._rag_eval` con `extra_metadata` esperada.
6. Admin `/marketing-kb` 4 tabs render OK.
7. Conversación e2e visible cita StoryBrand u otra metodología cuando se pide.
8. **Provider routing per-role correcto bajo F10 (heredado TP4-TP6 gate Sprint 0)** — knowledge_search NO debe romper Kimi K2.6 no-thinking + temp=0.6 régimen.

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP7-marketing-kb-rag.md`
8. `docs/domains/copilot/testing-2026-04/results/TP6-2026-04-26.md` (aprendizajes + B7+B8 fixes commiteados + B11 deferred)
9. `docs/domains/copilot/redesign-2026-04/learnings/F10-marketing-kb.md` (F10 source — leer ANTES de ejecutar)
10. `docs/domains/copilot/redesign-2026-04/learnings/F11-router-wire-and-rag-eval.md` (F11.5 source si existe)
11. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`
12. **TP6 commits (`git log --oneline -8`):** B7-TP6 voseo arch fix / B8-TP6 sanitizer channel enforce / static.j2 + tools_hint.j2 strengthen / output_sanitizer 3 safety nets compose / chat.py user_msg propagation.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP7-marketing-kb-rag.md §Research mandate`:
- `qdrant collection size optimization 2026 dense vector`
- `contextual chunking RAG retrieval recall 2026 benchmarks`
- `text-embedding-3-large openai 2026 pricing dimension`

Tessl tiles: skill `tessl-context` para tile sobre RAG / Qdrant / OpenAI embeddings si existe.

Si descubrís escenario crítico no listado en TP7 doc, agregalo a `phases/TP7-marketing-kb-rag.md` ANTES ejecutar (lección TP6 reforzada).

**Sanity check API real (lección TP3+TP4+TP5+TP6 reforzada — NO SKIPEAR):** ANTES de ejecutar S7.x, leer la signature real de `MarketingKbStore` + `knowledge_search` tool en `backend/src/modules/copilot/infrastructure/qdrant/marketing_kb_store.py` + `backend/src/modules/copilot/application/tools/` y confirmar:
1. F10 efectivamente shipea el store + tool, NO solo declarations.
2. `knowledge_search(query, scope)` está wired a tools registry + bound en routes relevantes.
3. La synthesis post-knowledge_search efectivamente cita el chunk en el output (TP6 lesson: tool call OK ≠ tool result usado).
4. Hay `_rag_eval` workflow registered + Streamlit `/marketing-kb` page funcional.

Si encontrás divergencias vs phase doc TP7, ajustar phase doc PRIMERO antes de correr.

**Sanity check verification deterministic (lección TP6 B8 reforzada):** TP6 destapó que el AGENT (Kimi K2.6) puede llamar tools y NO usar el resultado. Para TP7 RAG, contar `tool_call name='knowledge_search'` rows en trace NO basta — verificar que los `chunks` retornados aparezcan literalmente en la respuesta (regex match o judge dim). Si no aparecen, considerar safety net en sanitizer (similar a TP6 channel format enforcement) o aceptar como B-tp7-XX deferred.

## Setup heredado (NO rehacer — verificado en TP1+TP2+TP3+TP4+TP5+TP6 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn — TP6 confirmó refresh ~40s necesario)
- `.env`: `CLERK_TEST_SESSION_ID` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` + Sprint 0 vars (DEEPSEEK_API_KEY + KIMI_API_KEY + DASHSCOPE_API_KEY + AI_PROVIDER_<ROLE>)
- Tenants test:
  - **alpaca-2** `c67c9845-6cf7-4aee-beba-7e177e84d167` — brand_summary v2 (580 chars, voice "dinámica, moderna"). **Tenant primario TP6 + TP7** (Visionarias `6347e21e-…` SIN brand_summary row, no usable para escenarios brand-voice).
- TP1+TP2+TP3+TP4+TP5+TP6 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) façade resuelve provider per-role.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key`.
- **TP4+TP5+TP6 confirma routing live:**
  - REASONING DeepSeek deepseek-reasoner OK.
  - **AGENT Kimi K2.6** OK con régimen **NO-THINKING + temperature=0.6** (post B4+B8 reset, ver TP5).
  - NANO/FAST OpenAI gpt-4o-mini OK.
  - Qwen 401 (cuenta sin verificar — A6 anomaly heredada, NO bloquea TP7).

### NUEVO TP6 fixes (commits incluidos en este push)
- **B7-TP6 voseo cross-channel arch fix** — `copilot_system_static.j2` explicit "español neutro latinoamericano" + glosario voseo→neutro contraste. `synthesizer.py` fallback strings neutro. `output_sanitizer.py::correct_voseo_in_text` regex map 50+ formas con preservación capitalización. Tests: `test_system_prompt_neutro_latam.py` (12) + `test_output_sanitizer_channel_and_voseo.py` voseo block (12).
- **B8-TP6 SMS overflow arch fix** — `output_sanitizer.py::detect_channel_in_user_msg` + `enforce_channel_format_if_needed` deterministic safety net. `chat.py::_run_graph_stream` agrega `user_msg` kwarg. `chat.py::stream_chat` propaga. `chat.py::_sanitize_ai_messages` propaga a persistence. Tests: 21 en `test_output_sanitizer_channel_and_voseo.py`.
- **`copilot_system_tools_hint.j2`** — sección `format_for_channel` explícita con flujo obligatorio + límites por canal cuando tool está bound.
- **TP6 phase doc reframed** — failure playbook actualizado + sección "Arquitectura post-TP6" con 3 safety nets.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}" | head -10
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP7 — confirmar router per-role boot OK + Kimi K2.6 régimen B8 sigue activo:
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

# Output esperado (idem TP5+TP6):
# NANO       -> openai     (gpt-4o-mini)
# REASONING  -> deepseek   (deepseek-reasoner)
# FAST       -> openai     (gpt-4o-mini)
# VISION     -> openai     (gpt-4o)
# AGENT      -> kimi       (kimi-k2.6)
# EMBEDDING  -> openai     (text-embedding-3-large)
# AGENT temp = 0.6
# AGENT extra_body = {'thinking': {'type': 'disabled'}}

# CRÍTICO TP7 — Qdrant collection nicolify_marketing_kb pob:
docker exec visionarias_qdrant curl -sS http://localhost:6333/collections/nicolify_marketing_kb 2>&1 | head -20
# Esperado: status='ok', result.config.params.vectors.size=3072 (text-embedding-3-large), points_count ≥31

# Container env reflect Sprint 0 (CRÍTICO post-restart):
docker exec visionarias_brain_dev env | grep -E "AI_PROVIDER_AGENT|AI_MODEL_AGENT|KIMI_API_KEY"
# Si AI_PROVIDER_AGENT no aparece → docker compose up -d --force-recreate api_dev (recreate, no solo restart)
```

Si router boot falla → resolver Sprint 0 setup primero, NO arrancar TP7. Si Qdrant collection no tiene 31 docs → `python scripts/seed_nicolify_marketing_kb.py` antes.

## Patrón llamada API + SQL probes

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: c67c9845-6cf7-4aee-beba-7e177e84d167" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: text/event-stream" \
  -d '{"message":"explicame StoryBrand para mi marca","conversation_id":null,"client_context":{"current_route":"/copilot"}}'
```

**Importante TP7:** F10 RAG es output-stage (similar a TP6 channel formatter) integrada a `knowledge_search` tool + system prompt MARKETING_KB_HINT layer. Probable trigger via tool call cuando user pregunta sobre methodology / framework / how-to. Verificar en F10 source qué patrón usa.

DB:
- `copilot_trace_event` con `event_type='tool_call'` filtered name='knowledge_search'.
- `copilot_conversations.messages` (JSONB con AI messages — verificar citation aparece en bloques type=text).
- `copilot_workflow_metric` con `workflow_id='_rag_eval'` para S7.6 manual run.

SQL probes en `01-tooling.md §Infraestructura interna` + `phases/TP7-marketing-kb-rag.md §Tools / queries`.

## Anomalías heredadas (de TP1+TP2+TP3+TP4+TP5+TP6 + Sprint 0)

### A1 (heredado TP3, neutralizado TP4-TP6) — OpenAI quota
0 errores TP6. Continuar monitoreo.

### A2 (heredado TP3+TP4) — Voseo en strings user-facing copilot module
**RESUELTO TP6** vía B7-TP6 fix arquitectónico. Cierra A2.

### A3 (heredado TP2 design) — Lighthouse route-gated
TP7 puede correr en `/copilot` (ruta general) o `/brand-studio` según escenario.

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k
NANO/FAST en OpenAI siguen vulnerables. Spacing ≥1s recomendado.

### A5 (heredado TP1 B3) — `cost_usd` log no aplica cache discount + Kimi/DeepSeek pricing missing
Sigue pendiente.

### A6 (heredado Sprint 1) — Qwen DashScope 401
NO bloquea TP7.

### TP4-B5 (heredado TP4, deferred) — Provider routing observability gaps
TP6 no usó "force 400 → vanish" — confirmó Kimi via tool_call name='format_for_channel' rows directos en trace. TP7 puede usar similar pattern para knowledge_search.

### TP4-B6 (heredado TP4, deferred) — intent_classifier miscalsifica cross-tabla
NO afectó TP6.

### TP5-B9 (heredado TP5, deferred) — F6 cutover gap
NO afecta TP7 (RAG es independiente de F6).

### TP5-B10 (heredado TP5, deferred) — `awareness.py` other `_check_*` funcs same narrow except
NO afecta TP7.

### TP6-B11 (NUEVO TP6, deferred) — Kimi K2.6 thinking-disabled compliance ~50% para "use tool result verbatim"

**Síntoma:** AGENT llama tool (format_for_channel en TP6 caso) pero ignora el `content` retornado ~50% del tiempo. Mitigado en TP6 vía sanitizer arch fix.

**Riesgo TP7:** RAG `knowledge_search` retorna chunks. Si AGENT ignora chunks y paraphrasea sin cita, `citation_accuracy` baja. **Verificar TP7 que respuesta menciona explícitamente methodology label / source_doc del chunk top-1**.

**Plan:** monitor en TP7 S7.5 + S7.8. Si compliance baja, agregar safety net similar a TP6 (e.g. citation footer post-LLM injection cuando knowledge_search se ejecutó). Decision arquitectónica multi-fase.

## Aprendizajes accionables de TP6

- **Sanitizer último escalón > prompt-trust con Kimi K2.6 thinking-disabled (B8-TP6)**: F-pos siempre debe agregar safety net deterministic en sanitizer/post-process para targets hard-fail. F10 RAG citation accuracy puede tener issue similar — si AGENT cita pero re-paraphrasea sin source mention, considerar inyectar citation footer post-LLM si tool `knowledge_search` devolvió chunks.
- **Tool calls sin verificación deterministic = false confidence**: TP6 destapó que `tool_call` row con `status='ok'` NO garantiza que el AGENT use el resultado. Para TP7 RAG, contar `tool_call name='knowledge_search'` rows NO es prueba de retrieval funcional — verificar que los `chunks` retornados aparezcan en la respuesta final (regex match o judge dim).
- **Phase doc actualizar al fin del TP**: TP6 actualizó playbook + sección "Arquitectura post-TP6" antes de cerrar. TP7 debe hacer lo mismo cuando descubra escenarios nuevos (no esperar al final).

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) — TP6 cerró regla cross-channel pero TP7 puede tocar synthesizer/RAG output que necesite verificación.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + recreate.
7. Stage por nombre en commits (parallel-safety).
8. Tools que ejecuten SQL/external calls dentro de un tool deben usar broad `except Exception` + `logger.exception` (pattern B7-TP5 establecido).
9. **Verification deterministic > tool_call count** (pattern B8-TP6 establecido). Si el target SLO depende de "AGENT use tool result", agregar safety net post-LLM o validar regex chunks-in-output.

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP7-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP8** (1-3 bullets accionables o omitir si no hay) + sección **§Cost split per-provider** mostrando cost real RAG.
2. `docs/domains/copilot/testing-2026-04/prompts/TP8-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP8 (quality + observability, F9 + F11.5), research mandate de `phases/TP8-quality-eval-observability.md`, anomalías heredadas (incluir B5 obs gap + B9 F6 cutover + B10 awareness sweep + B11 Kimi compliance si siguen sin fix).
3. Si `phases/TP7-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP8-start.md` + cost saved vs baseline.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o router boot check.
- Mockear LLM cuando TP exige real-LLM (RAG necesita real-LLM + Qdrant real para validar retrieval+citation flow).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP8 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP8).
- Embeber el prompt TP8 dentro del reporte `results/TP7-*.md` — vive en `prompts/TP8-start.md`, el reporte sólo referencia el path.
- **NUEVO TP7 (lección TP6 B8)**: contar `tool_call` rows como prueba de "tool funcionando". Validar el output downstream usa el resultado del tool (regex chunks-in-output, citation match, etc.).
- **NUEVO TP7**: asumir que F10 está integrado solo porque `marketing_kb_store.py` existe — verificar wiring synthesizer/orchestrator antes de scenarios (lección TP5+TP6).

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn (~40s TTL).
- Qdrant collection vacío → `python scripts/seed_nicolify_marketing_kb.py`.
- Kimi 400 vuelve → re-verificar B4+B8 (temp 0.6 + thinking disabled). Ver TP5 results §B8.
- AGENT no cita chunks → revisar trace `tool_call name='knowledge_search'` data.output_preview vs respuesta final. Si chunks retornados pero no en respuesta → B11-similar deferred + considerar safety net.
- Container env stale (post `.env` edit) → `docker compose up -d --force-recreate api_dev`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check + Qdrant collection check + sanity-check F10 source code wiring. Recién después tocás tools.
```
