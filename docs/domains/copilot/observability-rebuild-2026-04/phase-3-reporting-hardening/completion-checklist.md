# Phase 3 — Completion Checklist

---

## Pre-condición Fase 2

- [ ] Fase 2 cerrada: `phase-2-atomic-switch/completion-checklist.md` todos los items ✓.
- [ ] Soak completado, métrica diff cost < 5%.
- [ ] `phase-2-atomic-switch/deferred-debt.md` revisado.

## Research

- [ ] `learnings.md` tiene bloque `## Research findings` con los 6 items completados.

## Reporting layer

- [ ] SQL function `compute_cycle_start` creada vía migración idempotente.
- [ ] Test `test_compute_cycle_start.py` verde con casos edge (anchor 1, 15, 25, sin config).
- [ ] MV `mv_daily_llm_cost_per_tenant` creada con unique index.
- [ ] Test `test_mv_aggregation.py` verde.
- [ ] ARQ task `aggregate_refresh_task` registrada y corriendo cada hora.
- [ ] `BillingCycleService.compute_window` y `current_cycle_window` funcionales.
- [ ] `CostAggregator.tenants_summary` < 200ms para 50 tenants × 30 días.

## Streamlit dashboard

- [ ] `PageSpec(slug="costo-copilot", title="Costo Copilot", icon="💰")` en `PAGE_SPECS`.
- [ ] `pages/costo-copilot.py` y `modules/costo_copilot.py` creados.
- [ ] Smoke test admin pasa: `cd backend && .venv/bin/pytest tests/admin/test_admin_smoke.py -k costo -x -q`.
- [ ] Vista 1 (Comando Central) renderiza tabla con tenants y KPIs.
- [ ] Vista 2 (Detalle por tenant) renderiza 3 tabs.
- [ ] Vista 3 (Top conversaciones) renderiza tabla.
- [ ] Botón "Exportar CSV" descarga archivo válido.
- [ ] Spanish neutro: `grep -nE "vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí" backend/src/admin/modules/costo_copilot.py` → cero matches.

## Refactor pages existentes

- [ ] `/trazas` sigue funcionando, ahora muestra `cost_usd` en rows event_type='llm_call'.
- [ ] `/copilot-routing` lee de `copilot_llm_call` (queries más performantes).
- [ ] Smoke tests admin verdes para ambas pages.

## Hardening

- [ ] PII redaction integrada en `event_store` y `LlmCallRepository`.
- [ ] Test `test_sanitization.py` verde con casos: email, teléfono LatAm, token, sin PII.
- [ ] Verificación manual: `SELECT data FROM copilot_trace_event WHERE created_at > NOW() - interval '1 hour' LIMIT 20;` → no hay emails/teléfonos en plain text.
- [ ] Retention worker `retention_task` registrado, env vars documentadas.
- [ ] Test retention verde.
- [ ] Cost alert worker `cost_alert_check_task` registrado.
- [ ] Test cost alert verde.

## Docs actualizados

- [ ] `docs/domains/copilot/INDEX.md` apunta a este folder y al dashboard nuevo.
- [ ] `.claude/rules/copilot-resilience.md` actualizado con queries a `copilot_llm_call`.
- [ ] `.claude/rules/copilot-observability.md` creada (regla nueva).
- [ ] `CLAUDE.md` regla 10 (Copilot) referencia la nueva regla si aplica.

## Quality gates

- [ ] `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` → 0 errors.
- [ ] `cd backend && .venv/bin/pytest -x -q --tb=short` → todos verdes.
- [ ] `cd backend && .venv/bin/pytest tests/architecture/ tests/admin/ -x -q` → todos verdes.
- [ ] Coverage backend ≥43%.
- [ ] `cd frontend && npx tsc --noEmit` → 0 errors.
- [ ] `cd frontend && npx eslint src/` → 0 errors.
- [ ] `cd frontend && npx vitest run` → verde.
- [ ] E2E smoke verde.

## Cierre del rebuild completo

- [ ] `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b" backend/src/` → cero matches (re-verificar tras Fase 3).
- [ ] `backend/src/modules/copilot/observability/` es la única ubicación con código de obs.
- [ ] Streamlit muestra costo real por tenant en ciclo 25-25 funcional.
- [ ] `learnings.md` lleno con métricas finales del rebuild (3 fases combinadas).
- [ ] `deferred-debt.md` lleno; items relevantes movidos a `docs/mejoras-proceso/to-do.md`.
- [ ] Mensaje de cierre al usuario con resumen + métricas + next steps.

---

**Si CUALQUIER item no se puede marcar:** Fase 3 NO está cerrada. Documentar bloqueo, pausar, consultar.
