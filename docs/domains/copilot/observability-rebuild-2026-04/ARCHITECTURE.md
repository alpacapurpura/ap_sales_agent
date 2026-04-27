# Target Architecture — Copilot Observability

> Estado objetivo tras Fase 3. Toda decisión de diseño aquí es vinculante; cambios requieren actualizar este doc + nota en `learnings.md` de la fase respectiva.

## 1. Principio rector

**Observability se suscribe; copilot no la invoca.** El acoplamiento es a la API estable de LangChain (callbacks) + al event bus de dominio del copilot, **no** a la estructura interna del orchestrator.

Consecuencia: agregar tools, nodos, providers LLM, card kinds, workflows, **no requiere tocar el módulo de observability**.

## 2. Diagrama estructural

```
┌────────────────────────────────────────────────────────────────┐
│                          COPILOT                                │
│                                                                 │
│  application/orchestrator/   ← chat.py, deep_agent, graph       │
│  application/tools/          ← langchain Tools                  │
│  domain/events.py            ← CardEmitted, RoutingDecided, ... │
│                                                                 │
│  Solo conoce dos cosas:                                         │
│   1. LangChain/LangGraph (framework)                            │
│   2. Su propio event bus (publica, no consume)                  │
└────────────────────────────────────────────────────────────────┘
              │ callbacks                  │ domain events
              │ (estándar LangChain)       │ (shared event bus)
              ▼                            ▼
┌────────────────────────────────────────────────────────────────┐
│         backend/src/modules/copilot/observability/              │
│                                                                 │
│  recording/                                                     │
│    callback_handler.py     ← BaseCallbackHandler subclass       │
│      on_chat_model_start  → llm_call open span                  │
│      on_chat_model_end    → finalize llm_call (tokens, cost)    │
│      on_tool_start/end    → tool_call rows                      │
│      on_chain_start/end   → node_enter/node_exit                │
│      on_llm_error         → error rows                          │
│    domain_subscribers.py   ← copilot domain events → trace rows │
│    turn_envelope.py        ← turn_start/turn_end span context   │
│    sanitization.py         ← truncate + PII redaction           │
│                                                                 │
│  pricing/                                                       │
│    resolver.py             ← (provider, model, ts) → unit cost  │
│    litellm_sync.py         ← daily pull GitHub raw → snapshot   │
│                                                                 │
│  cost/                                                          │
│    calculator.py           ← tokens × unit cost = cost_usd      │
│    fx_resolver.py          ← USD → tenant currency snapshot     │
│                                                                 │
│  persistence/                                                   │
│    llm_call_repository.py                                       │
│    trace_event_repository.py                                    │
│    pricing_snapshot_repository.py                               │
│    tenant_billing_config_repository.py                          │
│                                                                 │
│  reporting/                                                     │
│    billing_cycle_service.py  ← compute_cycle_window(t, date)    │
│    cost_aggregator.py        ← rollups por día/modelo/tenant    │
│                                                                 │
│  workers/                                                       │
│    pricing_sync_task.py    ← ARQ daily 03:00 UTC                │
│    aggregate_refresh_task.py ← ARQ hourly REFRESH MV            │
│    retention_task.py       ← ARQ daily, drop > N days           │
│                                                                 │
│  api/  (interno al admin, no expuesto al frontend público)      │
│    routes_billing.py       ← endpoints para Streamlit           │
└────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────┐
│                    backend/src/admin/                           │
│  modules/costo_copilot.py  + modules/trazas.py (refactored)     │
│  modules/copilot_routing.py (refactored, lee módulo nuevo)      │
└────────────────────────────────────────────────────────────────┘
```

## 3. Seams (qué cruza el boundary)

### Seam A — LangChain/LangGraph callbacks

API estable, no la inventamos. La heredamos de `langchain_core.callbacks.BaseCallbackHandler`.

| Callback | Captura | Tabla destino |
|---|---|---|
| `on_chat_model_start` | provider, model_requested, started_at | abre span en memoria |
| `on_chat_model_end` | tokens, model_responded, cached_*, response_id | `copilot_llm_call` + `copilot_trace_event` |
| `on_tool_start` | tool_name, args | abre span en memoria |
| `on_tool_end` | output, duration | `copilot_trace_event` (`tool_call`) |
| `on_chain_start/end` | node_name, graph_step | `copilot_trace_event` (`node_enter/exit`) |
| `on_llm_error` / `on_tool_error` | error_type, error_message | `copilot_trace_event` (status='error') |

**Cómo se inyecta:** `RunnableConfig(callbacks=[handler])` en `graph.astream_events(state, config=obs.langchain_config())`. Una sola línea en chat.py.

### Seam B — Domain events del copilot

Eventos que NO son LangChain-nativos (cards, routing decisions, mutations). Publicados via `shared/events/event_bus.py`. Subscribers en `observability/recording/domain_subscribers.py`.

