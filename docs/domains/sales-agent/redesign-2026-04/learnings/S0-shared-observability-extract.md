## Learnings · S0 · shared-observability-extract

> Doc para S1. Foundation lista para sales_agent observability parity.

---

## Resumen (3 líneas)

- **Entregado**: 13 archivos movidos `copilot/observability/{recording,cost,pricing,persistence,reporting,workers}/` → `shared/agent_observability/` (sanitization + cost calculator + fx_resolver + pricing aliases/resolver/litellm_sync + persistence pricing_snapshot + tenant_billing_config repos + models + reporting cycle_window + billing_cycle_service + workers/pricing_sync_task). 3 abstract bases nuevas (`BaseAgentCallbackHandler` Template Method + 2 Repo Protocols). 1 arch test ratchet `test_shared_agent_observability_purity.py` activo (KNOWN_VIOLATIONS vacío).
- **Decisión no obvia**: scope **recortado** vs plan original `02-architecture-target §1`. Solo 13 archivos puros / cross-tenant reference se mueven; `callback_handler.py`, `turn_envelope.py`, `domain_subscribers.py`, `llm_call_repository.py`, `trace_event_repository.py`, `llm_call_model.py`, `cost_aggregator.py`, `cost_alert_service.py`, `retention_task.py`, `aggregate_refresh_task.py`, `cost_alert_task.py` quedan en `copilot/observability/` porque están acoplados a tablas `copilot_*` o domain events específicos. S1/S2 los abstrae cross-agent.
- **Listo para S1**: 2522 tests verdes (copilot/ + arch/ + admin/ + shared/), branch `development` limpio, ruff 0 errors, format check verde, test arch shared purity activo, abstract bases declaradas para que `SalesAgentCallbackHandler` herede.

---

## Decisiones clave

- **Move físico, sin re-exports transitorios**:
  - Tomada: cada `git mv` actualiza todos los consumers en el mismo flujo (sed bulk). No `from src.modules.copilot.observability.X import *` shims temporales.
  - Razón: anti-parche `04-principles §1.4` + observability rebuild `PRINCIPLES §2 migración total no paralela`. Re-exports = código muerto que rota.
  - Alternativa descartada: dejar shims 4 semanas. Rechazada — los grep de imports se hacen rápido (1 sed por archivo movido) y el blast radius es pequeño (~20 callers BE+tests).

- **Scope recortado vs plan original**:
  - Tomada: 13 archivos a shared (puros / cross-tenant reference data). 11 quedan en copilot/.
  - Razón: `cost_aggregator`, `retention_task`, `aggregate_refresh_task`, `cost_alert_service` tienen SQL hardcoded sobre tablas `copilot_*` (ej. `DELETE FROM copilot_trace_event`, `REFRESH MATERIALIZED VIEW mv_daily_llm_cost_per_tenant`, `select(CopilotLlmCallModel)`). Mover ahora requeriría parametrizar por `agent_kind` + cross-agent MV, fuera del scope S0.
  - Alternativa: forzar mover todo + introducir parametrización ad-hoc. Rechazada — eso es S2 (cross-agent MV `mv_daily_llm_cost_per_tenant_v2`). En S0 no hay 2do consumer real para esos archivos hasta S1.

- **`agent_kind` string libre, no enum**:
  - Tomada: shared no declara `enum AgentKind`. El discriminator vive en MV cross-agent (S2) como columna `VARCHAR`.
  - Razón: reference data tables (`model_pricing_snapshot`, `tenant_billing_config`) son globales — no necesitan discriminator. Y un enum en shared crea acoplamiento prematuro: cada nuevo agente requeriría migration + bump.
  - Trade-off: type checker no valida values. Aceptable: el valor solo aparece en columnas DB que cada agent escribe a su propia tabla.

- **Repo abstracto = Protocol PEP 544, no ABC**:
  - Tomada: `BaseLLMCallRepoProtocol` y `BaseTraceEventRepoProtocol` son `typing.Protocol` con structural typing.
  - Razón: copilot usa sync `Session`, sales_agent (S1) puede usar async `AsyncSession`. Protocol via `add(...)` deja ambos satisfacer sin herencia. Backend DDD §3.3 en CLAUDE.md tolera ambos.
  - Alternativa: ABC con generic `[T_Session]`. Rechazada — generic boilerplate sin payoff hoy.

- **`BaseAgentCallbackHandler` ABC sí, no Protocol**:
  - Tomada: `recording/base_callback_handler.py` es abstract Template Method que extiende `langchain_core.callbacks.BaseCallbackHandler`. Subclase obligatoria para implementar `_persist_llm_call_row` + `_persist_trace_event_row`.
  - Razón: LangChain `BaseCallbackHandler` ya es jerarquía concreta — Protocol no compone con herencia obligada de la library. ABC herencia compone naturalmente.

