# S2 · Cost guardrails + cycle 25-25 cross-agent

## Objetivo

Extender `BillingCycleService`, `CostAggregator`, MV diaria, retention worker y cost alerts para incluir `agent_kind`. Streamlit admin `/costo-copilot` evoluciona a `/costo-agentes` con drill-down. Sales_agent es el módulo más caro en LLM — necesita visibilidad y guardrails.

## Dependencias

- S1 cerrado: `sales_agent_llm_call` poblado con `cost_usd` + `pricing_version_id`.

## Criterios de éxito

1. MV `mv_daily_llm_cost_per_tenant` extendida con columna `agent_kind` (UNION ALL de copilot+sales_agent).
2. `CostAggregator.aggregate(tenant_id, agent_kind=None)` — None = cross-agent total.
3. `BillingCycleService.cycle_cost(tenant_id, agent_kind=None)` — filtrable.
4. `tenant_billing_config.threshold_usd` aplica cross-agent (sin breakdown). Alert dispara cuando suma > threshold.
5. Streamlit `/costo-agentes` (rename/extend) con tabs:
   - Total (cross-agent)
   - Copilot
   - Sales Agent (con drill-down por lead/channel)
6. Retention worker corre para `sales_agent_trace_event` (90d) y `sales_agent_llm_call` (365d). Configurable via env.
7. Quality gates verdes.

## Research mandate

### Queries WebSearch obligatorias

1. `Postgres materialized view UNION ALL refresh CONCURRENTLY 2026` — performance al combinar tablas con índices distintos.
2. `cost alert threshold multi-product SaaS billing dashboard` — UX de drill-down + alerts.
3. `LangChain LiteLLM pricing audit log retention compliance 2026` — duración legal mínima.

### Tessl tiles

- N/A primaria. Si query identifica librería de billing → instalar.

### Lectura obligatoria

- `learnings/S1-*.md`.
- `backend/src/shared/agent_observability/reporting/billing_cycle_service.py` (post-S0).
- `backend/src/shared/agent_observability/reporting/cost_aggregator.py`.
- `backend/src/shared/agent_observability/workers/aggregate_refresh_task.py`.
- `backend/src/shared/agent_observability/workers/retention_task.py`.
- `backend/src/admin/modules/copilot_costs.py` o equivalente Streamlit existente.

### Hallazgos research

#### Q1 — Postgres MV UNION ALL + REFRESH CONCURRENTLY (2026)

- `REFRESH MATERIALIZED VIEW CONCURRENTLY` exige **UNIQUE index** sobre el MV. Columnas únicamente (no expresiones, no WHERE, includes all rows). Sin él Postgres no puede diff row-by-row.
- Mecánica: ejecuta SELECT del MV en staging, hace `FULL OUTER JOIN` contra tabla actual, aplica INSERT/DELETE/UPDATE incremental. Reads no se bloquean.
- **Trampa nullable**: si una columna del unique index es nullable, `NULL = NULL` evalúa a NULL → toda fila parece distinta y el refresh se vuelve full rewrite. **Mitigación**: declarar `agent_kind`/`tenant_id`/`occurred_on` como NOT NULL en MV (UNION ALL los garantiza si los inputs lo son).
- UNION ALL combinando 2 tablas con índices distintos funciona; refresh recalcula ambas branches. Sin issue con esta arquitectura siempre que ambas tablas tengan índice por `(tenant_id, occurred_on)` (S1 ya creó esos).
- Fuentes: PostgreSQL 18 docs `sql-refreshmaterializedview`, Crunchy Data Indexing MVs.

#### Q2 — Cost alert UX multi-product SaaS (2026)

- Best practice = **breakdown por producto/agente** en notificación + threshold cross-producto. Pattern Finout (multi-cloud aggregation) y Zluri (budget thresholds): un threshold único + email/slack que muestra qué línea consumió cuánto.
- "Bill shock" prevention: alert con drilldown explícito reduce time-to-action vs alert agregado opaco.
- Decisión: cross-agent threshold único por tenant (`tenant_billing_config.cost_alert_threshold_usd`). Si total cross-agent > threshold → structlog warning con breakdown `{copilot: $X, sales_agent: $Y}`. NO doble threshold per agent (overhead config + risk drift).
- Fuentes: Schematic (Usage-Based Billing 2026), Zluri (SaaS spend management).

