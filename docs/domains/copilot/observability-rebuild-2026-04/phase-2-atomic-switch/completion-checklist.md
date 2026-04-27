# Phase 2 — Completion Checklist

Marcar cada item solo con evidencia. No marcar por fe.

---

## Pre-condición Fase 1

- [ ] Fase 1 cerrada: `phase-1-foundation/completion-checklist.md` todos los items ✓.
- [ ] `phase-1-foundation/deferred-debt.md` revisado — items de Fase 2 incorporados al plan de esta fase si aplica.

## Research

- [ ] `learnings.md` tiene bloque `## Research findings` con los 6 items completados.
- [ ] Sesiones paralelas chequeadas (`git status` + `git log`). chat.py / extraction_card_flow.py libres de WIP ajeno.
- [ ] Si hubo cambios al diseño, fueron consultados al usuario.

## Event bus + domain events

- [ ] Event bus en `backend/src/shared/events/event_bus.py` funcional (creado o verificado existente).
- [ ] `tests/shared/events/test_event_bus.py` verde.
- [ ] `backend/src/modules/copilot/domain/events.py` tiene `TurnStarted`, `TurnEnded`, `CardEmitted`, `RoutingDecided` definidos como `@dataclass(frozen=True)`.
- [ ] `tests/modules/copilot/domain/test_events.py` verde.
- [ ] `register_subscribers` invocado desde `backend/src/main.py` lifespan startup.
- [ ] Test `test_register.py` verde.

## Switch atómico — el commit

- [ ] **Un solo commit** contiene: cambios en `chat.py` + `extraction_card_flow.py` + deletion de `trace_recorder.py` + `usage_tracking.py` + `node_trace.py`.
- [ ] `git show <hash> --stat` muestra deletions (no solo modifications).
- [ ] `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b" backend/src/` → cero matches.
- [ ] `git grep "from src.modules.copilot.application.observability.trace_recorder" backend/src/` → cero matches.
- [ ] `git grep "from src.modules.copilot.application.orchestrator.usage_tracking" backend/src/` → cero matches.
- [ ] `git grep "from src.modules.copilot.application.observability.node_trace" backend/src/` → cero matches.
- [ ] Test `test_atomic_switch.py` verde.

## Compatibilidad UI vieja

- [ ] Subscriber `TurnEnded` agrega summary al JSONB `data` del row `turn_end` con shape: `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_input_tokens`, `cache_hit_rate`, `cost_usd`, `response_length`, `message_count`, `block_count`.
- [ ] Streamlit `/trazas` y `/copilot-routing` siguen funcionando sin cambios (verificación manual: abrir admin en dev, navegar las dos páginas, verificar que muestran turnos del último día).

## Feature flag rollback (temporal)

- [ ] `COPILOT_OBS_REBUILD_DISABLED` env var implementada.
- [ ] `.env.example` actualizada.
- [ ] Test `test_disabled_flag.py` verde.
- [ ] Plan de borrado documentado en `learnings.md` con fecha objetivo.

## Soak en dev

- [ ] 24-48h transcurridas en dev environment con flag en default (rebuild activo).
- [ ] `docker logs visionarias_brain_dev --tail 500 | grep -i "trace_event_write_failed\|llm_call_write_failed"` → cero o niveles aceptables.
- [ ] `SELECT COUNT(*) FROM copilot_llm_call WHERE created_at > NOW() - interval '24 hours';` → > 0 y proporcional a turns.
- [ ] `SELECT COUNT(*) FROM copilot_trace_event WHERE event_type='llm_call' AND created_at > NOW() - interval '24 hours';` → > 0.
- [ ] Diff cost agregado por turn entre `copilot_llm_call.SUM(cost_usd)` y `copilot_trace_event.turn_end.data->>'cost_usd'` < 5%.

## Borrado del feature flag

- [ ] Commit `chore(copilot-obs): remove temporary rollback flag` aplicado tras soak.
- [ ] Env var, código del flag, y test del flag → eliminados.
- [ ] Tests pasan sin el flag.

## Quality gates

- [ ] `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` → 0 errors.
- [ ] `cd backend && .venv/bin/ruff format --check src/ tests/` → clean.
- [ ] `cd backend && .venv/bin/pytest -x -q --tb=short` → todos verdes.
- [ ] `cd backend && .venv/bin/pytest tests/architecture/ -x -q` → todos verdes.
- [ ] Coverage backend: `cd backend && .venv/bin/pytest --cov=... -q` → ≥43%.
- [ ] E2E smoke: `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke` verde.

## Hot path consistency

- [ ] `chat.py` post-switch tiene **a lo sumo 2 imports** del módulo obs (`ObservabilityContext`) + imports de domain events. NO importa repos, callback handlers, etc.
- [ ] `extraction_card_flow.py` post-switch publica `CardEmitted` event, sin import directo a obs.
- [ ] `chat.py` no tiene ninguna llamada `recorder.record(...)`. Verificar grep.

## Docs cerradas

- [ ] `learnings.md` lleno (con decisiones de research + ejecución).
- [ ] `deferred-debt.md` lleno.
- [ ] Commit final docs.
- [ ] Status entrega prompt de `handoff-prompts/start-phase-3.md` al usuario.

---

**Si CUALQUIER item no se puede marcar:** Fase 2 NO está cerrada. El switch atómico es el item de mayor riesgo del rebuild — si quedó algo sin terminar, **pausar y consultar**, no avanzar a Fase 3.
