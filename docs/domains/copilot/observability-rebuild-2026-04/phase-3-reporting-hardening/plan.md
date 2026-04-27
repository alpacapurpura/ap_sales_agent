# Phase 3 — Reporting + Hardening

**Objetivo:** entregar el dashboard de costo por tenant en Streamlit (objetivo de negocio) + cerrar deuda técnica (PII, retention, alertas). Refactorizar `/trazas` y `/copilot-routing` para que lean del módulo nuevo cuando aplique.

**Riesgo al copilot:** bajo (refactor de admin pages + workers, no toca hot path).

**Duración estimada:** 2 días.

**Pre-condición:** Fase 2 cerrada. Soak completado. `copilot_llm_call` poblada con datos reales de varios días.

---

## Tasks

### T3.1 — Research checklist

Ejecutar `research-checklist.md`. ~20 min.

---

### T3.2 — SQL function `compute_cycle_start`

**Acción:** migración Alembic (idempotente):

```sql
CREATE OR REPLACE FUNCTION compute_cycle_start(p_tenant UUID, p_date DATE)
RETURNS DATE LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE anchor SMALLINT;
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

**Tests primero:**
- `test_compute_cycle_start.py` (en `tests/modules/copilot/observability/reporting/`):
  - tenant con anchor 25, date=2026-04-26 → 2026-04-25
  - tenant con anchor 25, date=2026-04-24 → 2026-03-25
  - tenant sin config (anchor default 25) → 2026-04-25 si date >= 25
  - anchor 1, date=2026-04-15 → 2026-04-01
  - anchor 15, date=2026-04-14 → 2026-03-15

**Criterio aceptación:** tests verdes, función disponible en DB.

---

### T3.3 — Materialized view `mv_daily_llm_cost_per_tenant`

**Acción:** migración crea MV (schema en `ARCHITECTURE.md` §4.3) + unique index.

**Tests primero:**
- `test_mv_aggregation.py`:
  - Insertar rows sintéticas en `copilot_llm_call`.
  - `REFRESH MATERIALIZED VIEW mv_daily_llm_cost_per_tenant`.
  - Verificar agregaciones correctas.

**Criterio aceptación:** tests verdes, MV creada.

---

### T3.4 — `aggregate_refresh_task` ARQ worker

**Acción:** completar esqueleto de Fase 1.
- Cron hourly: `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_llm_cost_per_tenant`.
- Logs structlog: `mv_aggregate_refresh_complete duration_ms=...`.

**Tests primero:** `test_aggregate_refresh.py` — invoca task, verifica refresh completa.

**Criterio aceptación:** tests verdes, task registrada en `backend/src/workers/settings.py`.

---

### T3.5 — `BillingCycleService` + `CostAggregator`

**Acción:**
- `reporting/billing_cycle_service.py`:
  - `compute_window(tenant_id, target_date) -> tuple[date, date]` → (start, end_exclusive). Llama a SQL function.
  - `current_cycle_window(tenant_id) -> tuple[date, date]` → con today.
  - `previous_cycle_window(tenant_id) -> tuple[date, date]`.
- `reporting/cost_aggregator.py`:
  - `tenants_summary(target_date) -> list[TenantCostRow]` (todos los tenants en el ciclo del target_date).
  - `tenant_detail(tenant_id, start, end) -> TenantDetailRow` (con breakdown por modelo, días, conversaciones).
  - `top_conversations_by_cost(tenant_id, start, end, limit=20) -> list[ConversationCostRow]`.
  - `daily_series(tenant_id, days=60) -> list[DailyCostPoint]`.

**Tests primero:**
- `test_billing_cycle_service.py` — windows correctas para ciclo actual, anterior, edge cases.
- `test_cost_aggregator.py` — fixtures con tenants/calls sintéticos, queries devuelven shapes esperados.

**Criterio aceptación:** tests verdes. Performance: `tenants_summary` < 200ms para 50 tenants × 30 días de data.

---

### T3.6 — Streamlit page `costo-copilot`

**Acción:**
1. Crear `backend/src/admin/modules/costo_copilot.py` con `render_costo_copilot()`.
2. Crear `backend/src/admin/pages/costo-copilot.py` (wrapper, una sola línea).
3. Append `PageSpec(slug="costo-copilot", title="Costo Copilot", icon="💰")` en `PAGE_SPECS` de `app.py`.
4. Smoke test en `tests/admin/test_admin_smoke.py` (regla `admin-panel.md`).

**Layout en español neutro LatAm (sin voseo):**

**Vista 1 — Comando Central (default):**
- Selector ciclo: `<25 mar – 25 abr>` con flechas para ciclos pasados/proyectado.
- KPIs row: tenants activos, total LLM cost USD, conversations, turns, calls, avg cost/turn.
- Tabla por tenant: tenant, conversations, turns, calls, $USD, $local, %flat_fee. Sortable. Filtrable.
- Botones: `Exportar CSV`, `Refresh`.

**Vista 2 — Detalle por tenant:**
- Selector tenant (dropdown).
- 3 tabs:
  - **Resumen ciclo**: total + delta vs ciclo anterior + proyección.
  - **Series temporales**: line chart costo USD diario últimos 60 días (Plotly). Stacked bar por modelo.
  - **Breakdown por modelo**: pie chart cost USD por (provider, model_responded, role). Tabla con avg input/output tokens, cache_hit_rate, error_count.

**Vista 3 — Top conversaciones costosas (drill-down):**
- Top 20 conversations del ciclo actual ordenadas por cost desc.
- Click → link a `/trazas?conversation_id=...`.

**Tests primero:** smoke test que la página renderiza sin exception headless.

**Criterio aceptación:**
- Page accesible en admin.
- Smoke test verde.
- Spanish neutro (verificar con grep voseo: `grep -nE "vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí" backend/src/admin/modules/costo_copilot.py` → cero matches).

---

### T3.7 — Refactor `/trazas` y `/copilot-routing`

**Acción:**
- `backend/src/admin/modules/trazas.py`:
  - Si actualmente lee solo de `copilot_trace_event` con event_type='llm_call' que ahora existe → debería seguir funcionando.
  - Mejora: agregar columna "cost_usd" al timeline cuando event_type='llm_call' (lee de `copilot_llm_call.cost_usd` joined por span_id).
  - Mejora: filtro "solo llm_call" o "solo tool_call".
- `backend/src/admin/modules/copilot_routing.py`:
  - Si lee `data->>'cost_usd'` del JSONB de `turn_end` → cambiar a query directa de `copilot_llm_call` agregada (más performante).
  - Mantener compat de UI.

**Tests:** smoke + asserción manual de funcionamiento.

**Criterio aceptación:** ambas pages funcionan + leen del módulo nuevo cuando aplica.

---

### T3.8 — PII redaction (Presidio + regex)

**Acción:**
- `recording/sanitization.py` (creado en Fase 1, ahora se completa):
  - `redact_payload(payload: dict) -> dict`: aplica regex (emails, teléfonos LatAm, IDs) **síncrono** antes de truncate. NO aplica Presidio sincrónico (overhead).
  - Worker async opcional `pii_post_redaction_task` que re-procesa rows sospechosas con Presidio → en deferred-debt si no llega.
- Integrar en `event_store.py` (repositorio que escribe `copilot_trace_event`) y en `LlmCallRepository.add` para campos `data` y `args`/`output_preview`.

**Tests primero:**
- `test_sanitization.py`:
  - Email `juan@ejemplo.com` → `j***@ejemplo.com`.
  - Teléfono `+51 999 888 777` → `+51 *** *** ***`.
  - Token `sk-abc123...` → `[REDACTED_TOKEN]`.
  - String sin PII → intacto.

**Criterio aceptación:** tests verdes. Payloads en DB sin PII en muestreo manual.

---

### T3.9 — Retention worker

**Acción:** completar esqueleto Fase 1.
- `workers/retention_task.py`:
  - Cron daily 04:00 UTC.
  - Política: `DELETE FROM copilot_trace_event WHERE created_at < NOW() - interval '90 days' AND status != 'error'`.
  - `DELETE FROM copilot_llm_call WHERE created_at < NOW() - interval '365 days'` (mayor retención para auditoría billing).
  - Configurable via env vars `COPILOT_TRACE_RETENTION_DAYS=90`, `COPILOT_LLM_CALL_RETENTION_DAYS=365`.
  - Logs structlog con counts.

**Tests primero:** `test_retention.py` — fixture rows viejas, ejecutar task, verificar deletion respetando filtros.

**Criterio aceptación:** tests verdes, task registrada.

---

### T3.10 — Alertas de costo

**Acción:**
- ARQ task `cost_alert_check_task` (cron daily 09:00 local time del tenant — para v1 simple: 12:00 UTC):
  - Para cada tenant en `tenant_billing_config` con `cost_alert_threshold_usd` definido:
    - Calcular cost del ciclo actual (`SUM(cost_usd)` con window de cycle).
    - Si > threshold → emitir log warn + (opcional v2) email/Slack.
  - Logs structlog.

**Tests primero:** `test_cost_alert.py` — fixture tenants, cost > threshold, verifica warning.

**Criterio aceptación:** tests verdes. Email/Slack puede quedar a deferred-debt si no hay infra ya.

---

### T3.11 — Export CSV

**Acción:** botón en Streamlit "Exportar CSV ciclo actual" → genera CSV con una row por tenant (cycle_start, cycle_end, conversations, turns, calls, cost_usd, cost_local, currency, flat_fee, pct_used).

`pandas.DataFrame(...).to_csv(index=False)` + `st.download_button`.

**Tests:** smoke (botón existe). Manual verificar CSV abre en Excel.

**Criterio aceptación:** botón funcional.

---

### T3.12 — Update docs

**Acción:**
1. `docs/domains/copilot/INDEX.md` — agregar entrada al rebuild folder + dashboard `costo-copilot`.
2. `.claude/rules/copilot-resilience.md` — actualizar sección "Debug copilot" con queries a `copilot_llm_call` en lugar/además de `copilot_trace_event` JSONB. Mencionar que cost+model están en columnas tipadas, no JSONB.
3. Crear `.claude/rules/copilot-observability.md` (regla nueva):
   - Cómo agregar nuevo domain event.
   - Cómo agregar provider LLM nuevo (auto cubierto por LiteLLM sync, pero documentar workflow si no aparece).
   - Cómo modificar pricing manual (insert en `model_pricing_snapshot` con `source='manual'`).
   - Retention policy.
   - PII redaction policy.
4. Update `CLAUDE.md` regla 10 "Copilot" si aplica (apuntar a la nueva regla).

**Criterio aceptación:** docs actualizados. INDEX.md rinde correcto.

---

### T3.13 — Quality gates finales

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd backend && .venv/bin/pytest tests/admin/ tests/architecture/test_admin_panel.py -x -q
cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q
```