| Evento | Quién publica | Qué captura |
|---|---|---|
| `CardEmitted(card_kind, source_tool, payload_keys)` | tools / extraction_card_flow | `copilot_trace_event` (`card_emitted`) |
| `RoutingDecided(tier, classifier, confidence)` | orchestrator | `copilot_routing_log` + trace event |
| `MutationApplied(domain, field_path, ...)` | propose_field_updates | `copilot_mutation_journal` (sin cambios — ya existe) |
| `TurnStarted(message_preview, route, attachments)` | orchestrator | `copilot_trace_event` (`turn_start`) |
| `TurnEnded(...)` | orchestrator | `copilot_trace_event` (`turn_end`) — pero **agregado vino del callback handler**, no calculado en chat.py |

**Cómo se inyecta:** subscribers se registran al boot del módulo (`observability/__init__.py` → `register_subscribers()`). Cero llamadas explícitas desde chat.py.

## 4. Schema DB final

### 4.1 Existentes — qué pasa con ellas

| Tabla | Estado tras rebuild |
|---|---|
| `copilot_trace_event` | **Mantiene**. Sigue siendo log canónico de eventos. Schema sin breaking changes; solo agrega event_type='llm_call' real. |
| `copilot_conversations` | Sin cambios. |
| `copilot_routing_log` | Sin cambios (ya correcto). |
| `copilot_events` | Sin cambios. |
| `copilot_mutation_journal` | Sin cambios. |
| `copilot_workflow_metric` | Sin cambios. |
| `copilot_pinned_memory`, `copilot_inspiration` | Sin cambios. |

### 4.2 Nuevas (Fase 1)

```sql
-- Una row por invocación LLM. Event-sourced, immutable.
CREATE TABLE copilot_llm_call (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    conversation_id UUID,
    turn_id UUID NOT NULL,
    span_id UUID NOT NULL,           -- mismo árbol que copilot_trace_event
    parent_span_id UUID,
    role VARCHAR(32) NOT NULL,       -- 'agent' | 'judge' | 'classifier' | 'summarizer'
    provider VARCHAR(32) NOT NULL,   -- 'openai' | 'anthropic' | 'google' | 'xai'
    model_requested VARCHAR(128) NOT NULL,
    model_responded VARCHAR(128) NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cached_read_tokens INTEGER NOT NULL DEFAULT 0,
    cached_write_tokens INTEGER NOT NULL DEFAULT 0,
    reasoning_tokens INTEGER NOT NULL DEFAULT 0,
    pricing_version_id UUID NOT NULL,
    input_unit_cost_usd NUMERIC(14,12) NOT NULL,
    output_unit_cost_usd NUMERIC(14,12) NOT NULL,
    cached_read_unit_cost_usd NUMERIC(14,12) NOT NULL DEFAULT 0,
    cost_usd NUMERIC(16,10) NOT NULL,
    tenant_currency CHAR(3),
    fx_rate_to_tenant NUMERIC(16,8),
    fx_rate_source VARCHAR(32),
    cost_tenant_currency NUMERIC(16,8),
    started_at TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ok',
    error_type VARCHAR(64),
    occurred_on DATE GENERATED ALWAYS AS (started_at::date) STORED,
    occurred_year_month VARCHAR(7) GENERATED ALWAYS AS (to_char(started_at, 'YYYY-MM')) STORED
);
CREATE INDEX ix_llm_call_tenant_day ON copilot_llm_call (tenant_id, occurred_on);
CREATE INDEX ix_llm_call_turn ON copilot_llm_call (turn_id);
CREATE INDEX ix_llm_call_tenant_model_day ON copilot_llm_call (tenant_id, model_responded, occurred_on);
CREATE INDEX ix_llm_call_errors ON copilot_llm_call (tenant_id, started_at DESC) WHERE status='error';

-- Pricing histórico point-in-time (snapshot per provider+model con valid_from/valid_to).
CREATE TABLE model_pricing_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(32) NOT NULL,
    model VARCHAR(128) NOT NULL,
    input_cost_per_token NUMERIC(14,12) NOT NULL,
    output_cost_per_token NUMERIC(14,12) NOT NULL,
    cache_read_cost_per_token NUMERIC(14,12) DEFAULT 0,
    cache_write_cost_per_token NUMERIC(14,12) DEFAULT 0,
    batch_input_cost_per_token NUMERIC(14,12),
    source VARCHAR(32) NOT NULL,        -- 'litellm' | 'manual'
    source_etag VARCHAR(64),
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,                -- NULL = vigente
    raw_payload JSONB NOT NULL
);
CREATE UNIQUE INDEX ix_pricing_active ON model_pricing_snapshot (provider, model) WHERE valid_to IS NULL;
CREATE INDEX ix_pricing_lookup ON model_pricing_snapshot (provider, model, valid_from DESC);

-- Anchor de ciclo billing + currency por tenant.
CREATE TABLE tenant_billing_config (
    tenant_id UUID PRIMARY KEY,
    billing_cycle_anchor_day SMALLINT NOT NULL DEFAULT 25,
    billing_currency CHAR(3) NOT NULL DEFAULT 'USD',
    fx_source VARCHAR(32) NOT NULL DEFAULT 'frankfurter',
    flat_fee_amount NUMERIC(14,2),
    cost_alert_threshold_usd NUMERIC(14,2),
    notes TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.3 Materialized view (Fase 3)

```sql
CREATE MATERIALIZED VIEW mv_daily_llm_cost_per_tenant AS
SELECT
    tenant_id, occurred_on AS day,
    model_responded AS model, provider, role,
    COUNT(*) AS call_count,
    COUNT(DISTINCT turn_id) AS turn_count,
    COUNT(DISTINCT conversation_id) AS conversation_count,
    SUM(input_tokens) AS input_tokens,
    SUM(output_tokens) AS output_tokens,
    SUM(cached_read_tokens) AS cached_read_tokens,
    SUM(cost_usd) AS cost_usd,
    SUM(cost_tenant_currency) AS cost_tenant_currency,
    AVG(duration_ms)::INT AS avg_duration_ms,
    SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS error_count
