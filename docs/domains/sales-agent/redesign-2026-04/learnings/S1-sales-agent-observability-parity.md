# Learnings · S1 · sales-agent observability parity + PII LATAM + tool_call_dedup

> Doc para S2. Foundation event-sourced lista para cost guardrails cross-agent.

---

## Resumen (3 líneas)

- **Entregado**: tablas `sales_agent_llm_call` / `sales_agent_trace_event` / `sales_agent_routing_log` (migración 078 idempotente, validada en clone DB). `SalesAgentCallbackHandler` heredando `BaseAgentCallbackHandler` shared (Template Method) con cost+pricing+FX vía shared resolvers (Kimi K2.6/K2.5 alias). PII LATAM en `shared/agent_observability/recording/sanitization.py` (DNI/CURP/CUIT/RFC/CC/RUC/CPF/CVV/tarjeta) con keyword guards. Mirror `tool_call_dedup.py` env-prefix `SALES_AGENT_*` wired en `node_tool_executor`. Subgraph callback forwarding (`sales_agent_node(state, config)`). 4 domain events (`LeadQualified` / `ObjectionHandled` / `StageTransitioned` / `ToolLoopDetected`) con subscribers best-effort. Reconciliation worker opt-in `SALES_AGENT_DUAL_WRITE_RECONCILE=1`. `sales_audit.py` dual-read activo (sidebar + timeline) + `clear_user_history` extended.
- **Decisión no obvia**: el callback handler **no** hereda los 6 LangChain callbacks del base (Template Method incompleto); duplica la plumbing copilot bajo S1 para no tocar copilot en el mismo sprint. Lift al base = DEFERRED-post-S6 cuando copilot retrofitee. Documentado como tech-debt con pattern de fix.
- **Listo para S2**: 5510 tests verdes, ruff/format clean, migration apply idempotente en dev DB, `model_pricing_snapshot` + `tenant_billing_config` ya cross-agent (post-S0), reconciliation worker registered en `WorkerSettings.functions` + `SchedulerSettings.cron_jobs` (cron @ minute=25, off por env-flag).

---

## Decisiones clave

- **Callback handler activo en orchestrator, no en LLMFactory**:
  - Tomada: `chat.py:868` cambia a `agent_app.ainvoke(state, config={"callbacks":[handler]})`. **No** se toca `LLMFactory.generate_response` ni cada `@trace_node`. Subgraph forwarding via `sales_agent_node(state, config)` reenvía a `sales_app.invoke(state, config=config)`.
  - Razón: `LLMFactory` es un singleton cross-agent; agregar callbacks ahí acopla copilot. Pasar `config` al ainvoke es el pattern documentado de LangGraph y propaga a todos los `on_chat_model_*` / `on_tool_*` / `on_chain_*` automáticamente.
  - Trade-off: legacy `LLMLog` writer sigue activo en `providers/openai.py:168` durante dual-write window. **No** se tocan las 9 sites de `LLMFactory.get_service()` en sales_agent. Cleaner, scope estricto.

- **PII keyword-guarded por bare-digit IDs**:
  - Tomada: DNI / CC / RUC / CPF bare-digit requieren keyword `(dni|documento|cédula|cc|cuit|cuil|ruc|cpf|nit)`. CURP / RFC / CPF formatted / CUIT-dash sin keyword.
  - Razón: bare 7-11 dígitos sin keyword = false-positive trivial sobre order_ids, external_references, scores, timestamps. CURP 18-char + letras es estructuralmente única; no necesita keyword. El research mandate confirmó que LATAM compliance (LGPD BR, LFPDPPP MX, PDPA) acepta keyword-anchored.
  - Trade-off: lead que dice "12345678 mi cliente" sin keyword **no** se redacta. Aceptable: tu propio agente sales debe resguardar identidad explícita; el agente humano no debería loguear así.

- **Subgraph forwarding via signature change**:
  - Tomada: `sales_agent_node(state)` → `sales_agent_node(state, config: RunnableConfig)`. Forward `sales_app.invoke(state, config=config)`.
  - Razón: research confirmó (deepwiki LangGraph) que un compiled subgraph invocado como `add_node` es **opaque** — el callback handler parent no llega a los nodos internos sin reenviar config. Sin esto, los 7 nodos de sales_app (qualifier, closer, etc.) no aparecen en `node_enter`/`node_exit` rows.
  - Trade-off: el `@trace_node` legacy sigue agregando AgentTrace rows desde dentro del subgraph — eso queda, dual-write esperado.

