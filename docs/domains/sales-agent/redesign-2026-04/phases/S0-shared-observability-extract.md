# S0 · Extract `shared/agent_observability/` (foundation)

## Objetivo

Extraer la capa de observabilidad de `copilot/observability/` a `shared/agent_observability/` parametrizada por `agent_kind`. **Zero behavior change** en copilot. Foundation para que sales_agent (S1+) consuma el mismo substrate.

## Dependencias

- Ninguna (foundation phase).

## Criterios de éxito

1. `src/shared/agent_observability/` existe con sub-paquetes: `recording/`, `pricing/`, `cost/`, `persistence/`, `reporting/`, `workers/`.
2. `BaseAgentCallbackHandler` (abstract) declarado en `recording/base_callback_handler.py`.
3. `sanitization.py`, `litellm_sync.py`, `cost/calculator.py`, `cost/fx_resolver.py`, `reporting/billing_cycle_service.py`, `reporting/cycle_window.py` movidos sin lógica modificada (o re-exportados via thin adapter inicial).
4. Copilot consume desde `shared/` en vez de paths internos. Imports actualizados.
5. **Cero diff funcional**: `copilot_llm_call`, `copilot_trace_event`, `model_pricing_snapshot` schema y comportamiento idénticos.
6. Quality gates pasan: ruff + pytest copilot + arch tests.
7. Tests copilot existentes verdes sin modificar lógica de tests (solo paths de import si exposés).
8. Anti-pattern check: `tests/architecture/test_no_new_copilot_module_imports.py` no se relaja.

## Research mandate

> Antes de codear, ejecutar este research fresco y poblar la sección "Hallazgos research" abajo.

### Queries WebSearch obligatorias

1. `LangChain BaseCallbackHandler best practices async 2026` — verificar si la clase base sigue siendo el handler correcto post-LangChain 0.3.
2. `Python shared module DDD multi-bounded-context observability pattern` — patrones de extract a shared sin coupling.
3. `LiteLLM model_prices_and_context_window.json schema 2026` — el JSON es el SSoT del worker `pricing_sync_task`. Verificar shape vigente.

### Tessl tiles a verificar

- `tessl__langgraph` — invariantes del callback handler en LangGraph 0.3+.
- `tessl__fastapi` — patterns de shared module + DI.

### Lectura obligatoria del codebase

- `backend/src/modules/copilot/observability/recording/callback_handler.py` (entero)
- `backend/src/modules/copilot/observability/recording/sanitization.py`
- `backend/src/modules/copilot/observability/pricing/litellm_sync.py`
- `backend/src/modules/copilot/observability/cost/calculator.py`
- `backend/src/modules/copilot/observability/reporting/billing_cycle_service.py`
- `backend/src/modules/copilot/observability/persistence/` — entender repos
- `.claude/rules/copilot-observability.md`
- `docs/domains/copilot/observability-rebuild-2026-04/ARCHITECTURE.md` (si existe)

### Hallazgos research (2026-04-28)

**LangChain `BaseCallbackHandler`** (`reference.langchain.com/python/langchain_core/callbacks/`, `python.langchain.com/api_reference/core/callbacks.html`): API estable post-LangChain 0.3. Pattern subclass + `RunnableConfig(callbacks=[handler])` ratificado. Async-first recomendado pero el handler actual usa métodos sync (suficiente porque la persistencia es best-effort fuera del hot path). Sin breaking changes que afecten el extract.

**Python DDD shared bounded context** (Cosmic Python ch.7, contextmapper.org, dev.to/aws-builders/modeling-shared-entities-across-bounded-contexts): cuando 2 BC consumen el mismo concepto cross-cutting (observability) la convención es `shared/` con primitives + cada BC implementa su concrete. **Confirmado el plan original**: pure helpers + reference data tables al shared, concretes específicos del agente quedan en su BC. NO Strategy parametrizado por `agent_kind` para SQL — cada BC tiene su tabla porque el shape diverge (sales agrega `lead_id`/`channel_type`).

