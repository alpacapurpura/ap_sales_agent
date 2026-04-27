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

### D1.5 — Modelos en `observability/persistence/models/`, no `infrastructure/models/`
- **Contexto:** plan T1.3 dice "en `infrastructure/models/`" pero la estructura del módulo (T1.1) es flat (sin layer `infrastructure/`).
- **Opciones:** (A) Crear `observability/infrastructure/models/`, (B) co-locar bajo `persistence/models/`, (C) poner en `copilot/infrastructure/models/` (junto a los modelos legacy del copilot).
- **Elegida:** B. Razón: Principio 1 (cohesión) — todo lo de obs vive en `observability/`. La capa `persistence/` ya hospeda repositorios; los modelos son su artefacto natural. C contamina el módulo legacy.

### D1.6 — Generated columns con expresiones IMMUTABLE explícitas
- **Contexto:** Postgres rechaza `to_char(timestamp, ...)` y `started_at::date` en `GENERATED ALWAYS AS ... STORED` porque ambos dependen de TZ/locale (STABLE, no IMMUTABLE).
- **Opciones:** (A) Quitar `occurred_on` / `occurred_year_month` y derivarlos en queries, (B) Anclar a UTC con `AT TIME ZONE 'UTC'` y sintetizar año-mes con `EXTRACT + LPAD`, (C) Bumpear a Postgres 17+ (no opción).
- **Elegida:** B. Razón: el índice `(tenant_id, occurred_on)` es load-bearing para la MV de Fase 3 — no se puede diferir. La fórmula `EXTRACT + LPAD` es 100% IMMUTABLE y verificada en vivo.

### D1.7 — ETag normalisation en `litellm_sync` (no migration)
- **Contexto:** GitHub raw devuelve weak ETags `W/"<sha256-hex>"` ≈71 chars; columna es `varchar(64)`.
- **Opciones:** (A) Otra migración bumpeando a `varchar(128)`, (B) Strip `W/` + comillas + truncate a 64 en código.
- **Elegida:** B. Razón: el ETag es solo un fingerprint para `If-None-Match`; la pérdida de los últimos 7 chars no rompe la comparación de Phase 1. Migrar la columna agrega ruido al rollback de la atomic switch (Fase 2).

### D1.8 — Aggregator de turn_end flushea antes del SELECT
- **Contexto:** el callback handler hace `session.add(row)` por cada LLM call durante el turn; al cerrar `observe_turn`, el aggregator corre `SELECT SUM(...)` sobre `copilot_llm_call` y ve `0` rows porque `autoflush=False`.
- **Opciones:** (A) Tener el handler flushear cada vez (overhead), (B) Que el aggregator flushee una sola vez antes del SELECT.
- **Elegida:** B. Razón: una sola flush al final del turn vs N flushes (uno por LLM call). Mantiene la lógica del handler "best-effort, no toques transactions" y centraliza la garantía en un solo punto.

---

## Sorpresas / atajos descubiertos

- LangGraph `astream_events(version="v2")` y `BaseCallbackHandler` coexisten: el primero emite eventos en el stream, el segundo recibe callbacks via `RunnableConfig`. Ambos ven los mismos eventos LLM/tool/chain. Elegimos callback handler para Fase 1 porque tiene API estable y cero acoplamiento al loop de stream del orchestrator.
- `usage_metadata.input_token_details.cache_read` es la clave normalizada por LangChain (mismo nombre para OpenAI prefix-cache + Anthropic prompt cache). Reproducimos esa lectura en `cost/calculator.py`.
- `EventBus.publish(event, session=db)` defiere dispatch a `after_commit`. Para events de copilot domain (Fase 2) probablemente queramos session=None (dispatch inmediato) porque copilot no tiene transacción "principal" en el stream.
- **GitHub raw devuelve weak ETags** (`W/"<sha>"`), no fuertes. El bandwidth ahorro vía `If-None-Match` requiere preservar el `W/` exactly… pero como `varchar(64)` lo trunca, perdemos la opción (sin bumpear schema). En la práctica GitHub raw es CDN-cached así que no es un problema real, solo un detalle.
- **Frankfurter es ECB-backed pero no lista PEN/COP** — supuesto que tenía cobertura LATAM completa fue incorrecto. Bug encontrado durante research, no en producción. Mitigado con flag `fx_unsupported`.
- **`to_char` en Postgres es STABLE, no IMMUTABLE.** Asumí que era IMMUTABLE porque "es una función pura sobre timestamps". Resulta que depende de `lc_messages` y `lc_time` configurables, así que Postgres no lo deja en una stored generated column. Solución vía `EXTRACT + LPAD` quedó en migración.
- **El sync de LiteLLM produce ~22 false-positive updates por corrida** (~1% de 1972 rows) por rounding de `NUMERIC(14,12)` sobre tasas con 13+ decimales. Aceptado como deferred-debt (no afecta cálculo de costo per-call, solo el conteo de "row updated").
- **Existing autouse fixture `_isolate_trace_recorder_db` en `tests/conftest.py:115` va a romper en Fase 2** cuando borremos `trace_recorder.py`. Plan listado en `deferred-debt.md`.

---

## Cambios al schema durante ejecución