- **Repo Protocols `@runtime_checkable`**:
  - Tomada: `BaseLLMCallRepoProtocol` y `BaseTraceEventRepoProtocol` decorados con `@runtime_checkable` en shared.
  - Razón: tests de subclase quieren `isinstance(repo, BaseLLMCallRepoProtocol)`. Sin el decorator falla `TypeError`. Es additive, sin breaking changes.
  - Trade-off: Protocol con runtime_checkable hace check estructural por methods declarados (ignora signatures). Aceptable — el contrato es la presencia de `add(...)`.

- **callback handler 6-callbacks duplica copilot**:
  - Tomada: copio el plumbing (on_chat_model_start/end/error, on_tool_start/end/error, on_chain_start/end + helpers) literal a `SalesAgentCallbackHandler`. **No** retrofitea copilot en este sprint.
  - Razón: scope creep — retrofit copilot significa tocar una clase de 580 LOC con production traffic + 250 LOC de tests. Plan original (00-vision §3) protege copilot Phase 2. S6 abre ventana de cleanup arquitectónico.
  - Trade-off: ~250 LOC duplicadas hasta lift. Documentado en tech-debt como DEFERRED-post-S6 con pattern de fix (`on_*` callbacks en abstract base + `_persist_*_row` overrides per-agent).

- **Tracker tool_call_dedup en `state['_tool_dedup_tracker']`**:
  - Tomada: el orchestrator (`chat.py`) crea el tracker antes de `ainvoke` y lo guarda como key arbitraria del initial_state. `node_tool_executor` lo lee desde state cada vez que va a despachar tool.
  - Razón: `AgentState` es TypedDict pero acepta keys extras runtime. LangGraph propaga el dict a todos los nodos. Esto evita global mutable + evita pasar tracker como kwargs (que romperia signatures de nodos pre-existentes).
  - Trade-off: la key `_tool_dedup_tracker` es magic string. Documentada inline como contract entre orchestrator y node_tool_executor. Test arch puede extender en S6.

---

## Sorpresas / gotchas críticos

- **`structlog.warning(event=...)` colisiona** con structlog reserved kwarg `event` (que es el message string). Salí con `TypeError: meth() got multiple values for argument 'event'`. Fix: rename del kwarg a `domain_event_name` en subscribers. **Lección**: nunca pasar `event=...` como structured field en structlog.

- **`from __future__ import annotations` rompe LangGraph runtime introspection**: con `__future__ annotations`, el type hint `RunnableConfig | None` queda como string al import time; LangGraph hace runtime check del shape via `inspect` y emite UserWarning sobre tipado. Fix: usar import directo (no TYPE_CHECKING) + `RunnableConfig` (no `| None`) en `sales_agent_node`. Como LangGraph siempre inyecta config, `Optional` no es necesario.

- **Calculator necesita `cache_write_cost_per_token`**: el `calculate_cost` shared lee el atributo del snapshot — mi fixture stub no lo tenía y best-effort path swallow excepción → trace mirror nunca se persiste. Bug de test fixture, no de prod. **Lección**: mock fixtures deben replicar TODO el atributo set del modelo real, no solo lo que el test mira.

- **`@trace_node` decorator persiste a real DB**: tests de `node_tool_executor` rompen en CI sin mock de `SessionLocal` + `AuditRepository`. Fix: monkeypatch ambos en autouse fixture. **Lección**: cualquier test futuro que toque nodos sales necesita ese mock — considerar fixture compartido en `tests/modules/sales_agent/conftest.py` (DEFERRED, sólo si más nodos se testean).

- **Migration clone DB pattern repeats**: `pg_dump -s | psql -d migration_test` + stamp prod head + upgrade head + verify idempotence + drop. 5 commands. **Útil mantener flujo as-is** — automate como `make migration-test` en S6 si vuelve a repetirse.

- **`agent_log_model.py` no existe** — la doc 02-architecture-target §2 + tech-debt-log lo mencionaban pero la tabla legacy real es `llm_logs` con clase `LLMLog` en `llm_log_model.py`. Sin impacto funcional pero corrijo en learning para que S6 cutover apunte al nombre correcto.

---

## Recomendaciones accionables para S2