**LiteLLM `model_prices_and_context_window.json`** (`docs.litellm.ai/docs/provider_registration/add_model_pricing`, `github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json`): schema 2026 sin breaking changes — sigue exponiendo `input_cost_per_token`, `output_cost_per_token`, `cache_read_input_token_cost`, `cache_creation_input_token_cost`, `litellm_provider`, `mode`, plus nuevos `deprecation_date`, `supports_*` booleans, `input_cost_per_token_above_200k_tokens` (tier pricing). El parser `_parse_entry` actual (chat/completion only, requires `input_cost_per_token` + `output_cost_per_token` + `litellm_provider`) sigue siendo correcto. Tier pricing >200k tokens = follow-up debt (no en S0).

---

## Ajustes vs plan original

Tras revisar `copilot/observability/` archivo-por-archivo + grep de callers, **el scope se RECORTA** vs el plan original de `02-architecture-target.md §1`. La extracción shared es válida pero solo aplica a un subset.

### Lo que SÍ se mueve a `shared/agent_observability/`

Símbolos puros / reference data cross-tenant / sin acoplamiento a tablas concretas:

| Archivo | Por qué movible |
|---|---|
| `recording/sanitization.py` | Pure regex, zero state. |
| `cost/calculator.py` | Pure function (tokens × pricing snapshot). |
| `cost/fx_resolver.py` | Pure (USD → tenant currency via Frankfurter). |
| `pricing/aliases.py` | Pure data dict. |
| `pricing/resolver.py` | Protocol-based, agnóstico a tabla concreta. |
| `pricing/litellm_sync.py` | Solo necesita `PricingSnapshotRepository` (también movido). |
| `persistence/pricing_snapshot_repository.py` | Tabla **global cross-tenant** `model_pricing_snapshot` (reference data). |
| `persistence/tenant_billing_config_repository.py` | Tabla **global** `tenant_billing_config`. |
| `persistence/models/pricing_snapshot_model.py` | Idem. |
| `persistence/models/tenant_billing_config_model.py` | Idem. |
| `reporting/cycle_window.py` | Pure cycle math. |
| `reporting/billing_cycle_service.py` | Solo lee `tenant_billing_config` (global). |
| `workers/pricing_sync_task.py` | Solo orquesta `sync_pricing` con `SessionLocal`. |

Nuevos en shared (foundations para S1):

| Archivo | Razón |
|---|---|
| `recording/base_callback_handler.py` | Abstract Template Method. S1 sales_agent hereda. NO fuerza herencia copilot en S0 (zero behavior change). |
| `persistence/base_llm_call_repo.py` | Abstract repo Protocol. S1 mirror. |
| `persistence/base_trace_event_repo.py` | Abstract repo Protocol. |

### Lo que NO se mueve (queda en `copilot/observability/`)

Acoplamiento físico a tablas `copilot_*` o domain events específicos del copilot. **S2/S1 abstracta** (cross-agent MV + retention parametrizada).

| Archivo | Por qué queda |
|---|---|
| `recording/callback_handler.py` | Concreto copilot. S1 abstrae cuando declare `SalesAgentCallbackHandler`. |
| `recording/turn_envelope.py` | Hardcoded `CopilotLlmCallModel` aggregate query + `_legacy_compat_keys` específicos copilot. |
| `recording/domain_subscribers.py` | Específico `EVENT_CARD_EMITTED` / `EVENT_ROUTING_DECIDED` copilot domain. |
| `persistence/llm_call_repository.py` | Concreto `CopilotLlmCallModel`. |
| `persistence/trace_event_repository.py` | Concreto `CopilotTraceEventModel`. |
| `persistence/models/llm_call_model.py` | Tabla `copilot_llm_call`. |
| `application/cost_alert_service.py` | Lee via `CostAggregator` (cosa copilot). S2 cross-agent. |
| `reporting/cost_aggregator.py` | Hardcoded `CopilotLlmCallModel` queries. S2 abstrae con MV cross-agent. |
| `workers/retention_task.py` | SQL hardcoded `DELETE FROM copilot_trace_event/copilot_llm_call`. S1 cross-agent. |
| `workers/aggregate_refresh_task.py` | SQL hardcoded `REFRESH MATERIALIZED VIEW mv_daily_llm_cost_per_tenant`. S2 cross-agent MV v2. |
| `workers/cost_alert_task.py` | Wrapper de `cost_alert_service`. |

