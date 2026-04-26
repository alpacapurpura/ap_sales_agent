# TP6 start prompt — copy-paste this fenced block to a fresh conversation

```
Iniciar TP6 plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP6

Validar F7 (`OutputChannelFormat` registry + `format_for_channel` tool + `synthesizer.py::_CHANNEL_HINTS`). Confirmar:
1. Pedir output "para WhatsApp" / "para email" / "para SMS" / "chat" produce formato correcto per canal.
2. Markdown NO sale roto en canales sin support (WhatsApp: `•` o lineas plain, NO `**bold**`).
3. Brand voice/tono preservado mientras adapta al canal.
4. Caracteres especiales (emoji, unicode, ¿¡) preservados.
5. Length limits del canal respetados (SMS ≤160 chars).
6. Spanish neutro LatAm sin voseo (regla 11) en TODOS los outputs.
7. **Provider routing per-role correcto bajo F7 (heredado TP4-TP5 gate Sprint 0)** — channel formatter NO debe romper Kimi K2.6 no-thinking + temp=0.6 régimen.

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos, §5 budget post Sprint 0)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP6-channel-formatter.md`
8. `docs/domains/copilot/testing-2026-04/results/TP5-2026-04-26.md` (aprendizajes + B7+B8 fixes commiteados + B9+B10 deferred)
9. `docs/domains/copilot/redesign-2026-04/learnings/F7-channel-formatter.md` (F7 source — leer ANTES de ejecutar)
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`
11. **TP5 commits (`git log --oneline -8`):** B7 awareness SQL fix / B8 Kimi thinking disabled + temp 0.6 reset / TP5 phase doc reframe / engine direct invocation scenarios.

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 3 web searches del mandate listado en `phases/TP6-channel-formatter.md §Research mandate`:
- `whatsapp business api message formatting markdown 2026`
- `sms 160 character limit segmentation 2026`
- `email html plain text dual format LLM generation 2026`

Tessl tiles: skill `tessl-context` para tile sobre formatting / canal específico si existe.

Si descubrís escenario crítico no listado en TP6 doc, agregalo a `phases/TP6-channel-formatter.md` ANTES ejecutar.

**Sanity check API real (lección TP3+TP4+TP5 reforzada — NO SKIPEAR):** ANTES de ejecutar S6.x, leer la signature real de `synthesizer.py::_CHANNEL_HINTS` + `format_for_channel` tool en `backend/src/modules/copilot/application/tools/` y confirmar:
1. F7 efectivamente shipea el dict + tool, NO solo declarations en `domain/output_channels.py`.
2. `synthesize_answer(..., output_channel: str)` está wired al chat orchestrator.
3. Hay un dispatch del LLM hacia el formatter (vía tool selection / heuristic) — TP5 destapó que F6 era zombie por gap orchestrator. F7 puede tener gap similar.

Si encontrás divergencias vs phase doc TP6, ajustar phase doc PRIMERO antes de correr.

## Setup heredado (NO rehacer — verificado en TP1+TP2+TP3+TP4+TP5 + Sprint 0 smoke)

### Heredado de TPs previos
- Migraciones aplicadas hasta `073_add_chinese_provider_keys` (head)
- DeepEval 3.9.7 + trafilatura 2.0.0 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh per turn)
- `.env`: `CLERK_TEST_SESSION_ID` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY` + Sprint 0 vars (DEEPSEEK_API_KEY + KIMI_API_KEY + DASHSCOPE_API_KEY + AI_PROVIDER_<ROLE>)
- Tenants test:
  - **Visionarias** `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` — 12 productos + 8-15 leads + brand_summary v2 con voice_tone explicit. **Tenant primario TP6 para brand voice + canales.**
  - **alpaca-2** `c67c9845-6cf7-4aee-beba-7e177e84d167` — brand_summary v2 (580 chars).
- TP1+TP2+TP3+TP4+TP5 fixes commiteados.

### NUEVO Sprint 0 multi-provider (commits 9d63c0da + ae30d4f9 + 98d6fe7a)
- 3 providers OpenAI-compat: `DeepSeekService`, `KimiService`, `QwenService`.
- `MultiRoleLLMRouter` (`shared/infrastructure/llm/router.py`) façade resuelve provider per-role.
- `Tenant` model: + `deepseek_api_key` / `kimi_api_key` / `dashscope_api_key`.
- **Sprint 1+TP4+TP5 confirma routing live:**
  - REASONING DeepSeek deepseek-reasoner OK.
  - **AGENT Kimi K2.6** OK con régimen **NO-THINKING + temperature=0.6** (post B4+B8 reset, ver TP5).
  - NANO/FAST OpenAI gpt-4o-mini OK.
  - Qwen 401 (cuenta sin verificar — A6 anomaly heredada, NO bloquea TP6).