#### Q3 — LiteLLM tier pricing (2026)

- Schema soporta `input_cost_per_token_above_200k_tokens` + `output_cost_per_token_above_200k_tokens` + `cache_creation_input_token_cost_above_200k_tokens` + `cache_read_input_token_cost_above_200k_token`. Aplica cuando contexto > 200k.
- Modelos sales_agent (Kimi K2.6, DeepSeek-V4, Claude Opus 200k) pueden caer en tier alto durante long conversations.
- **Decisión S2**: NO implementar tier pricing en `calculate_cost` shared. Postpone a fase futura cuando emerja real cost inflation (>5% drift entre cost_usd grabado y reconciliation con LiteLLM). DEFERRED-post-S6 con flag para escalar a calculator.
- Fuentes: BerriAI/litellm `model_prices_and_context_window.json`, LiteLLM Cost Calculation docs.

#### Q4 — PII async post-write workers (extra)

- Presidio + spaCy NER agrega ~50-200ms latency. Demasiado para hot path callback handler (target <10ms p99).
- Pattern correcto: regex-only síncrono (lo que ya tenemos en `sanitization.py` post-S1) + worker async post-write con Presidio que re-redacta payloads con PII no detectada por regex (nombres, organizaciones).
- DEFERRED-post-S6: `pii_async_audit_task.py` que lee batches de `*_trace_event`/`*_llm_call`, corre Presidio, UPDATE row si encuentra PII no enmascarada. Compliance opcional para tenants enterprise.
- Fuentes: oneuptime LLMOps PII Detection 2026, IJC Safe Observability paper, microsoft/presidio.

### Decisiones de diseño S2 (post-research)

- **CostAggregator parametrizado por model class** (no SQL hardcoded). Constructor toma `(db, llm_call_model)`. Factory `for_copilot(db)` / `for_sales_agent(db)`.
- **`CrossAgentCostAggregator`** compone N CostAggregator instances (uno por agent_kind del registry). Suma rows en Python (datasets pequeños — ~100s de tenants). Evita SQL UNION cross-table en service layer; el MV `mv_daily_v2` cubre el caso "performance dashboard".
- **`AgentObservabilityRegistry`** en `shared/agent_observability/` lista `[(agent_kind, llm_call_model, trace_event_table_name, llm_call_table_name)]`. Single source para workers + aggregator + cost_alert.
- **`aggregate_refresh_task`**: refresh ambas MVs (`mv_daily_llm_cost_per_tenant` legacy + `mv_daily_llm_cost_per_tenant_v2` nueva). Best-effort independiente por MV. Vieja se mantiene por 1 release para no romper consumers externos.
- **`retention_task`**: itera registry list `[(table, env_var, default_days, preserve_errors)]`. Cada DELETE bounded por índice de cada tabla. Best-effort — fallo en una no aborta las otras.
- **`cost_alert_service`**: usa `CrossAgentCostAggregator`. Iter `tenant_billing_config WHERE threshold IS NOT NULL`. Suma cross-agent → si > threshold emit structlog `cost_alert_threshold_exceeded` con `breakdown={agent_kind: cost_usd}`.
- **Streamlit**: page nuevo `costo-agentes`. Tabs: **Total** (cross-agent) / **Copilot** (link al viejo `costo-copilot` o ataja a aggregator copilot) / **Sales Agent** (drilldown por lead vía `top_leads_by_cost`).
- **`top_leads_by_cost`** análogo a `top_conversations_by_cost` pero filtrando `lead_id IS NOT NULL` (sales_agent específico). Vive como method del aggregator parametrizado solo cuando el model expone `lead_id`.

---

## Diseño

### MV cross-agent

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_llm_cost_per_tenant_v2 AS
SELECT
    'copilot' AS agent_kind,
    tenant_id,
    occurred_on,
    SUM(cost_usd) AS cost_usd,
    COUNT(*) AS calls,
    COUNT(DISTINCT turn_id) AS turns
