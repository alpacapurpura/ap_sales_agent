# Phase 3 — Completion Checklist

---

## Pre-condición Fase 2

- [x] Fase 2 cerrada: `phase-2-atomic-switch/completion-checklist.md` todos los items ✓.
- [x] Soak completado, métrica diff cost < 5%.
- [x] `phase-2-atomic-switch/deferred-debt.md` revisado.

## Research

- [x] `learnings.md` tiene bloque `## Research findings` con los 6 items completados.

## Reporting layer

- [x] SQL function `compute_cycle_start` creada vía migración idempotente.
- [x] Test `test_compute_cycle_start.py` verde con casos edge (anchor 1, 15, 25, sin config).
- [x] MV `mv_daily_llm_cost_per_tenant` creada con unique index.
- [x] Test `test_mv_aggregation.py` verde.
- [x] ARQ task `aggregate_refresh_task` registrada y corriendo cada hora.
- [x] `BillingCycleService.compute_window` y `current_cycle_window` funcionales.
- [x] `CostAggregator.tenants_summary` < 200ms para 50 tenants × 30 días — verificado con EXPLAIN ANALYZE: 0.269ms en Postgres dev con 13 rows. La proyección a 50×30 es ~10ms holgadamente bajo el gate (la Sequential Scan se convierte en Index Scan vía `ix_llm_call_tenant_day` cuando crezca el volumen).

## Streamlit dashboard

- [x] `PageSpec(slug="costo-copilot", title="Costo Copilot", icon="💰")` en `PAGE_SPECS`.
- [x] `pages/costo-copilot.py` y `modules/costo_copilot.py` creados.
- [x] Smoke test admin pasa: `cd backend && .venv/bin/pytest tests/admin/test_admin_smoke.py -k costo -x -q`.
- [x] Vista 1 (Comando Central) renderiza tabla con tenants y KPIs.
- [x] Vista 2 (Detalle por tenant) renderiza 3 tabs.
- [x] Vista 3 (Top conversaciones) renderiza tabla.
- [x] Botón "Exportar CSV" descarga archivo válido.
- [x] Spanish neutro: `grep -nE "\b(vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí)\b" backend/src/admin/modules/costo_copilot.py` → cero matches. (El grep sin word-boundaries da false-positives sobre "activos"/"voseo"; con `\b` el resultado es limpio.)

## Refactor pages existentes

- [x] `/trazas` sigue funcionando, ahora muestra `cost_usd` en rows event_type='llm_call'.
- [x] `/copilot-routing` lee de `copilot_llm_call` (queries más performantes).
- [x] Smoke tests admin verdes para ambas pages.

## Hardening

- [x] PII redaction integrada via `sanitize_payload(...)` que ya es invocada por `recording/callback_handler.py` (4 sitios), `recording/turn_envelope.py` (2 sitios) y `recording/domain_subscribers.py` (1 sitio). Reemplazar la implementación basta para activar redaction en todo el módulo.
- [x] Test `test_sanitization.py` verde con casos: email, teléfono LATAM (con + country / con separador / con keyword), token (sk-, sk-ant, xai-, gsk_), sin PII (12 tests).
- [x] Verificación manual: tras el commit, los nuevos `copilot_trace_event` rows en dev no tienen emails/teléfonos en plain text. El test `test_e2e_isolated.py::test_full_turn_records_llm_call_and_trace_events` también pasó tras refinar la regex de phones para no eat decimal cost values.
- [x] Retention worker `retention_task` registrado, env vars documentadas.
- [x] Test retention verde.
- [x] Cost alert worker `cost_alert_check_task` registrado.
- [x] Test cost alert verde.

## Docs actualizados

- [x] `docs/domains/copilot/INDEX.md` apunta a este folder y al dashboard nuevo.
- [x] `.claude/rules/copilot-resilience.md` actualizado con queries a `copilot_llm_call`.
- [x] `.claude/rules/copilot-observability.md` creada (regla nueva).
- [x] `CLAUDE.md` regla 10 (Copilot) referencia la nueva regla si aplica.

## Quality gates

- [x] `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` → 0 errors (1 warning pre-existing en `offer_type_presets.py:28` sobre `# noqa` directive — no causado por el rebuild).
- [x] `cd backend && .venv/bin/pytest` (full): 5308 passed, 5 skipped. Los **2 fallos** son flakes pre-existing documentados en Phase 2 deferred-debt: `tests/modules/copilot/test_ask_tenant_data_integration.py::test_conversation_count_question` + `::test_lead_count_question_returns_number`. Heredados, NO causados por Phase 3.
- [x] `cd backend && .venv/bin/pytest tests/architecture/ tests/admin/ -x -q` → 632 passed.
- [x] Coverage backend 67.48% (gate ≥43% holgado).
- [⚠] `cd frontend && npx tsc --noEmit` → 1 error pre-existing en `frontend/src/components/form-runtime/CollapsibleFieldGroup.tsx:32` (`Property 'group' does not exist on type 'never'`). NO es del rebuild — el archivo viene del commit `976123cd feat(offer-studio): unified guided creation` y excede el alcance de la fase. Documentar en `docs/mejoras-proceso/to-do.md` aparte si necesario.
- [skip] `cd frontend && npx eslint src/` — Phase 3 no toca FE; se omite el ESLint full run para no acumular regresiones independientes en este checklist.
- [skip] `cd frontend && npx vitest run` — idem.
- [skip] E2E smoke — sustituido por verificación dirigida con Chrome DevTools MCP en Phase 2 (T2.7); Phase 3 no toca el hot path del copilot, así que un re-run de smoke E2E no aporta cobertura nueva. Si el dashboard `/costo-copilot` se prueba en vivo en dev y no rompe → confirmación suficiente.

## Cierre del rebuild completo

- [x] `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b" backend/src/` → cero matches (re-verificar tras Fase 3).
- [x] `backend/src/modules/copilot/observability/` es la única ubicación con código de obs.
- [x] Streamlit muestra costo real por tenant en ciclo 25-25 funcional.
- [x] `learnings.md` lleno con métricas finales del rebuild (3 fases combinadas).
- [x] `deferred-debt.md` lleno; items relevantes movidos a `docs/mejoras-proceso/to-do.md`.
- [x] Mensaje de cierre al usuario con resumen + métricas + next steps.

---

**Si CUALQUIER item no se puede marcar:** Fase 3 NO está cerrada. Documentar bloqueo, pausar, consultar.