- **No retrofit copilot callback handler en S0**:
  - Tomada: `ObservabilityCallbackHandler` (copilot) NO hereda de `BaseAgentCallbackHandler` aún. Mantiene su shape self-contained.
  - Razón: §3 zero behavior change copilot. S1 retrofitea ambos handlers (copilot + sales_agent nuevo) en el mismo sprint cuando hay 2 consumers reales.
  - Trade-off: la abstract base S0 está "huérfana" hasta S1. Aceptable: la ratchet arch test bloquea regresiones al subpaquete.

---

## Sorpresas / gotchas críticos

- **`cost_alert_service.py` import depth**: el archivo `application/cost_alert_service.py` quedó en copilot (depende de `cost_aggregator` con SQL copilot) pero importa `BillingCycleService` (movido a shared) + `TenantBillingConfigModel` (movido). Funciona porque copilot importando shared es ✅; arch test bloquea solo el otro sentido. Validación: el arch test `test_shared_agent_observability_purity` pasa.
- **sed pattern engaño**: el primer bulk `s|src.modules.copilot.observability.cost|src.shared.agent_observability.cost|g` matcheó tanto `src/modules/...cost/fx_resolver.py` (con slashes) como `src.modules...cost.fx_resolver` (con dots) porque `.` en regex matches any char. Resultó en string mangled `src.shared.agent_observability.cost/fx_resolver.py` en `tests/architecture/test_master_data.py:32`. Fix manual con `Edit`. **Lección S1+: usar `\.` escapado o sed con delimitador no-slash + escape de dots**.
- **import-from-module pattern**: en `tests/.../reporting/test_billing_cycle_service.py:69,83`: `from src.modules.copilot.observability.reporting import billing_cycle_service` (sin `.billing_cycle_service` final). El sed bulk no lo cubría — falló con `ImportError`. Fix manual con sed específico para esa forma. **Lección**: el grep inicial debe cubrir 3 patterns: `from X.Y.Z import a`, `from X.Y import Z`, `import X.Y.Z`.
- **Allowlist arch test apunta a path**: `KNOWN_USD_DEFAULT_FILES` y similares mantienen path strings literal. Cualquier move requiere update simultáneo del allowlist o el test falla. `tests/architecture/test_master_data.py` actualizado para 2 paths.
- **Empty `__init__.py` después de move**: `copilot/observability/cost/`, `copilot/observability/pricing/` quedaron sin archivos hijos → `rmdir` los borró. Las dirs no aparecen en git si están vacías; OK.

---

## Recomendaciones accionables para S1

- [ ] **S1 retrofit copilot handler**: `ObservabilityCallbackHandler` (copilot) hereda de `BaseAgentCallbackHandler` y mueve la lógica `_persist_llm_call` actual (~67 líneas) al método del base. Override `_persist_llm_call_row` + `_persist_trace_event_row` con repos copilot. Tests `test_callback_handler.py` (250 LOC) deben seguir verdes sin cambio.
- [ ] **S1 declarar `SalesAgentCallbackHandler`**: hereda `BaseAgentCallbackHandler`, override con `SalesAgentLlmCallRepository` + `SalesAgentTraceEventRepository` (nuevos en S1). El handler concrete agrega kwargs `lead_id` + `channel_type` que el `_persist_*_row` abstract acepta vía `**agent_specific`.
- [ ] **S1 mover cost_aggregator + retention/aggregate_refresh/cost_alert a shared parametrizada por table name**: reservar para S2. Por ahora copilot conserva sus copies. Sales_agent tendrá clones idénticos en su módulo hasta cross-agent MV (S2).
- [ ] **S1 PII regex extension**: el `sanitization.py` movido contiene email + LATAM phones + API tokens. Sales_agent extiende con `dni|curp|cuit|rfc|cvv|nro tarjeta` patterns. Como `redact_string` aplica regex tuple ordenado, S1 puede agregar al tuple sin tocar el `redact_value` walker.
- [ ] **S1 alembic migrations**: nuevas tablas `sales_agent_llm_call`, `sales_agent_trace_event`, `sales_agent_routing_log` (mirror copilot + lead_id + channel_type). Reuse `model_pricing_snapshot` + `tenant_billing_config` (compartido cross-agent post-S0).
- [ ] **S1 dual-read sales_audit.py**: ya documentado en `audit/admin-migration-plan.md §2`. Ventana 4 semanas.

---

## Hooks listos