- **`occurred_year_month` definición.** Plan + ARCHITECTURE.md §4.2 usaban `to_char(started_at, 'YYYY-MM')`. Postgres rechaza por no ser IMMUTABLE. Reemplazado por `EXTRACT(YEAR FROM ... AT TIME ZONE 'UTC')::INT::TEXT || '-' || LPAD(EXTRACT(MONTH FROM ... AT TIME ZONE 'UTC')::INT::TEXT, 2, '0')`. Ítem en `deferred-debt.md` para reflejar el cambio en el ARCHITECTURE.md.
- **`occurred_on` definición.** Plan usaba `started_at::date`. Igual problema (depende de TZ). Reemplazado por `(started_at AT TIME ZONE 'UTC')::date`.

---

## Cambios al callback handler durante ejecución

- **Hook name correction (no behaviour change).** Plan usaba `on_chat_model_end`; la API real de `BaseCallbackHandler` solo expone `on_llm_end` (que dispara para chat y no-chat). Refleja en `learnings.md` D1.2 + `deferred-debt.md` para actualizar ARCHITECTURE.md.
- **Default `tenant_currency="USD"`** terminó en 3 archivos (`fx_resolver`, `callback_handler`, `turn_envelope`). Allowlist actualizado en `tests/architecture/test_master_data.py` con justificación documentada (mismo rol que `iam/domain/tenant.py`).

---

## Tests que costaron más de lo esperado

- **`test_e2e_isolated.py`** — el aggregator de `turn_end` veía 0 rows porque las llamadas del callback handler usan `session.add` sin `flush`. Fix simple (flush antes del SELECT) pero sólo se descubrió en e2e — ningún test unitario lo cubría. Aprendizaje: las decisiones sobre flush/commit en repos best-effort necesitan al menos un test de integración que las ejercite con datos reales.
- **`test_pricing_resolver.py::test_cache_skips_repo_on_second_call`** — `MagicMock` auto-crea atributos que rompen comparaciones `<` con `datetime`. Corregido inicializando `valid_from` explícitamente en el helper de mocks.
- **`test_litellm_sync.py`** — el smoke contra GitHub real reveló dos issues: ETag truncation + 22 false-positive updates por NUMERIC precision. Ambos resueltos / documentados.

---

## Items para `.claude/rules/` (si aplica)

Ninguno crítico. Posibles candidatos para evaluar al cerrar Fase 3:

- Patrón "factory de session por handler" para subscribers del EventBus (`repo_factory: Callable[[], Repo]`) — útil para cualquier módulo nuevo que escuche eventos cross-module.
- Patrón "best-effort observability" — ya existe en `.claude/rules/copilot-resilience.md` §"Debug copilot". Considerar agregar el contrato del callback handler (cero exceptions propagadas, structlog warning per hook).

---

## Métrica final fase

- **Commits creados:**
  - `eab7b2cd` chore(copilot-obs): scaffold observability module structure (T1.1)
  - `48e05755` feat(copilot-obs): add llm_call + pricing_snapshot + billing_config tables (T1.2)
  - `08527be5` feat(copilot-obs): add SQLAlchemy models for new tables (T1.3)
  - `01572adc` feat(copilot-obs): add repositories with tenant isolation (T1.4)
  - `e8ca123a` feat(copilot-obs): add pricing resolver + LiteLLM sync worker (T1.5)
  - `f36feea0` feat(copilot-obs): add cost calculator + FX resolver (T1.6)
  - `637ef26e` feat(copilot-obs): add LangChain callback handler (not wired) (T1.7)
  - `323bc740` feat(copilot-obs): add turn envelope context manager (T1.8)
  - `ea89109e` feat(copilot-obs): add domain event subscribers (not registered) (T1.9)
  - `28cfde11` test(copilot-obs): add isolated e2e test for new module (T1.10)
  - + commit final docs (T1.13).
- **Diff total:** 42 files changed, 4365 insertions(+), 45 deletions(-).
- **Tests añadidos:** 64 tests nuevos en `tests/modules/copilot/observability/` (todos verdes), 0 tests existentes quebrados, 13 tests de schema sobre la migración.
- **Coverage backend:** 67.48% (gate ≥43% holgado; antes ~67%, sin regresión).
- **Quality gates:** ruff lint + format clean; 575 arch tests verdes; full pytest 5276 passed / 7 skipped / 11 deselected (2 deselected son pre-existing flakes documentados, 9 son los `verify`/`integration` markers).
- **Hot-path intacto:** `git diff eab7b2cd^ HEAD -- backend/src/modules/copilot/application/orchestrator/{chat,deep_agent,graph}.py backend/src/modules/copilot/application/observability/trace_recorder.py backend/src/modules/copilot/application/orchestrator/usage_tracking.py` → vacío. Smoke `curl /health` 200 OK. `grep -r ObservabilityCallbackHandler|ObservabilityContext|register_subscribers backend/src/modules/copilot/application/` → 0 matches.
- **Pricing populated:** 1972 active rows en `model_pricing_snapshot` (openai 96 / anthropic-via-bedrock / azure 124 / fireworks_ai 244 / xai 36 / gemini 41 / etc.). Worker registrado cron 03:00 UTC.
- **Tiempo real ejecución:** ~3 horas wall-clock para las 13 tasks (research + scaffold + 3 tablas + ORMs + 4 repos + pricing + cost/FX + callback + envelope + subscribers + e2e + verificaciones + close).
