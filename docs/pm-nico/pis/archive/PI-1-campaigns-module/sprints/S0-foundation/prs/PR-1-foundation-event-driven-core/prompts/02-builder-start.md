# Prompt — Builder kickoff (PR-1 foundation-event-driven-core)

> Copy-paste este prompt en una nueva sesión Claude Code, o spawn `nicolify-backend` vía Agent tool. PM pre-coció contexto.

```
Sos `nicolify-backend`. Trabajo: implementar PR-1-foundation-event-driven-core completo siguiendo CONTRACT.md.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/PR.md` — problema + scope
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/CONTRACT.md` — schemas + interfaces + decisiones architect (SSoT pre-implementación)
3. `docs/pm-nico/current-state/{campaigns,sales_agent,copilot,brand}.md` — capacidades vivas (no duplicar)
4. `.claude/rules/backend-ddd.md` + `tenant-isolation.md` + `tdd-mandatory.md` + `backend-migrations.md` + `architectural-fitness.md`
5. `CLAUDE.md` (root)

**Skills a invocar:**
- `sales-agent-expert` — antes tocar emisores sales_agent migration
- `copilot-expert` — antes tocar extraction_card_flow idempotency migration
- `brand-expert` — antes tocar brand_summary_regen flow
- `tessl__fastapi` — patterns FastAPI (relevante para AsyncSession + dependency injection)
- `tessl__pytest-api-testing` — patterns tests API
- `tessl__graceful-degradation` — IdempotencyService soft-fail si Redis unavailable

**Workflow TDD strict (RED → GREEN → REFACTOR por sub-deliverable):**

**Sub-deliverable 1: Outbox**
1. Domain layer:
   - RED: `tests/shared/domain_events/test_outbox_domain.py` (DomainEvent VO invariants)
   - GREEN: implementar `shared/domain_events/outbox/domain/event.py`
2. Infrastructure layer:
   - RED: `tests/shared/domain_events/test_outbox_repository.py` (append + claim_pending + mark_dispatched, tenant_id filter en cada método)
   - GREEN: `shared/domain_events/outbox/infrastructure/{models.py,repository.py}`
3. Migration:
   - Crear `backend/migrations/versions/109_add_domain_event_outbox_and_campaign_observability.py` raw SQL idempotente
   - `make migrate-upgrade` local + verificar aplicada
4. Application layer:
   - RED: `tests/shared/domain_events/test_outbox_service.py` (enqueue + at-least-once + dedupe)
   - GREEN: `shared/domain_events/outbox/application/outbox_service.py`
5. Dispatcher:
   - RED: `tests/shared/domain_events/test_outbox_dispatcher.py` (pending → dispatched, kill+restart recovery)
   - GREEN: `shared/domain_events/outbox/infrastructure/dispatcher.py` + ARQ task wiring
6. Adapter compat:
   - RED: `tests/shared/domain_events/test_event_bus_adapter.py` (legacy publish redirige outbox cuando flag ON)
   - GREEN: `shared/domain_events/outbox/application/event_bus_adapter.py` + deprecation shim en `shared/domain/events.py`

**Sub-deliverable 2: Idempotency**
1. Domain VO: `tests/shared/idempotency/test_idempotency_key.py` → `shared/idempotency/domain/key.py`
2. Infrastructure: `tests/shared/idempotency/test_redis_store.py` → `shared/idempotency/infrastructure/redis_store.py`
3. Application: `tests/shared/idempotency/test_decorator.py` → `shared/idempotency/application/decorator.py` + `service.py`
4. Soft-fail: si Redis unavailable → log warning + permitir ejecución (no raise)

**Sub-deliverable 3: Campaign observability registration**
1. RED: `tests/modules/campaigns/test_observability_registration.py` (verificar `agent_kind="campaign"` registrado)
2. GREEN: crear `backend/src/modules/campaigns/observability/__init__.py` con `register_agent_observability(...)`
3. Importar módulo en `backend/src/main.py` startup (mirror sales_agent + copilot pattern)
4. Migration 109 incluye `campaign_llm_call` + `campaign_trace_event` (mirror schemas)

**Sub-deliverable 4: Migración 3 emisores con feature flags**
1. Tests existentes `test_event_bus.py` + `test_*_event_handlers.py` → SIGUEN PASANDO con flag OFF (default)
2. Para cada módulo (sales_agent, copilot, brand):
   - Reemplazar `from src.shared.domain.events import EventBus` por `from src.shared.domain_events.outbox.application.event_bus_adapter import EventBusAdapter as EventBus`
   - Tests específicos (con flag ON via fixture `monkeypatch.setenv`) verifican enqueue a outbox
3. Feature flags ENV: `USE_OUTBOX_PATTERN_SALES_AGENT`, `_COPILOT`, `_BRAND` (default `false`)

**Sub-deliverable 5: Architecture fitness tests**
1. `tests/architecture/test_outbox_invariants.py` (sin allowlist)
2. `tests/architecture/test_idempotency_used_at_webhooks.py` (allowlist inicial = legacy webhooks. Builder pobla con `grep -rn "@router.post.*webhooks"`)

**Quality gates NATIVE WSL (sin `docker exec`):**
- `cd backend && .venv/bin/ruff check . --fix && .venv/bin/ruff format .`
- `cd backend && .venv/bin/mypy src/shared/domain_events src/shared/idempotency src/modules/campaigns/observability`
- `cd backend && .venv/bin/pytest tests/shared/domain_events tests/shared/idempotency tests/modules/campaigns -v`
- `cd backend && .venv/bin/pytest tests/architecture -v`
- `cd backend && .venv/bin/pytest tests/{brand,sales_agent,copilot,crm} -v` (regression)
- Migration test: clone DB siguiendo `.claude/rules/backend-migrations.md`
- Final: `/test-backend` (13 gates) — debe pasar todo

**Si bloqueado por algo no anticipado en CONTRACT:**
- STOP. Append a `IMPL-LOG.md` sección "Bloqueadores".
- NO inventar solución arquitectónica. Devolver control a PM con marker `@pm`.

**Outputs:**
- Code + tests + migration en codebase
- `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/IMPL-LOG.md` siguiendo template
  - Sub-deliverables completados con checks
  - Decisiones tomadas (no inventadas, basadas en CONTRACT)
  - Lista commits hechos
  - Rollout flag plan (siguiente PR flip por módulo)
- Commits conventional siguiendo `.claude/rules/git-safety.md`:
  - PROHIBIDO `git add .|-A|-u`. Stage por nombre.
  - Conventional: `feat(shared/domain_events): ...`, `feat(shared/idempotency): ...`, `feat(campaigns): observability spec`, `refactor(sales_agent): migrate to outbox adapter`, `test(shared): ...`
  - `git pull origin development` antes cada commit (regla parallel-safety M5)

**Al terminar:**
1. IMPL-LOG.md completo
2. Update `current-state/campaigns.md` (cap: observability spec registered) + `current-state/sales_agent.md`/`copilot.md`/`brand.md` (cap: outbox migration ready behind flag)
3. Última línea de tu respuesta:
   `<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-1 builder done" para review. -->`
4. Reportar a Chris brief < 250 palabras: sub-deliverables shipped + tests verdes + commit hashes + flag rollout pendiente.
```

## Notas

- Builder es BE-only (no FE en PR-1).
- Si tests existentes rompen → root cause investigation (`.claude/rules/debugging.md`), NO `--ignore` ni `xfail`.
- Soft-fail Redis es decisión arquitectónica documentada en CONTRACT — no la cambies sin escalar.
