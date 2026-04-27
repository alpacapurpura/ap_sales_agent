# Phase 1 — Foundation

**Objetivo:** crear el módulo nuevo, las tablas, el worker de pricing y los repositorios. **NO conectar al hot path del copilot.** Sistema corre idéntico desde fuera.

**Riesgo al copilot:** cero (nada del código nuevo se invoca durante los turns).

**Duración estimada:** 1-2 días.

**Pre-condición:** completar `research-checklist.md` antes de tocar código.

---

## Tasks

> Ejecutar en orden. Cada task tiene criterios de aceptación verificables.

### T1.1 — Crear estructura de carpetas

**Acción:**
```
backend/src/modules/copilot/observability/
  __init__.py
  recording/
    __init__.py
    callback_handler.py        (esqueleto — completo en T1.5)
    domain_subscribers.py       (esqueleto — completo en T1.6)
    turn_envelope.py            (esqueleto)
    sanitization.py
    event_store.py
  pricing/
    __init__.py
    resolver.py
    litellm_sync.py
  cost/
    __init__.py
    calculator.py
    fx_resolver.py
  persistence/
    __init__.py
    llm_call_repository.py
    trace_event_repository.py
    pricing_snapshot_repository.py
    tenant_billing_config_repository.py
  reporting/
    __init__.py
    billing_cycle_service.py
    cost_aggregator.py
  workers/
    __init__.py
    pricing_sync_task.py
    aggregate_refresh_task.py    (esqueleto, completo en Fase 3)
    retention_task.py            (esqueleto, completo en Fase 3)
  api/
    __init__.py
    routes_billing.py            (esqueleto, completo en Fase 3)
```

**Criterio aceptación:**
- Estructura existe.
- `pytest tests/architecture/test_folder_naming.py -x -q` pasa (snake_case).
- `pytest tests/architecture/test_ddd_boundaries.py -x -q` pasa (no nuevos cross-module imports).

---

### T1.2 — Migración Alembic con 3 tablas nuevas

**Acción:** crear migración `0XX_copilot_observability_rebuild.py` (X = siguiente número en `backend/alembic/versions/`).

Schema completo en `ARCHITECTURE.md` §4.2. Idempotente raw SQL.

**Tests primero:**
- `tests/modules/copilot/observability/test_migration_schema.py`:
  - Verifica `copilot_llm_call` existe + columnas + tipos.
  - Verifica índices `ix_llm_call_tenant_day`, `ix_llm_call_turn`, `ix_llm_call_tenant_model_day`, `ix_llm_call_errors`.
  - Verifica `model_pricing_snapshot` existe + unique partial index `ix_pricing_active`.
  - Verifica `tenant_billing_config` existe + PK.

**Criterio aceptación:**
- `docker exec -t visionarias_brain_dev bash -c 'cd /app && alembic upgrade head'` corre sin error.
- Down → up → idempotente.
- Re-run `alembic upgrade head` no falla.
- Test schema verde.

---

### T1.3 — SQLAlchemy models

**Acción:** en `infrastructure/models/`:
- `llm_call_model.py` → `CopilotLlmCallModel`
- `pricing_snapshot_model.py` → `ModelPricingSnapshotModel`
- `tenant_billing_config_model.py` → `TenantBillingConfigModel`

Naming convention: `{Name}Model`, `__tablename__` exacto al SQL.

**Tests primero:** `tests/modules/copilot/observability/test_models.py` — instancia + commit + read-back.

**Criterio aceptación:**
- Tests verdes.
- `pytest tests/architecture/test_domain_purity.py` pasa (modelos en `infrastructure/`, no `domain/`).

---

### T1.4 — Repositorios

**Acción:** en `observability/persistence/`:
- `LlmCallRepository`: `add(...)`, `find_by_turn(turn_id)`, `find_by_tenant_range(tenant_id, start, end)`, `count_errors_today(tenant_id)`.
- `PricingSnapshotRepository`: `find_active(provider, model)`, `find_at(provider, model, ts)`, `close_active(provider, model)`, `add(...)`.
- `TenantBillingConfigRepository`: `get(tenant_id)`, `upsert(...)`.
- `TraceEventRepository`: limpia interfaz para escribir `copilot_trace_event` (absorbe rol del actual `trace_recorder`).

**Tests primero:** `tests/modules/copilot/observability/test_repositories.py` — happy path + tenant isolation (query filtra tenant_id).

**Criterio aceptación:**
- Tests verdes.
- Todas queries filtran `tenant_id` donde aplica (excepto pricing snapshot — global).

---

### T1.5 — Pricing resolver + LiteLLM sync worker