- [ ] **S2 cross-agent MV**: `mv_daily_llm_cost_per_tenant_v2` UNION ALL de `copilot_llm_call` + `sales_agent_llm_call` con discriminator `agent_kind`. Ya tenemos los datos — el MV es 1 SQL.
- [ ] **S2 BillingCycleService cross-agent**: parametrizar la table name (hoy hardcoded copilot). Pattern: factory que retorna service por agent_kind.
- [ ] **S2 `costo-agentes` page**: mirror de `costo-copilot`. Usa `_shared.render_agent_kind_selector()` (declarado en admin-migration-plan.md §4 — implementar). Page lee MV cross-agent.
- [ ] **S2 cost alerts cross-agent**: extender `cost_alert_service` para iterate por agent_kind. Default threshold per-tenant viene de `tenant_billing_config.cost_alert_threshold_usd` (ya cross-agent).
- [ ] **S2 retention parametrize**: `purge_expired_trace_rows` hoy SQL hardcoded `copilot_trace_event`. S2 abstrae a worker que itera tabla list = `[copilot_trace_event, sales_agent_trace_event]`. Mismo para llm_call.
- [ ] **S2 NO retrofitea copilot handler aún** — lift al base es post-S6, después del cutover legacy.

---

## Hooks listos

- `backend/src/modules/sales_agent/observability/` — submódulo cohesivo: `recording/{callback_handler,factory}` + `persistence/{models,repos}` + `workers/{dual_write_reconciliation_task}` + `domain_events/subscribers`.
- `backend/src/modules/sales_agent/application/orchestrator/tool_call_dedup.py` — env-prefixed mirror, ready para S6 lift to `shared/agent_observability/tools/` cuando copilot + sales muestren divergencia 0.
- `backend/alembic/versions/078_sales_agent_observability_tables.py` — idempotente, raw SQL `IF NOT EXISTS` en 3 tables + 11 indexes. Test pattern (`pg_dump -s | psql -d migration_test`) probado.
- `backend/tests/architecture/test_sales_agent_observability_invariants.py` — 8 assertions ratchet sin allowlist. Cualquier regresión en subgraph forwarding / best-effort / sanitize_payload routes falla CI.
- `backend/src/workers/settings.py` — `run_sales_agent_dual_write_reconcile` registrado en `WorkerSettings.functions` + `SchedulerSettings.functions` + `SchedulerSettings.cron_jobs (minute=25)`. Off por env, on durante 4-week window.
- `backend/src/admin/modules/sales_audit.py` — dual-read activo. Banner "Dual-read window — leyendo nuevo (N) + legacy (M)" + sidebar prefer event-sourced. Smoke test verde.
- `backend/src/modules/sales_agent/domain/events.py` — 4 events nuevos pydantic-based. Subscribers en `observability/domain_events/subscribers.py` con `register_subscribers(event_bus)` para wiring single-call.

---

## Riesgos abiertos

- **`from __future__ import annotations` en otros archivos sales_agent + LangGraph**: si alguien agrega `RunnableConfig` con `__future__ annotations` repite el UserWarning. Fix preventivo: nunca usar future annotations en archivos que LangGraph introspecta. **Mitigación S1**: arch test bloquea? No. Aceptable porque solo `orchestrator/graph.py` toca config. **Watchpoint**: si futuro nodo declara `config: RunnableConfig`, repetir mi pattern (sin `__future__`).

- **Reconciliation worker mide diff sólo de trace_event vs agent_traces** — no compara `sales_agent_llm_call` vs `llm_logs`. Justificable (legacy `llm_logs` no tiene cost/provider/model_responded típicos; rejoin no es 1:1). **Documentado**: el cutover criterion del plan dice "diff <1% en trace count, dejamos LLM rebuild post-cutover".

- **PII regex performance**: agregamos 7 nuevos regex (4 NATIONAL_ID_STRUCTURAL + 1 NATIONAL_ID_KEYWORD + 1 CARD + 1 CVV) sobre cada string del payload. Benchmark no se midió. **Watchpoint S2**: si callback handler latency p99 > 10ms (research target shared), profiling de regex applies. **Mitigación**: `re.compile` cacheado al import, fast path si len < 5.

- **Subscribers crean su propio SessionLocal**: 4 handlers, 4 sesiones nuevas durante un turn. Best-effort y rápido (single insert + commit), pero contention en pool en alta carga. **Watchpoint**: si turn rate > 10/s/tenant la pool puede saturar. **Mitigación pendiente** (DEFERRED-S2 si emerge): pasar la session orchestrator vía contextvar al subscriber.