### NUEVO TP5 fixes (commits incluidos en este push)
- **B7 awareness SQL fix** — `awareness.py:_check_offer_completion` query alineada con partial index `ix_products_active_by_tenant`: `WHERE tenant_id=:tid AND deleted_at IS NULL AND archived_at IS NULL`. Broad `except Exception` + `logger.exception` reemplaza narrow `(TypeError, ValueError)`. Test regression: `test_awareness_offer_completion.py` (4 cases).
- **B8 Kimi K2.6 thinking disabled + temp 0.6 reset** — `KimiService._get_chat_model` fuerza `extra_body={"thinking": {"type": "disabled"}}` para todo K2 + clampea `_K2_REQUIRED_TEMPERATURE = 0.6`. Reconciliación con B4: thinking-enabled exigía temp=1.0; thinking-disabled exige 0.6. Tests: `test_k2_6_disables_thinking_mode` + `test_k2_6_temperature_clamped_to_required_value` + `test_kimi_k2_temperature_clamped_for_agent_role` (factory wire).
- TP5 phase doc reframed: F6 es zombie live (no hay cutover orchestrator). Scenarios reframed a engine direct invocation + persistence live + chat coexistence regression.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}" | head -10
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30

# CRÍTICO TP6 — confirmar router per-role boot OK + Kimi K2.6 régimen B8:
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('/home/chris/AISALESHT/.env')
from src.core.config import Settings; import src.core.config as cfg; cfg.settings = Settings()
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory
LLMFactory._instance = None
r = LLMFactory.get_service()
for role in ModelRole:
    print(f'{role.name:10s} -> {r.get_provider_for_role(role).value:10s} ({cfg.settings.get_model(role)})')
# Kimi K2.6 régimen post-B8 verificación:
client = r.get_client(role=ModelRole.AGENT)
print(f'AGENT temp = {client.temperature}')
print(f'AGENT extra_body = {client.model_kwargs.get(\"extra_body\", {})}')
"

# Output esperado (idem TP5):
# NANO       -> openai     (gpt-4o-mini)
# REASONING  -> deepseek   (deepseek-reasoner)
# FAST       -> openai     (gpt-4o-mini)
# VISION     -> openai     (gpt-4o)
# AGENT      -> kimi       (kimi-k2.6)
# EMBEDDING  -> openai     (text-embedding-3-large)
# AGENT temp = 0.6
# AGENT extra_body = {'thinking': {'type': 'disabled'}}

# Container env reflect Sprint 0 (CRÍTICO post-restart):
docker exec visionarias_brain_dev env | grep -E "AI_PROVIDER_AGENT|AI_MODEL_AGENT|KIMI_API_KEY"
# Si AI_PROVIDER_AGENT no aparece → docker compose up -d --force-recreate api_dev (recreate, no solo restart)
```

Si router boot falla → resolver Sprint 0 setup primero, NO arrancar TP6. Si Kimi 400 vuelve con "only 0.6 is allowed" → confirmar B8 disable thinking aplicado (`grep "thinking.*disabled" backend/src/shared/infrastructure/llm/providers/kimi.py`). Si Kimi 400 con "thinking enabled but reasoning_content missing" → B8 fue revertido, restaurar.

## Patrón llamada API + SQL probes

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 6347e21e-8112-4aa1-80d3-6adaa73bf6f9" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"<test>","conversation_id":null,"client_context":{"current_route":"/copilot"}}'
```

**Importante TP6:** F7 channel formatter es output-stage, integra con `synthesizer.py`. Probable trigger via tool `format_for_channel(channel, content)` o via tool description hint en `synthesize_answer(output_channel=...)`. Verificar en F7 source qué patrón usa.

DB:
- `copilot_trace_event` con `event_type='tool_call'` filtered name='format_for_channel' o name='synthesize_answer' depending wiring.
- `copilot_conversations.messages` (JSONB con AI messages — verificar markdown integrity per canal en bloques type=text).

SQL probes en `01-tooling.md §Infraestructura interna` + `phases/TP6-channel-formatter.md §Tools / queries`.

## Anomalías heredadas (de TP1+TP2+TP3+TP4+TP5 + Sprint 0)

### A1 (heredado TP3, neutralizado TP4+TP5) — OpenAI quota
0 errores en TP4+TP5. Continuar monitoreo en TP6.

### A2 (heredado TP3+TP4) — Voseo en strings user-facing copilot module
TP4 detectó instancias en `synthesizer.py:74,81` (`querés/podés`). NO fixeado en TP4-TP5. **TP6 directamente cubre regla 11 cross-channel — si encuentra voseo, fix inline.**

### A3 (heredado TP2 design) — Lighthouse route-gated
TP6 puede correr en `/copilot` (sin lighthouse) o en route con lighthouse según escenario.

### A4 (heredado TP1 B2) — OpenAI tier TPM 30k
NANO/FAST en OpenAI siguen vulnerables. Spacing ≥1s recomendado entre 16 escenarios matrix.