**Acción:**
- `pricing/resolver.py` → `PricingResolver.resolve(provider, model, at_ts) -> PricingSnapshot`. Cache LRU 5min keyed por `(provider, model)`. Si miss, query repo `find_at(provider, model, at_ts)`. Si no existe → fallback con flag `is_estimated=True`.
- `pricing/litellm_sync.py` → función `sync_pricing(session, http_client) -> SyncResult`. Fetcha `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json` (etag check), parsea entries con `litellm_provider in {openai, anthropic, vertex_ai, google, xai, ...}`, diff vs snapshots vigentes, cierra (set `valid_to=NOW()`) las cambiadas e inserta nuevas con `valid_from=NOW()`.
- `workers/pricing_sync_task.py` → ARQ task `sync_litellm_pricing` (cron daily 03:00 UTC). Registrar en `backend/src/workers/settings.py`.

**Tests primero:**
- `test_pricing_resolver.py` — resolve con cache hit, miss, fallback, point-in-time (call viejo usa snapshot viejo).
- `test_litellm_sync.py` — mock httpx response, verificar diff (insert nuevos, close viejos), idempotencia.

**Criterio aceptación:**
- Tests verdes.
- Manual smoke: `cd backend && .venv/bin/python -c "from src.modules.copilot.observability.pricing.litellm_sync import sync_pricing; ..."` o invocar el ARQ task local — verifica que tabla `model_pricing_snapshot` se llena con ≥50 modelos (gpt-4o, gpt-4o-mini, claude-3-5-sonnet, gemini-1.5-pro, etc.).

---

### T1.6 — Cost calculator + FX resolver

**Acción:**
- `cost/calculator.py` → `calculate_cost(input_tokens, output_tokens, cached_read_tokens, cached_write_tokens, pricing: PricingSnapshot) -> Decimal`. Devuelve `Decimal` para precisión, no float.
- `cost/fx_resolver.py` → `FXResolver.resolve(currency_code, at_ts) -> Decimal`. Cache diaria. Source: `frankfurter.app` (free, ECB-backed). Fallback `1.0` si `currency_code='USD'`.

**Tests primero:**
- `test_cost_calculator.py` — happy path, cached tokens half-price, edge cases (zero tokens).
- `test_fx_resolver.py` — USD passthrough, cached fetch, fallback en error de red.

**Criterio aceptación:**
- Tests verdes.
- Cálculos coinciden con tabla pricing actual de OpenAI (verificar con un cálculo manual).

---

### T1.7 — Callback handler (NO conectado al graph aún)

**Acción:** `recording/callback_handler.py` → `ObservabilityCallbackHandler(BaseCallbackHandler)`.

Hooks:
- `on_chat_model_start(serialized, messages, run_id, parent_run_id, **kwargs)` → guarda `started_at`, `provider`, `model_requested`, `run_id` en dict in-memory.
- `on_chat_model_end(response, run_id, **kwargs)` → extrae `usage_metadata`, `response_metadata.model_name`, calcula cost via `PricingResolver` + `CostCalculator` + `FXResolver`, persiste row en `copilot_llm_call` Y row en `copilot_trace_event` (event_type='llm_call').
- `on_tool_start(serialized, input_str, run_id, parent_run_id, **kwargs)` → in-memory open span.
- `on_tool_end(output, run_id, **kwargs)` → persiste `copilot_trace_event` (event_type='tool_call', con duration_ms).
- `on_chain_start(serialized, inputs, run_id, parent_run_id, **kwargs)` → si nombre es nodo LangGraph → `node_enter`.
- `on_chain_end(outputs, run_id, **kwargs)` → `node_exit`.
- `on_llm_error(error, run_id, **kwargs)` / `on_tool_error(error, run_id, **kwargs)` → `error` row.

Constructor: `ObservabilityCallbackHandler(tenant_id, conversation_id, user_id, turn_id, repos)`. Una instancia por turn.

**Tests primero:**
- `test_callback_handler.py` — invocar callbacks con payloads sintéticos (basados en docs LangChain April 2026), verificar:
  - `on_chat_model_end` escribe row en `copilot_llm_call` con tokens+cost correctos.
  - `on_tool_end` escribe row en `copilot_trace_event` con duration_ms.
  - Errores escriben row con `status='error'`.
  - Excepciones internas (DB caída) NO propagan al caller (best-effort).

**Criterio aceptación:**
- Tests verdes.
- Handler aún NO se invoca desde chat.py. Verificar con `grep -r "ObservabilityCallbackHandler" backend/src/modules/copilot/application/orchestrator/` → cero matches.

---

### T1.8 — Turn envelope

