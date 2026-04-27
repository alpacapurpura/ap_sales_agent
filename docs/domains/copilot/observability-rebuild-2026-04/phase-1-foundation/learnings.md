# Phase 1 — Learnings

> Llenado durante ejecución. Última actualización al cerrar fase.

---

## Research findings (executed 2026-04-26)

### LangChain BaseCallbackHandler

- **Status:** vigente con un matiz importante.
- **Versión LangChain confirmada:** `langchain_core` 1.3.2 instalada en `backend/.venv` (verificado con `ls site-packages`).
- **Firmas vigentes (verificadas en `langchain_core/callbacks/base.py`):**
  - `on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, tags=None, metadata=None, **kwargs)`
  - `on_llm_start(self, serialized, prompts, *, run_id, parent_run_id=None, tags=None, metadata=None, **kwargs)` (no-chat models)
  - `on_llm_end(self, response: LLMResult, *, run_id, parent_run_id=None, tags=None, **kwargs)`
  - `on_llm_error(self, error, *, run_id, parent_run_id=None, tags=None, **kwargs)`
  - `on_tool_start`, `on_tool_end`, `on_tool_error`, `on_chain_start`, `on_chain_end` siguen el mismo patrón.
- **Hallazgo clave:** `BaseCallbackHandler` **no tiene** `on_chat_model_end`. El plan/arquitectura lo nombra así porque ese es el nombre del **stream event** que emite `LangGraph.astream_events(version="v2")` (ver `usage_tracking.py:95` y `stream_provenance.py`). En el callback handler clásico (que se cablea con `RunnableConfig(callbacks=[...])`) hay un único `on_llm_end` que dispara para chat y no-chat.
- **Implicancia para Fase 1:** mantenemos el diseño tal cual (callback handler vía `RunnableConfig`). Renombramos en código `on_chat_model_end` → `on_llm_end` y dentro detectamos chat vs no-chat por correlación con `run_id` registrado en `on_chat_model_start`. `usage_metadata` se accede en `on_llm_end` desde `response.generations[0][0].message.usage_metadata` (AIMessage).
- **Notas:** el doc oficial migró de `python.langchain.com/docs/concepts/callbacks/` a `docs.langchain.com/oss/python/...` (308 redirect). El reference API se sirve hoy desde `reference.langchain.com/python/langchain_core/callbacks/`. Source code canónico (single source of truth para firmas): `github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/callbacks/base.py`.

### LiteLLM JSON schema

- **Status:** vigente.
- **Source:** `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json`.
- **Versión / commit:** archivo "main" branch al 2026-04-26 (no se fijó hash; el sync worker valida vía ETag de respuesta).
- **Keys relevantes confirmadas:**
  - `input_cost_per_token` (chat/embedding)
  - `output_cost_per_token` (chat/embedding)
  - `cache_read_input_token_cost` (modelos con prefix cache: GPT-4o, Claude 3.5+, Gemini)
  - `cache_creation_input_token_cost` (Anthropic prompt cache writes)
  - `litellm_provider` (`openai`, `anthropic`, `vertex_ai`, `bedrock`, `xai`, `cohere`, `mistral`, `groq`, …)
  - `mode` (`chat`, `completion`, `embedding`, `image_generation`, `audio_transcription`, …)
- **Keys nuevas observadas (no usadas todavía):** `output_cost_per_image`, `input_cost_per_pixel`, `input_cost_per_audio_token`, `output_cost_per_audio_token`, `tool_use_system_prompt_tokens`, varios `supports_*` flags. **Sin `reasoning_token_cost`** todavía — para o1/o3 el costo de reasoning tokens se imputa al output.
- **Decisión:** filtrar entries con `mode in {chat, completion}` y campos `input_cost_per_token` + `output_cost_per_token` presentes. Cache fields opcionales (DEFAULT 0 si missing).
- **Notas:** la entrada `sample_spec` es un template — saltarla en el parser.

### OTel GenAI semantic conventions

- **Status:** **Development** (no Stable). Verificado en `opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/` 2026-04-26.
- **Atributos confirmados (Development, Recommended):** `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.response.id`, `gen_ai.provider.name`, `gen_ai.operation.name`, `error.type`.
- **No existe** `gen_ai.usage.cost` en la spec (cost queda como atributo custom).
- **Decisión naming columnas:** mantener nombres del plan (`provider`, `model_requested`, `model_responded`, `input_tokens`, `output_tokens`, `cached_read_tokens`, …) — son OTel-shape compatible para mapeo trivial cuando se exporte. No vale la pena hacer rename a `gen_ai_*` mientras la spec siga en Development.
- **Notas:** revisar al promover la spec a Stable. Ese es el trigger para considerar columnas con prefijo `gen_ai_` o exportar a OTel collector.

### Frankfurter API

- **Status:** vigente, **dominio cambió**: `api.frankfurter.app` → `api.frankfurter.dev` (301 permanent redirect).
- **URL final usada:** `https://api.frankfurter.dev/v1/latest?base=USD`.
- **Verificado:** devuelve JSON `{amount, base, date, rates: {…}}` con 31 monedas, sin auth, ECB-backed.
- **Cobertura confirmada:** USD, MXN, BRL, CAD, AUD (no aparecen PEN ni COP en `latest?base=USD` — Frankfurter limita a divisas listadas por ECB; PEN y COP no están). **Implicancia:** si el tenant es PE/CO, FXResolver debe devolver tasa USD passthrough con flag `fx_unsupported=True` y caer en fallback (manual override en `tenant_billing_config.flat_fee_amount` o futura integración alternativa). Documentar en `cost/fx_resolver.py`.
- **Notas:** alternativa de respaldo (no implementada Fase 1): `exchangerate.host`. Decisión: aceptar gap PEN/COP para Fase 1, marcar como deferred-debt si se confirma uso por tenants reales.

