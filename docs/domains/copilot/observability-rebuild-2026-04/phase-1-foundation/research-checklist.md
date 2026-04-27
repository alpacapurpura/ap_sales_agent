# Phase 1 — Research Checklist (ejecutar ANTES de tocar código)

**Objetivo:** confirmar que el diseño en `ARCHITECTURE.md` sigue siendo SOTA al momento de ejecución. Si encontrás un cambio mayor, **pausá y consultá** antes de proceder.

**Tiempo estimado:** 30-45 min.

**Tools:** WebSearch, WebFetch (sin necesidad de Context7 para esta fase).

---

## 1. LangChain `BaseCallbackHandler` API estable

**Por qué importa:** `recording/callback_handler.py` depende de hooks LangChain. Si cambiaron firmas o agregaron hooks relevantes, hay que ajustar.

**Verificar:**
- WebFetch → https://python.langchain.com/docs/concepts/callbacks/
- WebFetch → https://api.python.langchain.com/en/latest/callbacks/langchain_core.callbacks.base.BaseCallbackHandler.html
- WebSearch → "langchain BaseCallbackHandler 2026 on_chat_model_end usage_metadata"
- Confirmar:
  - Hooks `on_chat_model_start`, `on_chat_model_end`, `on_tool_start`, `on_tool_end`, `on_chain_start`, `on_chain_end`, `on_llm_error`, `on_tool_error` siguen vigentes.
  - `usage_metadata` sigue siendo el contenedor canónico (no cambió a otro nombre).
  - `response_metadata.model_name` sigue siendo el campo para resolver model real (vs. solicitado).
  - `input_token_details.cache_read` sigue siendo el campo de cached tokens (Anthropic + OpenAI normalizados).

**Si difiere:** anotar en `learnings.md` el campo correcto y ajustar `callback_handler.py` y tests sintéticos.

---

## 2. LiteLLM pricing JSON schema

**Por qué importa:** `pricing/litellm_sync.py` parsea ese JSON. Cambios en estructura rompen el sync.

**Verificar:**
- WebFetch → https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json (puede ser grande — leer las primeras 200 líneas suele bastar para schema).
- WebSearch → "litellm model_prices_and_context_window.json schema 2026"
- Confirmar entries tienen al menos:
  - `input_cost_per_token`
  - `output_cost_per_token`
  - `cache_read_input_token_cost` (Anthropic / OpenAI prompt cache)
  - `cache_creation_input_token_cost`
  - `litellm_provider`
  - `mode` (chat / completion / embedding)

**Si schema cambió:** ajustar `pricing/litellm_sync.py` parser. Si keys nuevas relevantes (ej. `reasoning_token_cost`) → considerar si agregar al schema.

---

## 3. OpenTelemetry GenAI semantic conventions — status

**Por qué importa:** decisión de naming en `copilot_llm_call`. Si OTel promovió attrs a Stable, conviene alinear nombres.

**Verificar:**
- WebFetch → https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/
- WebFetch → https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
- WebSearch → "opentelemetry gen_ai semantic conventions stable 2026"
- Confirmar:
  - Attrs siguen en Development o ya promovidos a Stable.
  - Si Stable: revisar nombres exactos (`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, etc.) y si conviene renombrar columnas en migración (mejor antes que después).
  - Si nuevo attr `gen_ai.usage.cost` apareció: evaluar adoptar.

**Si Stable:** anotar en `learnings.md` y considerar rename de columnas (decision al usuario).

---

## 4. Frankfurter API (FX rates)

**Por qué importa:** `cost/fx_resolver.py` usa este source. Si baja, hay que cambiar a alternativa.

**Verificar:**
- WebFetch → https://www.frankfurter.app/
- WebFetch → https://api.frankfurter.app/latest?base=USD (verificar que devuelve JSON con `rates`).
- Confirmar:
  - API gratuita, sin auth.
  - Rates ECB-backed, daily.
  - Cobertura de PEN, MXN, COP, USD.

**Si discontinuado:** alternativas (en orden de preferencia): `exchangerate.host`, `openexchangerates.org` (free tier). Anotar y ajustar.

---

## 5. ARQ (Async Redis Queue) cron syntax

**Por qué importa:** `pricing_sync_task.py` es ARQ task con cron. Verificar sintaxis vigente.

**Verificar:**
- WebFetch → https://arq-docs.helpmanual.io/ (cron section)
- WebSearch → "arq python cron schedule 2026"
- Confirmar `cron(hour={3}, minute={0})` o equivalente.
- Verificar registro en `backend/src/workers/settings.py` — leer el archivo actual para imitar pattern existente.

**Si difiere:** ajustar invocación y registro.

---

## 6. Verificar archivos del repo a tocar

Lectura rápida (no investigación externa, pero indispensable antes de Fase 1):

- `backend/alembic/versions/059_copilot_trace_event.py` — patrón de migración a imitar.
- `backend/src/modules/copilot/infrastructure/models/trace_event_model.py` — naming convention modelos.
- `backend/src/modules/copilot/application/observability/trace_recorder.py` — pattern best-effort + SessionLocal local que **se mantiene** en `event_store.py` nuevo.
- `backend/src/workers/settings.py` — pattern para registrar cron jobs ARQ.
- `backend/src/modules/copilot/application/orchestrator/usage_tracking.py` — entender cómo se calcula costo HOY (para reproducir lógica equivalente en `cost/calculator.py`).
- `backend/tests/modules/copilot/test_trace_recorder.py` — pattern de tests con `set_session_factory` (clave para no bloquear en DNS Postgres en tests).

---

## 7. Verificar fecha actual

```bash
date
```

Confirmar que estás en abril/mayo 2026 (o más reciente). Si es 2027+: revisar si hubo cambios mayores en LangChain/LangGraph (ej. v2.x a v3.x) — entonces ampliar research a release notes.

---

## Output del research

Antes de empezar T1.1 del plan, agregar al inicio de `learnings.md` un bloque:

```markdown
## Research findings (executed YYYY-MM-DD)

### LangChain BaseCallbackHandler
- Status: [vigente / cambió]
- Notas: ...

### LiteLLM JSON schema
- Status: [vigente / cambió]
- Versión / commit hash visto: ...
- Notas: ...

### OTel GenAI semantic conventions
- Status: [Development / Stable]
- Decisión naming: ...

### Frankfurter API
- Status: [vigente / alternativa elegida X]

### ARQ cron syntax
- Sintaxis confirmada: ...

### Cambios al diseño respecto a ARCHITECTURE.md
- (vacío si nada cambió)
- ...
```

Si "Cambios al diseño" tiene items → **pausá y consultá al usuario** antes de proceder con T1.1.