### A5 (heredado TP1 B3) — `cost_usd` log no aplica cache discount + Kimi/DeepSeek pricing missing
Sigue pendiente. Logs reportan $0 para AGENT en Kimi.

### A6 (heredado Sprint 1) — Qwen DashScope 401
NO bloquea TP6.

### TP4-B5 (heredado TP4, deferred) — Provider routing observability gaps
Patrón "force 400 → vanish" sigue siendo el único validation path. TP5 lo usó OK.

### TP4-B6 (heredado TP4, deferred) — intent_classifier miscalsifica cross-tabla
NO afectó TP4-TP5. Probablemente NO afecta TP6 (canal formatter es output-stage, post-intent).

### TP5-B9 (NUEVO TP5, deferred) — F6 cutover gap
Workflows F6 son zombies live. NO afecta TP6 directly (channel formatter es output-stage independiente). Pero TP11 e2e UX requiere F6 live → F-pos cutover prerequisito de TP11.

### TP5-B10 (NUEVO TP5, deferred) — `awareness.py` other `_check_*` funcs same narrow except
NO afecta TP6. Plan: sweep en TP-housekeeping o TP8.

## Aprendizajes accionables de TP5

- **Kimi K2.6 thinking mode coupling con temperature regime (B8+B4 reset)**: F7 callsites que invoquen Kimi via `LLMFactory.get_client(role=AGENT)` heredan el clamp `temp=0.6` + thinking disabled. Si F7 introduce nuevo callsite con `extra_body` propio para canales (improbable, channel formatter es output-stage), respetar el merge `existing_extra | thinking_disabled` en `KimiService` (pattern ya en place). NO instanciar `ChatOpenAI` directo — bypassea ambos clamps.
- **Schema drift en awareness tools (B7+B10)**: cuando F7 toque tools que ejecuten SQL contra módulos del registry, replicar el pattern broad-except + logger.exception. Narrow except `(TypeError, ValueError)` es trampa heredada que TP5 destapó solo en `_check_offer_completion` — el resto de awareness puede romper igual cuando otra tabla cambie schema.
- **Sanity-check phase doc vs source code reality (lección TP3+TP4 reforzada)**: TP5 phase doc original estaba 100% basado en F6 cutover live que NO existe. Detectar pre-execution ahorró ~3 hs. TP6 debe leer F7 source + verificar que channel formatter está realmente integrado al synthesizer (no solo declared como en F6).

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado. **TP6 cubre regla 11 directly por matrix de canales.**
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec` para lint/tests. Docker SOLO para runtime + recreate (env propagation).
7. Stage por nombre en commits (parallel-safety).
8. Tools que ejecuten SQL/external calls dentro de un tool deben usar broad `except Exception` + `logger.exception` (pattern B7 establecido TP5).

## Output esperado al cerrar (OBLIGATORIO — protocolo §Paso 9)

1. `docs/domains/copilot/testing-2026-04/results/TP6-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir sección **§Aprendizajes para TP7** (1-3 bullets accionables o omitir si no hay) + sección **§Cost split per-provider** mostrando cost real channel formatter.
2. `docs/domains/copilot/testing-2026-04/prompts/TP7-start.md` (template canónico `04-protocol.md §Anexo A`). Adaptado: misión TP7 (marketing KB RAG, F10), research mandate de `phases/TP7-marketing-kb-rag.md`, anomalías heredadas (incluir B5 obs gap + B9 F6 cutover + B10 awareness sweep si siguen sin fix).
3. Si `phases/TP6-*.md` cambió → commit incluido.
4. Commits conventional + push a `origin/development`.
5. Reporte al user: 3 líneas resumen + paths al `results/` + `prompts/TP7-start.md` + cost saved vs baseline.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research o router boot check.
- Mockear LLM cuando TP exige real-LLM (canales necesitan real-LLM para validar formatting).
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos.
- Llenar reporte con info no accionable.
- Generar prompt TP7 genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP7).
- Embeber el prompt TP7 dentro del reporte `results/TP6-*.md` — vive en `prompts/TP7-start.md`, el reporte sólo referencia el path.
- **NUEVO TP6**: asumir que F7 está integrado solo porque `output_channels.py` existe — TP5 mostró que F6 era zombie ese mismo patrón. Verificar wiring synthesizer/orchestrator antes de scenarios.

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache` o refresh per turn.
- Kimi 400 "only 1 is allowed" vuelve → B8 thinking disable fue revertido, restaurar.
- Kimi 400 "only 0.6 is allowed" vuelve → temperature override clampeo perdido, verificar `_K2_REQUIRED_TEMPERATURE`.
- Kimi 400 "reasoning_content missing" vuelve → B8 thinking disable evade en algún callsite, grep `extra_body.*thinking` en BE.
- Container env stale (post `.env` edit) → `docker compose up -d --force-recreate api_dev`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2 + router boot check + Visionarias data check + sanity-check F7 source code wiring. Recién después tocás tools.
```
