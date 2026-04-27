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

> COMPLETAR.

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