- **`tool_call_dedup` no detecta args distintos pero output redundante**: sólo cuenta `(tool_name, args_hash)`. Si Kimi pide `get_lead(x)` → `get_lead(y)` → `get_lead(z)` con x/y/z distintos pero ningún progreso real, no hay ABORT. Aceptable hoy — el copilot anti-loop tiene la misma limitación.

---

## Tech debt detectado (NO arreglado)

- **[MEDIUM]** `SalesAgentCallbackHandler` duplica los 6 LangChain on_* callbacks del copilot `ObservabilityCallbackHandler` (~250 LOC). Lift a `BaseAgentCallbackHandler` cuando copilot retrofitee. **DEFERRED-post-S6**.
- **[LOW]** `agent_log_model.py` mencionado en docs no existe — la tabla legacy es `llm_logs` con clase `LLMLog` en `llm_log_model.py`. **FIX en docs S6 cutover** — actualizar tech-debt-log + admin-migration-plan que mencionan el nombre incorrecto.
- **[LOW]** subscribers crean `SessionLocal()` per-event. **DEFERRED-S2** si reconciliation worker detecta latency spike.
- **[LOW]** `_tool_dedup_tracker` en state es magic string sin type. Considerar TypedDict update si más keys arbitrarias se agregan. **DEFERRED-post-S6**.
- **[NEW LOW]** test fixtures de subscribers + node_tool_executor mockean `SessionLocal` + `AuditRepository` per-test. Promover a `tests/modules/sales_agent/conftest.py` cuando 3+ tests lo necesiten. **DEFERRED-S6 ratchet pass**.

---

## Fuentes research útiles

- [LangChain RunnableConfig propagation (deepwiki)](https://deepwiki.com/langchain-ai/langgraph/3.6-graph-composition-and-nested-graphs) — confirmó nested subgraph callbacks NO propagan automáticamente sin reforward de config.
- [LiteLLM model_prices_and_context_window.json](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json) — Kimi K2.6/K2.5 alias en `pricing/aliases.py` shared verifica costo > 0.
- [LGPD Brazil + ANPD 2026 enforcement priorities](https://tiinside.com.br/en/20/01/2026/lgpd-e-instituicoes-de-pagamento-...) — payment data sensitivity confirmada para retention 90d trace + 365d llm_call.
- [Mexico CURP/RFC validation reference (santoszv/curp-rfc-validators)](https://github.com/santoszv/curp-rfc-validators) — confirmó shape estructural CURP (18) + RFC (12-13) sin keyword.
- [Soft Migrations as Architecture (Bensusan)](https://technori.com/2026/04/25303-treat-soft-migrations-as-architecture-not-scaffolding/sebastian/) — pattern dual-write window con reconciliation activa, drift como expected (medible).

---

## Métricas medidas

- BE quality gates nativos: `ruff check` 0 errors, `ruff format --check` clean, `pytest -m "not verify and not integration"` = **5510 passed, 6 skipped, 10 deselected**.
- Migration `078_sales_agent_observability_tables.py` aplicada idempotente en clone DB (creación + re-run = 0 cambios).
- 8 architectural fitness assertions activas, KNOWN allowlists vacíos.
- Tests nuevos: 41 (10 callback_handler + 9 tool_call_dedup + 3 node_executor_dedup + 4 domain_subscribers + 6 reconciliation + 9 PII LATAM + others).
- Files nuevos/movidos: 13 nuevos (3 models + 3 repos + 1 callback handler + 1 factory + 1 tool_call_dedup + 1 reconciliation worker + 1 subscribers + 1 migration + 1 arch test + ~3 test files). 11 modified (chat.py, graph.py orchestrator, sales/nodes.py, audit_repository.py, sales_audit.py, events.py, sanitization.py, base repos, settings.py workers, master_data arch test, S1 phase doc).
- LOC añadidas: ~1900 (incluye docs + tests + handler + dedup mirror + worker).
- Spanish neutro: NO regresión — agent identity en `_LOOP_DIRECTIVE_TEMPLATE` y mensaje escalation usa tuteo (`pon`, `te`, no voseo). Spanish neutro scan baseline limpio se mantiene (S00 lo dejó verde).