- `backend/src/shared/agent_observability/` — 6 subpaquetes con responsabilidad única. S1+ amplía `recording/`, `persistence/` con concretes. NO mover archivos copilot-específicos sin verificar acoplamiento a tablas.
- `backend/tests/architecture/test_shared_agent_observability_purity.py` — ratchet activo, `KNOWN_VIOLATIONS = set()`. Cualquier import nuevo de `src.modules.*` desde `shared/agent_observability/` falla CI.
- `backend/src/shared/agent_observability/recording/base_callback_handler.py` — `BaseAgentCallbackHandler` (Template Method) listo para S1 retrofit copilot + nuevo sales_agent.
- `backend/src/shared/agent_observability/persistence/{base_llm_call_repo,base_trace_event_repo}.py` — Protocols listos para S1 sales_agent repos.
- `backend/src/workers/settings.py` — registra `sync_litellm_pricing` desde shared. S1+ workers retention/aggregate_refresh/cost_alert seguirán importando de copilot/ hasta S2.
- `backend/tests/architecture/test_master_data.py` — `ALLOWED_USD_DEFAULT_FILES` actualizado a `src/shared/agent_observability/{cost/fx_resolver.py, persistence/models/tenant_billing_config_model.py}`.

---

## Riesgos abiertos

- **`copilot/observability/__init__.py`** sigue exportando `register` + `ObservabilityContext` desde paths copilot. S1 cuando refactore callback_handler para heredar `BaseAgentCallbackHandler` verifica que `ObservabilityContext.start(...)` sigue produciendo el handler correcto.
- **No-test-coverage para `BaseAgentCallbackHandler` con concrete subclass**: las abstract methods están testeadas (cannot instantiate, abstracts list). Pero ningún concrete subclass lo hereda aún → S1 tests del retrofit son los que validan E2E.
- **Stage anchor test_master_data.py allowlist**: cualquier futuro move de archivo `cost/fx_resolver.py` o `persistence/models/tenant_billing_config_model.py` requiere update simultáneo. **No es bug** — solo recordatorio para future Claude que toque ese subpaquete.
- **`pricing/aliases.py` Kimi K2.6/K2.5**: se mantuvo idéntico al move (commit a3f65d04). Sales_agent (S1+) puede agregar entries sin tocar copilot — el dict `PROVIDER_MODEL_ALIASES` es punto único.

---

## Tech debt detectado (NO arreglado)

- [LOW] `src/modules/copilot/observability/__init__.py` lista subpaquetes que ya no existen físicamente (cost, pricing) en su docstring. **Decisión**: no actualizar acá — el doc-string apunta a la realidad post-S0 (recording, persistence, reporting, workers, application, api permanentes copilot-side). Si confunde, S1 lo limpia.
- [LOW] No quedan orphans-pre-existentes (DEFERRED-S0 de `05-tech-debt-log`) en archivos tocados por S0 — los 4 orphans `features/sales/components/dashboard/{ActivityFeedWidget,CalendarWidget}.tsx` + `overlay/{AppointmentSheet,AvailabilityModal}.tsx` no se tocaron porque S0 fue 100% backend. **Mantienen DEFERRED-S0 status**, candidatos S1 si toca FE.
- [LOW] `knowledge_builder.py` (217 LOC, sales_agent) sigue con lazy-imports brand+offer cross-module. S0 backend-only no formalizó ports `shared/links/`. DEFERRED-S0 → DEFERRED-post-S6 (refactor cohesión candidate).

---

## Fuentes research útiles

- [LangChain BaseCallbackHandler](https://reference.langchain.com/python/langchain_core/callbacks/) — confirmó subclass + `RunnableConfig(callbacks=[...])` pattern post-LangChain 0.3 sin breaking. Async-first recomendado pero sync handlers válidos para best-effort.
- [Cosmic Python Ch.7 Aggregates and Consistency Boundaries](https://www.cosmicpython.com/book/chapter_07_aggregate.html) — ratificó "shared primitives + per-BC concretes" sobre "Strategy parametrizado" cuando los tables divergen (sales_agent agrega `lead_id`/`channel_type`).
- [LiteLLM model_prices_and_context_window.json](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json) — schema 2026 sin breaking changes; nuevos campos opcionales (`deprecation_date`, `supports_*`, `input_cost_per_token_above_200k_tokens` tier pricing). Parser actual sigue válido. Tier-pricing >200k = follow-up debt (no en scope S0).

---

## Métricas medidas

- BE quality gates: `ruff check src/ tests/` 0 errors; `ruff format --check` verde; `pytest tests/modules/copilot/ tests/architecture/ tests/admin/ tests/shared/ -q` = **2522 passed** en ~60s.
- Archivos movidos: 13 (`git mv` preservó history).
- Archivos creados nuevos: 5 (3 abstract bases en shared + 1 arch test + 1 test bases).
- LOC añadidas (docs + tests + abstract bases): ~340 (learning + S0 phase doc + arch test + base files + base test).
- Imports actualizados: ~20 archivos (BE + tests).
- Spanish neutro scan: N/A (S0 solo backend, no user-facing).
- Allowlist `KNOWN_VIOLATIONS` en arch test shared purity: vacío.