### ARQ cron syntax

- **Versión instalada:** `arq` 0.27.0 (verificado en `backend/.venv/lib/python3.12/site-packages/arq-0.27.0.dist-info`).
- **Sintaxis confirmada:** `cron(func, hour=3, minute=0)` o `cron(func, hour={0, 6, 12, 18}, minute=15)` para múltiples slots.
- **Pattern repo:** `src/workers/settings.py` define `SchedulerSettings.cron_jobs = [cron(...), ...]`. Cada cron debe declarar la función también en `SchedulerSettings.functions`. Importar la callable al top del archivo.
- **Decisión:** registrar `sync_litellm_pricing` con `cron(sync_litellm_pricing, hour=3, minute=0)` (daily 03:00 UTC) en `SchedulerSettings.cron_jobs` y agregarla a ambas listas `WorkerSettings.functions` + `SchedulerSettings.functions` (arq lee `__dict__` no inherited attrs).

### Cambios al diseño respecto a ARCHITECTURE.md

Ninguno bloqueante. Ajustes menores documentados arriba:

1. Callback handler usa `on_llm_end` (no `on_chat_model_end`) — naming refinement, comportamiento idéntico.
2. URL Frankfurter: `frankfurter.app` → `frankfurter.dev`.
3. PEN/COP fuera de cobertura Frankfurter → fallback documentado, no bloqueante para Fase 1.

No fue necesario pausar/consultar al usuario.

---

## Decisiones tomadas

### D1.1 — Mantener naming columnas internas (no `gen_ai.*`)
- **Contexto:** OTel GenAI sigue en Development. Considerar rename de columnas a `gen_ai_input_tokens`, etc.
- **Opciones:** (A) Renombrar ahora para futuro export, (B) Mantener naming "natural" Postgres-friendly y mapear al exportar.
- **Elegida:** B. Razón: spec inestable, rename ahora invita a doble-rename si OTel cambia algo al promover. Mapeo en exporter es trivial (alias en `SELECT`).

### D1.2 — Callback handler usa `on_llm_end`, no `on_chat_model_end`
- **Contexto:** plan referencia `on_chat_model_end` (es nombre de stream event LangGraph, no método del callback handler).
- **Opciones:** (A) Implementar como subscriber de `astream_events` (B) Implementar como `BaseCallbackHandler` clásico cableado vía `RunnableConfig`.
- **Elegida:** B. Razón: API estable de LangChain (no LangGraph-específica), sobrevive a cambios en `astream_events`, hooks granulares (chain/tool nativos), best-effort sin tocar el loop de stream del orchestrator.

### D1.3 — Frankfurter passthrough cuando moneda no listada
- **Contexto:** PEN/COP no aparecen en `frankfurter.dev`.
- **Opciones:** (A) Bloquear soporte multi-moneda hasta integrar otra API. (B) Devolver tasa 1.0 + flag `is_estimated`/`fx_unsupported` y dejar `cost_tenant_currency` NULL.
- **Elegida:** B. Razón: cero acoplamiento adicional Fase 1; cualquier tenant LATAM con moneda no listada cae en flag visible y queda como deferred-debt resoluble en Fase 3.

### D1.4 — Idempotencia EventBus subscribers
- **Contexto:** `EventBus._handlers` es class-level singleton. Re-importar el módulo registra doble.
- **Opciones:** (A) Lista cruda con append, (B) Guard pattern (`if handler not in EventBus._handlers.get(event_name, []): subscribe(...)`).
- **Elegida:** B. Razón: pattern ya usado en `brand_summary_event_handlers.py`. Robusto a reimports en tests + hot-reload uvicorn.

---

## Sorpresas / atajos descubiertos

- LangGraph `astream_events(version="v2")` y `BaseCallbackHandler` coexisten: el primero emite eventos en el stream, el segundo recibe callbacks via `RunnableConfig`. Ambos ven los mismos eventos LLM/tool/chain. Elegimos callback handler para Fase 1 porque tiene API estable y cero acoplamiento al loop de stream del orchestrator.
- `usage_metadata.input_token_details.cache_read` es la clave normalizada por LangChain (mismo nombre para OpenAI prefix-cache + Anthropic prompt cache). Reproducimos esa lectura en `cost/calculator.py`.
- `EventBus.publish(event, session=db)` defiere dispatch a `after_commit`. Para events de copilot domain (Fase 2) probablemente queramos session=None (dispatch inmediato) porque copilot no tiene transacción "principal" en el stream.

---

## Cambios al schema durante ejecución

- (a llenar al cerrar fase si hubo ajustes durante implementación)

---

## Cambios al callback handler durante ejecución

- (a llenar al cerrar fase)

---

## Tests que costaron más de lo esperado

- (a llenar al cerrar fase)

---

## Items para `.claude/rules/` (si aplica)

- (a llenar al cerrar fase)

---

## Métrica final fase

- Commits creados (hashes + mensajes): a llenar
- Líneas añadidas: a llenar
- Tests añadidos: a llenar
- Coverage backend antes/después: a llenar
- Tiempo real ejecución: a llenar