E2E + frontend:
```bash
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

**Criterio aceptación:** todo verde.

---

### T3.14 — Cerrar fase + cierre del rebuild

1. Llenar `learnings.md`.
2. Llenar `deferred-debt.md` (estos items no van a "Fase 4" — van a `docs/mejoras-proceso/to-do.md`).
3. Verificar `completion-checklist.md`.
4. Commit final docs.
5. Mensaje de cierre al usuario:
   - Resumen del rebuild completo.
   - Métricas: archivos eliminados, líneas, commits.
   - Link al dashboard nuevo.
   - Items en deferred-debt que necesitan seguimiento.

---

## Commits sugeridos

1. `feat(copilot-obs): add billing cycle SQL function + tests` (T3.2)
2. `feat(copilot-obs): add daily cost MV + aggregate refresh worker` (T3.3 + T3.4)
3. `feat(copilot-obs): add billing cycle service + cost aggregator` (T3.5)
4. `feat(copilot-obs): add Streamlit costo-copilot dashboard` (T3.6)
5. `refactor(copilot-obs): trazas + copilot-routing read from new module` (T3.7)
6. `feat(copilot-obs): add PII redaction (regex) at recorder` (T3.8)
7. `feat(copilot-obs): add retention worker with configurable policy` (T3.9)
8. `feat(copilot-obs): add cost alert worker per tenant threshold` (T3.10)
9. `feat(copilot-obs): add CSV export for billing cycle` (T3.11)
10. `docs(copilot-obs): update INDEX, copilot-resilience, add observability rule` (T3.12)
11. `docs(copilot-obs): close phase 3 — fill learnings + deferred-debt` (T3.14)