### Decisiones clave

- **No re-exports transitorios.** Anti-parche `04-principles.md §1.4` + observability rebuild `PRINCIPLES.md §2`. Cada move actualiza todos los consumers en el mismo commit. Borrar el path viejo. Test fail si caller no actualizado.
- **`agent_kind` como string libre** (no enum). Razón: S2 puede agregar agentes futuros sin migración; el discriminator vive en MV cross-agent (`copilot` / `sales_agent`).
- **`BaseLLMCallRepo` Protocol-based**, no abstract con SQLAlchemy session. Razón: copilot tiene sync `Session`, sales_agent puede tener async `AsyncSession`. Protocol via `add(...)` agnostic.
- **`pricing_sync_task` único worker movido**. Razón: el task no toca tablas copilot_*; los otros 3 workers sí.
- **Imports tests**: actualizo todos los tests de `tests/modules/copilot/observability/` que apuntan a paths movidos. Tests de archivos que quedan en copilot conservan sus imports.

---

## Diseño

### Estructura target

```
src/shared/agent_observability/
├── __init__.py                          # exports public
├── recording/
│   ├── __init__.py
│   ├── base_callback_handler.py         # NEW: abstract base
│   ├── sanitization.py                  # MOVED from copilot
│   └── turn_envelope.py                 # MOVED (parametrize agent_kind)
├── pricing/
│   ├── __init__.py
│   ├── litellm_sync.py                  # MOVED
│   └── resolver.py                      # MOVED
├── cost/
│   ├── __init__.py
│   ├── calculator.py                    # MOVED
│   └── fx_resolver.py                   # MOVED
├── persistence/
│   ├── __init__.py
│   ├── base_llm_call_repo.py            # NEW: abstract repo
│   └── base_trace_event_repo.py         # NEW: abstract repo
├── reporting/
│   ├── __init__.py
│   ├── billing_cycle_service.py         # MOVED (parametrize tables)
│   ├── cost_aggregator.py               # MOVED
│   └── cycle_window.py                  # MOVED
└── workers/
    ├── __init__.py
    ├── pricing_sync_task.py             # MOVED (no per-agent code)
    ├── retention_task.py                # MOVED (parametrize table+days)
    └── aggregate_refresh_task.py        # MOVED
```

### Patrón GoF

- **Template Method** en `BaseAgentCallbackHandler`:
  ```python
  class BaseAgentCallbackHandler(BaseCallbackHandler):
      async def on_chat_model_start(self, ...): self._open_span(...)
      async def on_llm_end(self, ...):
          call = self._build_llm_call_event(...)
          call = self._apply_sanitization(call)  # shared
          call = self._resolve_pricing(call)     # shared
          await self._persist_llm_call(call)     # subclass impl

      @abstractmethod
      async def _persist_llm_call(self, call: LLMCallEvent) -> None: ...
  ```
- **Strategy** para PII regex pack: extensible per agent (sales_agent extiende con CURP/CUIT/DNI).
- **Repository pattern**: `BaseLLMCallRepo[T]` abstract con `add(call: T)`. Subclase per agente con tabla concreta.

### Decisiones clave (resueltas)

- [x] **Mover físicamente, sin re-exports.** Anti-parche.
- [x] **`agent_kind` string libre.** Reference data (`model_pricing_snapshot`, `tenant_billing_config`) son cross-agent puros — no necesitan discriminator.
- [x] **`BaseLLMCallRepo` Protocol** (PEP 544). Permite sync `Session` (copilot) + futuro async `AsyncSession` (sales_agent S1) sin acoplar a un dialecto SQL.
- [x] **`pricing_sync_task` registrado en `workers/settings.py` desde su nuevo path shared.** Único worker shared en S0; S1/S2 mueven retention/aggregate_refresh/cost_alert cuando se desacoplen de tablas copilot_*.