FROM copilot_llm_call
GROUP BY tenant_id, occurred_on, model_responded, provider, role;

CREATE UNIQUE INDEX ON mv_daily_llm_cost_per_tenant (tenant_id, day, model, provider, role);
```

Refresh: `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_llm_cost_per_tenant` cada hora vía ARQ.

### 4.4 SQL function (Fase 3)

```sql
CREATE OR REPLACE FUNCTION compute_cycle_start(p_tenant UUID, p_date DATE)
RETURNS DATE LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
    anchor SMALLINT;
BEGIN
    SELECT billing_cycle_anchor_day INTO anchor
    FROM tenant_billing_config WHERE tenant_id = p_tenant;
    IF anchor IS NULL THEN anchor := 25; END IF;
    IF EXTRACT(DAY FROM p_date)::SMALLINT >= anchor THEN
        RETURN date_trunc('month', p_date)::DATE + (anchor - 1);
    ELSE
        RETURN (date_trunc('month', p_date) - INTERVAL '1 month')::DATE + (anchor - 1);
    END IF;
END $$;
```

## 5. Código que muere (Fase 2)

| Archivo / símbolo | Razón |
|---|---|
| `application/observability/trace_recorder.py` | Lógica absorbida por `observability/recording/event_store.py` (repo limpio). |
| `application/observability/node_trace.py` | Callback handler emite node events nativamente. |
| `application/orchestrator/usage_tracking.py` (entero) | `UsageAccumulator` + `_PRICING` hardcoded reemplazados por `cost/calculator.py` + `pricing/resolver.py`. |
| `recorder.record(...)` calls en `chat.py` (~10 sitios) | Reemplazadas por callbacks + domain events. Solo quedan `obs.start_turn()` / `obs.end_turn()`. |
| `recorder.record(event_type='card_emitted', ...)` en `extraction_card_flow.py` | Reemplazada por `event_bus.publish(CardEmitted(...))`. |
| Drift `event_type='llm_call'` en docstring migration 059 | Resuelto: ahora se emite de verdad. |

**Métrica de éxito:** `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b"` en backend/src/ → cero matches tras Fase 2.

## 6. Compatibilidad backwards

- Datos históricos en `copilot_trace_event` quedan intactos. Schema sin breaking changes.
- `copilot_conversations.messages` JSONB intacto.
- Streamlit pages `/trazas`, `/copilot-routing`, `/copilot-quality` siguen funcionando durante Fase 2 (leen de `copilot_trace_event` que sigue vivo); en Fase 3 se refactorizan para usar el módulo nuevo cuando aplique.

## 7. Decisiones rechazadas (con razón)

| Opción | Por qué no |
|---|---|
| Adoptar Langfuse self-host | $300+/mes ClickHouse + dep crítica adicional. No justifica vs Postgres+MV para volumen actual. |
| Adoptar LangSmith hosted | Vendor lock + costo per-trace. Pain real es schema, no UI. |
| Migrar a TimescaleDB ya | Premature. Postgres + MV alcanza para <5M calls/mes. |
| OTel collector externo | Capa adicional sin payoff hoy. Schema OTel-shape ya queda compatible para migrar después. |
| Pre-agregar costos al write | Pierde re-cálculo. Event-sourced inmutable. |
| Mantener `UsageAccumulator` aggregator paralelo al callback handler | Frankenstein. Todo flujo de costo pasa por callback handler. |

## 8. Cómo evoluciona sin tocar el módulo

| Cambio en copilot | Acción en obs |
|---|---|
| Tool nuevo | Ninguna. Callbacks lo capturan. |
| Nodo LangGraph nuevo | Ninguna. Callbacks lo capturan. |
| Provider LLM nuevo | Ninguna. PricingResolver lee LiteLLM JSON. |
| Reasoning tokens nuevo bucket | ALTER ADD COLUMN aditivo. |
| Card kind nuevo | Ninguna. `CardEmitted.card_kind` es libre. |
| Pricing change provider | Ninguna. Worker `pricing_sync_task` lo detecta diariamente. |
| Multi-agent / sub-graphs / handoffs | Ninguna. `parent_span_id` ya modela jerarquía. |
| Domain event nuevo (ej. `AgentHandoffOccurred`) | Aditivo: nuevo subscriber en `domain_subscribers.py`. No toca existentes. |

**Lo único que dispara rewrite:** abandonar LangChain/LangGraph entero. Improbable a corto plazo.
