# Principios no-negociables

Aplican a las 3 fases. Si una decisión durante ejecución viola alguno, **pausá y consultá** — no improvises excepción.

## 1. Alta cohesión, bajo acoplamiento

- **Todo** lo de observabilidad vive en `backend/src/modules/copilot/observability/`. Nada disperso en orchestrator, tools, services.
- Copilot **no importa** de `observability/` (excepto el wrapper `ObservabilityContext` que se cablea en chat.py al inicio del turn — único punto de import).
- Observability **importa** de copilot solo: `domain/events.py` (contratos publish-subscribe). Nunca de orchestrator/tools/api.

## 2. Migración total, no paralela

- **Prohibido** dejar código viejo "deprecated" o "legacy" tras Fase 2. Se borra en el mismo commit que lo reemplaza.
- **Prohibido** features a medias: cada fase termina con sistema verde + funcional, no con "falta hacer X".
- **Prohibido** flags de feature permanentes para conmutar entre old/new. Flag temporal de 24-48h post-Fase-2 sí (rollback safety), pero se borra explícitamente en commit posterior.
- Métrica objetiva: `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b"` en backend/src/ → cero matches al cerrar Fase 2.

## 3. Switch atómico en hot path

- Cambios al hot path (`chat.py`, `deep_agent.py`, `graph.py`) **solo en Fase 2**, en **un solo commit**.
- Ese commit elimina los ~10 sitios de `recorder.record(...)` y reemplaza por:
  - `obs.start_turn(...)` / `obs.end_turn(...)` (turn envelope)
  - `event_bus.publish(CardEmitted(...))` para cards
  - `RunnableConfig(callbacks=[obs.callback_handler])` en graph stream
- Antes y después del commit el copilot funciona idéntico desde el punto de vista del usuario final.

## 4. Best-effort writes

- Observability **nunca rompe un turn del copilot**. Toda excepción en recorder/callback handler se loguea como `warning` y el turn sigue.
- Pattern existente en `trace_recorder.py:159-170` se conserva: try/except amplio + `db.rollback()` + `db.close()` en finally.
- Aplica a: callback handler, repositorios, pricing resolver, FX resolver, domain subscribers.

## 5. TDD obligatorio

- Tests primero, implementación después (regla `.claude/rules/tdd-mandatory.md`).
- Cada componente nuevo: test unitario antes de la primera línea de código.
- Migración: test de schema antes (verifica tabla existe + índices + constraints).
- Callback handler: test con `FakeListLLM` o `RunnableLambda` de LangChain antes de la lógica.

## 6. Pricing como data, no código

- **Prohibido** hardcodear precios. Cero `_PRICING = {...}` en código.
- Fuente única: `model_pricing_snapshot` poblada por worker `pricing_sync_task`.
- Worker fuente: `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json`.
- Snapshot al call (no al report): `copilot_llm_call.pricing_version_id` apunta a la row vigente al `started_at`.

## 7. Schema OTel-compatible

- Nombres de columnas en `copilot_llm_call` siguen OpenTelemetry GenAI semantic conventions (Development as of April 2026): `provider`, `model_requested`, `model_responded`, `input_tokens`, `output_tokens`, `cached_read_tokens`, etc.
- Permite exportar a OTel collector futuro con rename trivial.
- Span tree (`turn_id`/`span_id`/`parent_span_id`) ya es OTel-shape — se mantiene.

## 8. PII redaction antes de persistir

- Truncate a 4000 chars (existente) **no** es PII redaction.
- Fase 3 agrega Presidio (es+en recognizers) + regex (emails, teléfonos, IDs) en `recording/sanitization.py`.
- Aplica a: `data.input_messages`, `data.output_preview`, `tool_call.args`, `tool_call.output_preview`.
- Defense-in-depth: regex en recorder (síncrono, rápido), Presidio en worker async (post-write, opcional para prompts largos).

## 9. Tenant isolation estricto

- Todas las queries filtran `tenant_id` (regla `.claude/rules/tenant-isolation.md`).
- `copilot_llm_call`: índice `(tenant_id, occurred_on)` en primer plano. Reportes por tenant nunca scan full table.
- Workers (pricing_sync, retention, aggregate_refresh) operan cross-tenant pero a nivel agregado (no leakean data row-level).

## 10. Idempotencia en migraciones

- Raw SQL con `IF NOT EXISTS` (regla `.claude/rules/backend-migrations.md`).
- Re-run de la migración no rompe.
- Test antes de prod: clonar DB de prod, aplicar migration, validar.

## 11. Git safety en sesiones paralelas

- Branch `development` único. NUNCA crear feature branches o worktrees.
- Stage por nombre: `git add backend/src/modules/copilot/observability/recording/callback_handler.py`.
- **Prohibido** `git add .`, `git add -A`, `git add -u`.
- Si `git status` muestra archivos no tocados por esta sesión → dejar intactos, reportar al final.
- Conventional commit: `feat(copilot-obs)`, `chore(copilot-obs)`, `fix(copilot-obs)`, `docs(copilot-obs)`, `test(copilot-obs)`.

## 12. Lint/tests/type-check NATIVE WSL

- Backend: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`, `.venv/bin/pytest -x -q --tb=short`.
- Frontend: `cd frontend && npx tsc --noEmit`, `npx vitest run`.
- Docker SOLO para runtime + migrations + DB.
- **Prohibido** `docker exec ... ruff|pytest|tsc|vitest`.

## 13. Spanish neutro LatAm en user-facing

- Streamlit dashboard, error messages, tooltips: tuteo (`tú`), nunca voseo (`vos/tenés/podés/mirá`).
- Aplica a UI del Admin Panel (Fase 3). No aplica a logs internos, comentarios código, nombres de variables.
- Regla completa: `.claude/rules/spanish-text.md`.

## 14. Documentar al cerrar fase

Antes de declarar fase completa:
1. Llenar `learnings.md` con decisiones, sorpresas, atajos.
2. Llenar `deferred-debt.md` con items NO completados (justificar por qué).
3. Verificar cada item de `completion-checklist.md` (no marcar item sin evidencia).
4. Update `docs/domains/copilot/INDEX.md` solo cuando Fase 3 cierre.

## 15. Stopping conditions

Pausar y consultar al usuario si:
- Research checklist revela cambio mayor SOTA respecto al diseño (ej. OTel GenAI promovido a Stable con breaking attributes).
- Migration falla en clone de prod por razón no documentada.
- Tests fallan tras 3 intentos sin causa raíz clara.
- Aparece WIP de otra sesión que toca archivos a editar (chat.py, deep_agent.py).
- Cualquier item de `completion-checklist.md` no se puede satisfacer.

**Nunca** improvises excepción a un principio sin aprobación explícita.