---

## Plan TDD

### RED tests primero

1. `tests/shared/agent_observability/test_base_callback_handler_invariants.py`:
   - `BaseAgentCallbackHandler` no instanciable (abstract).
   - Subclase concreta llama `_persist_llm_call` con sanitized payload.
   - Excepción en `_persist_llm_call` NO rompe turn (best-effort).

2. `tests/shared/agent_observability/test_sanitization_invariants.py`:
   - Email LATAM redactado.
   - Phone con/sin keyword redactado.
   - API tokens (sk-*, gsk_*, xai-*) redactados.
   - Strings >4000 chars truncados.
   - Pure function, no side effects.

3. `tests/shared/agent_observability/test_pricing_resolver.py`:
   - `resolve(provider, model, ts)` retorna snapshot vigente.
   - Si no hay snapshot vigente → cost 0 + log warning.
   - Cache hit en lookup secuencial.

4. `tests/architecture/test_shared_observability_purity.py`:
   - `shared/agent_observability/` NO importa de `modules/`.
   - `recording/sanitization.py` NO usa SQL.
   - `cost/calculator.py` es pure function.

5. **Regression copilot**:
   - `tests/modules/copilot/observability/` existentes pasan sin tocar lógica.
   - Si paths de import cambian, ajustar imports — NO la lógica del test.

---

## Implementación step-by-step

1. Crear estructura `src/shared/agent_observability/` con `__init__.py` vacíos.
2. Mover `sanitization.py` → re-export en path antiguo (backwards compat transitorio).
3. Mover `cost/calculator.py`, `cost/fx_resolver.py` similar.
4. Mover `pricing/litellm_sync.py`, `pricing/resolver.py`.
5. Mover `reporting/billing_cycle_service.py`, `cost_aggregator.py`, `cycle_window.py`.
6. Mover `workers/pricing_sync_task.py`, `retention_task.py`, `aggregate_refresh_task.py`.
7. Declarar `BaseAgentCallbackHandler` (abstract) — extraer template del concrete copilot handler.
8. Refactor `copilot/observability/recording/callback_handler.py` para heredar `BaseAgentCallbackHandler` (concreto solo `_persist_llm_call`, `_persist_trace_event`).
9. Declarar `BaseLLMCallRepo`, `BaseTraceEventRepo` abstract.
10. Refactor copilot repos a heredar abstract bases.
11. Actualizar `workers/settings.py` para registrar tasks desde shared.
12. Borrar paths antiguos (después de verificar que no hay imports).

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Romper copilot durante extract | Tests existentes verdes obligatorio antes de avanzar cada step. Re-exports transitorios mientras se migran imports. |
| Coupling prematuro (sólo copilot consume hoy) | Justificación: S1 ya tiene a sales_agent como 2do consumer real. NO esperar. |
| Conflict con observability-rebuild en curso | Verificar que el rebuild ya cerró (commits previos sugieren sí). Si abierto → coordinar con usuario. |
| Workers ARQ cambian de location | `workers/settings.py` (raíz) es SSoT — registrar nuevos paths shared. |

---

## Tech debt watchpoints

- Si encuentras pricing inline hardcoded en copilot (post-rebuild no debería) → loggear.
- Si `sanitization.py` tiene regex específica de copilot que sales_agent no necesitará → mantener pero anotar.
- Si `turn_envelope.py` mezcla agent_kind hardcoded → eliminar acoplamiento.
- Si tests copilot importan paths internos en vez de API pública → aprovechar la fase para refactor mínimo.

---

## Ajustes vs plan original

> COMPLETAR si research/implementación reveló desviación del plan target (`02-architecture-target.md §1`).
