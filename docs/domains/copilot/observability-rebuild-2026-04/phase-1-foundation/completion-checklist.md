# Phase 1 — Completion Checklist

Marcar cada item solo con evidencia (comando + output, o referencia a test/commit). No marcar por fe.

---

## Research

- [ ] `learnings.md` tiene bloque `## Research findings` con los 5 items completados.
- [ ] Si hubo cambios al diseño, fueron consultados al usuario y anotados en `learnings.md`.

## Estructura

- [ ] `backend/src/modules/copilot/observability/` existe con todas las subcarpetas listadas en `plan.md` T1.1.
- [ ] `pytest tests/architecture/test_folder_naming.py -x -q` pasa.
- [ ] `pytest tests/architecture/test_ddd_boundaries.py -x -q` pasa (cero nuevos cross-module imports).

## DB

- [ ] Migración corre limpio: `docker exec -t visionarias_brain_dev bash -c 'cd /app && alembic upgrade head'`.
- [ ] `\d copilot_llm_call`, `\d model_pricing_snapshot`, `\d tenant_billing_config` muestran columnas e índices esperados.
- [ ] Re-run `alembic upgrade head` no falla (idempotencia).
- [ ] Test `test_migration_schema.py` verde.

## Models + Repositorios

- [ ] `test_models.py` verde.
- [ ] `test_repositories.py` verde.
- [ ] Cada query de cada repo filtra `tenant_id` (donde aplica). Verificar con grep.

## Pricing + Cost + FX

- [ ] `test_pricing_resolver.py` verde.
- [ ] `test_litellm_sync.py` verde.
- [ ] `test_cost_calculator.py` verde.
- [ ] `test_fx_resolver.py` verde.
- [ ] Smoke manual: `sync_pricing` corrido y `model_pricing_snapshot` tiene ≥50 entries con providers diversos (no solo OpenAI).
  - Comando smoke: `cd backend && .venv/bin/python -m src.modules.copilot.observability.workers.pricing_sync_task` (o equivalente per implementación).
  - Output esperado: `pricing_sync_complete rows_added=N rows_updated=M`.

## Callback Handler + Turn Envelope

- [ ] `test_callback_handler.py` verde.
- [ ] `test_turn_envelope.py` verde.
- [ ] `test_domain_subscribers.py` verde.
- [ ] Verificación de no-conexión: `git grep "ObservabilityCallbackHandler\|ObservabilityContext\|register_subscribers" backend/src/modules/copilot/application/` → cero matches.

## E2E aislado

- [ ] `test_e2e_isolated.py` verde.
- [ ] Test demuestra que pasando `obs.langchain_config()` a `astream_events` se persisten rows en `copilot_llm_call` + `copilot_trace_event` sin tocar copilot real.

## Hot path intacto

- [ ] `git diff HEAD~N backend/src/modules/copilot/application/orchestrator/chat.py` → vacío (N = número de commits Fase 1).
- [ ] `git diff HEAD~N backend/src/modules/copilot/application/orchestrator/deep_agent.py` → vacío.
- [ ] `git diff HEAD~N backend/src/modules/copilot/application/orchestrator/graph.py` → vacío.
- [ ] `git diff HEAD~N backend/src/modules/copilot/application/observability/trace_recorder.py` → vacío.
- [ ] `git diff HEAD~N backend/src/modules/copilot/application/orchestrator/usage_tracking.py` → vacío.
- [ ] Smoke manual del copilot:
  - `docker compose up -d`
  - Hacer un mensaje al copilot via UI o curl.
  - Verificar respuesta normal.
  - `SELECT COUNT(*) FROM copilot_trace_event WHERE created_at > NOW() - interval '5 minutes'` → > 0.
  - Verificar que sigue habiendo `event_type='turn_end'` con `data->>'cost_usd'` (path actual no roto).

## Quality gates

- [ ] `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` → 0 errors.
- [ ] `cd backend && .venv/bin/ruff format --check src/ tests/` → clean.
- [ ] `cd backend && .venv/bin/pytest -x -q --tb=short` → todos verdes.
- [ ] `cd backend && .venv/bin/pytest tests/architecture/ -x -q` → todos verdes.
- [ ] Coverage backend no bajó: `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q` → ≥43% (gate del proyecto).

## Worker pricing en prod

- [ ] Cron registrado en `backend/src/workers/settings.py`.
- [ ] Si dev environment levantado: ARQ scheduler logs muestran job `sync_litellm_pricing` registrado.

## Docs cerradas

- [ ] `learnings.md` lleno.
- [ ] `deferred-debt.md` lleno (puede ser "ninguno" — pero explícito).
- [ ] Commit final docs: `docs(copilot-obs): close phase 1 — fill learnings + deferred-debt`.
- [ ] Status entrega prompt de `handoff-prompts/start-phase-2.md` al usuario.

---

**Si CUALQUIER item no se puede marcar:** la fase no está cerrada. Documentar bloqueo en `deferred-debt.md` con plan de remediación, **pausar** y consultar al usuario.