FROM copilot_llm_call
GROUP BY tenant_id, occurred_on
UNION ALL
SELECT
    'sales_agent',
    tenant_id,
    occurred_on,
    SUM(cost_usd),
    COUNT(*),
    COUNT(DISTINCT turn_id)
FROM sales_agent_llm_call
GROUP BY tenant_id, occurred_on;

CREATE UNIQUE INDEX ix_mv_daily_v2 ON mv_daily_llm_cost_per_tenant_v2(agent_kind, tenant_id, occurred_on);
```

Refresh `CONCURRENTLY` requiere unique index.

### `CostAggregator.aggregate`

```python
async def aggregate(
    self,
    tenant_id: UUID,
    cycle_start: date,
    cycle_end: date,
    agent_kind: Literal["copilot", "sales_agent"] | None = None,
) -> CostBreakdown:
    """None = cross-agent total. Específico = filtrar."""
```

### Streamlit `/costo-agentes`

Pages registry (`.claude/rules/admin-panel.md`):
```python
PageSpec(slug="costo-agentes", title="Costo Agentes", icon="dollar-sign"),
```

Tabs Streamlit:
- **Total**: barra apilada por día; agent_kind como hue.
- **Copilot**: igual a `/costo-copilot` actual.
- **Sales Agent**: agregaciones nuevas — top leads costosos, costo per channel, costo per stage.

### Cost alert evolución

```python
# src/shared/agent_observability/application/cost_alert_service.py
async def run_cost_alerts():
    for tenant in tenants_with_threshold:
        cycle_cost = await aggregator.aggregate(
            tenant.id, cycle_start, cycle_end, agent_kind=None,
        )
        if cycle_cost.total > tenant.threshold_usd:
            send_alert(tenant, breakdown=cycle_cost.by_agent)
```

Alert email muestra breakdown:
```
Tenant X excedió threshold $50:
- Copilot: $12.30
- Sales Agent: $43.10
Total: $55.40
```

---

## Plan TDD

### RED tests

1. `tests/shared/agent_observability/test_cost_aggregator_cross_agent.py`:
   - `aggregate(agent_kind=None)` suma copilot + sales_agent.
   - `aggregate(agent_kind="sales_agent")` filtra correcto.
   - Tenant sin sales_agent rows: aggregator devuelve 0 sin error.

2. `tests/shared/agent_observability/test_mv_concurrent_refresh.py`:
   - Refresh CONCURRENTLY no bloquea reads.
   - Unique index presente.

3. `tests/modules/admin/test_costo_agentes_page.py`:
   - Streamlit AppTest renderiza sin exception.
   - Tabs presentes.

4. `tests/shared/agent_observability/test_cost_alert_breakdown.py`:
   - Alert email contiene breakdown por agent_kind.

5. `tests/architecture/test_retention_task_parametrized.py`:
   - `retention_task` corre para ambas tablas con días distintos.

---

## Implementación step-by-step

1. Migración Alembic: nueva MV (drop+create vs ALTER incompatible). Idempotente.
2. `CostAggregator.aggregate` extender signature.
3. `BillingCycleService.cycle_cost` extender.
4. Streamlit page nuevo + registry.
5. Cost alert: breakdown en email template.
6. Retention worker: extender ARQ cron para sales_agent.
7. Verificar performance MV con `EXPLAIN ANALYZE` post-refresh (target <500ms).

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| MV refresh CONCURRENTLY falla | Tener unique index. Test en clone DB. |
| Drift MV vs tablas tras migration | Refresh manual post-deploy. Cron hourly. |
| Streamlit page rompe smoke admin | Test `tests/admin/test_admin_smoke.py` cubre nuevo page. |
| Cost alert email floods | Throttle 1 alert por tenant per cycle. Test idempotencia. |

---

## Tech debt watchpoints

- Si pricing snapshots viejos no tienen `pricing_version_id` correcto en sales_agent_llm_call → mark as suspect, NO usar para billing real hasta backfill.
- Si Streamlit `/costo-copilot` tiene queries hardcoded → refactor a service layer (alta cohesión).
- Si email templates están hardcoded en cost_alert_service → mover a `templates/` y i18n.

---

## Ajustes vs plan original

> COMPLETAR.