**Acción:** `recording/turn_envelope.py` → `ObservabilityContext`:
```python
@classmethod
def start(cls, *, tenant_id, conversation_id, user_id) -> "ObservabilityContext":
    ...
def langchain_config(self) -> RunnableConfig:
    """Returns config dict to pass to graph.astream_events(state, config=...)."""
    return {"callbacks": [self.callback_handler]}
def start_turn(self, *, message, route, attachments) -> None:
    """Persiste turn_start row."""
def end_turn(self, *, response_length, message_count, block_count, duration_ms) -> None:
    """Persiste turn_end row con totales agregados (calculados desde callback_handler)."""
async def __aenter__(self): ...
async def __aexit__(self, exc_type, exc, tb): ...
```

`__aenter__` llama `start_turn`. `__aexit__` llama `end_turn` con totales sumados de las rows `copilot_llm_call` del turn (o desde state interno del handler).

**Tests primero:** `test_turn_envelope.py` — start/end ciclo, agregación de costos, manejo de excepción.

**Criterio aceptación:**
- Tests verdes.
- API limpia: chat.py futuro solo necesita `obs = ObservabilityContext.start(...); async with obs.observe_turn(message=..., ...): graph.astream_events(state, config=obs.langchain_config())`.

---

### T1.9 — Domain subscribers (esqueleto)

**Acción:** `recording/domain_subscribers.py` → registra listeners para domain events (`CardEmitted`, `RoutingDecided`, `TurnStarted`, `TurnEnded`).

En Fase 1 los publishers aún no existen en copilot — solo el subscriber listo. `register_subscribers(event_bus)` es función exportada que se llamará desde el boot del módulo en Fase 2.

**Tests primero:** `test_domain_subscribers.py` — mock event_bus, publicar evento sintético, verificar persiste row.

**Criterio aceptación:**
- Tests verdes.
- `register_subscribers` exportado pero **NO invocado** todavía. Verificar `grep -r "register_subscribers" backend/src/` → solo en obs module + tests.

---

### T1.10 — Smoke E2E del módulo aislado

**Acción:** test integración:
- `tests/modules/copilot/observability/test_e2e_isolated.py`:
  - Instancia `ObservabilityContext`.
  - Mock `BaseChatModel` con `FakeListLLM` o equivalente.
  - Construye un mini-graph LangGraph de 2 nodos (sin invocar copilot real).
  - Ejecuta `graph.astream_events(state, config=obs.langchain_config())`.
  - Verifica:
    - 1 row turn_start
    - 1 row turn_end
    - ≥1 row llm_call con cost_usd > 0
    - ≥1 row trace_event con event_type='llm_call'

**Criterio aceptación:**
- Test verde.
- Demuestra el módulo funciona end-to-end **sin tocar copilot**.

---

### T1.11 — Verificar copilot intacto

**Acción:**
- `git diff backend/src/modules/copilot/application/orchestrator/chat.py` → vacío.
- `git diff backend/src/modules/copilot/application/orchestrator/deep_agent.py` → vacío.
- `git diff backend/src/modules/copilot/application/observability/trace_recorder.py` → vacío.
- `git diff backend/src/modules/copilot/application/orchestrator/usage_tracking.py` → vacío.
- Smoke manual del copilot: levantar dev, mandar un mensaje, verificar respuesta y verificar que `copilot_trace_event` sigue registrando con el mismo schema.

**Criterio aceptación:**
- Cero cambios en hot path.
- Copilot funciona idéntico.

---

### T1.12 — Quality gates

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q
```

**Criterio aceptación:** todo verde.

---

## Commits sugeridos (Conventional)

Stage por nombre (NUNCA `git add .`):

1. `chore(copilot-obs): scaffold observability module structure` (T1.1)
2. `feat(copilot-obs): add llm_call + pricing_snapshot + billing_config tables` (T1.2)
3. `feat(copilot-obs): add SQLAlchemy models for new tables` (T1.3)
4. `feat(copilot-obs): add repositories with tenant isolation` (T1.4)
5. `feat(copilot-obs): add pricing resolver + LiteLLM sync worker` (T1.5)
6. `feat(copilot-obs): add cost calculator + FX resolver` (T1.6)
7. `feat(copilot-obs): add LangChain callback handler (not wired)` (T1.7)
8. `feat(copilot-obs): add turn envelope context manager` (T1.8)
9. `feat(copilot-obs): add domain event subscribers (not registered)` (T1.9)
10. `test(copilot-obs): add isolated e2e test for new module` (T1.10)
11. `docs(copilot-obs): close phase 1 — fill learnings + deferred-debt` (T1.13)

---

### T1.13 — Cerrar fase

1. Llenar `learnings.md` con decisiones, cambios al diseño, sorpresas.
2. Llenar `deferred-debt.md` con lo que NO se completó (con razón).
3. Verificar `completion-checklist.md` (cada item evidenciado).
4. Commit final docs.
5. Devolver al usuario el prompt de `handoff-prompts/start-phase-2.md`.
