# Prompt — Architect kickoff (PR-1 foundation-event-driven-core)

> Copy-paste este prompt en una nueva sesión Claude Code, o spawn `nicolify-architect` vía Agent tool. PM ya pre-coció contexto.

```
Sos `nicolify-architect`. Trabajo: producir CONTRACT.md para PR-1-foundation-event-driven-core (PI-1 campaigns S0 foundation).

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/PR.md` — problema + soluciones elegidas + scope completo
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/PI.md` — visión PI + Sprint 0 reframe robustez
3. `docs/pm-nico/current-state/campaigns.md` — capability "observability spec registered" será nueva
4. `docs/pm-nico/current-state/{sales_agent,copilot,brand}.md` — emisores actuales a migrar
5. `docs/pm-nico/research/2026-04-29-campaigns-foundation-synthesis.md` — síntesis foundation
6. `.claude/rules/backend-ddd.md` + `.claude/rules/tenant-isolation.md` + `.claude/rules/backend-migrations.md` + `.claude/rules/architectural-fitness.md`
7. Código vivo (read-only, validar Explore audit en PR.md sigue válido):
   - `backend/src/shared/domain/events.py` (EventBus actual)
   - `backend/src/shared/agent_observability/registry.py` (API existente)
   - `backend/src/modules/copilot/observability/__init__.py` (ejemplo registro)
   - `backend/src/modules/sales_agent/observability/__init__.py` (ejemplo registro)
   - `backend/src/modules/copilot/application/extraction_card_flow.py:68-77` (idempotency ad-hoc actual)
   - `backend/migrations/versions/` últimas 3 (estilo migration vigente)

**Skills a invocar (durante diseño, NO solo audit):**
- `sales-agent-expert` — invariantes voz brand + protected surfaces (no romper) emisores sales_agent
- `copilot-expert` — invariantes copilot extraction_card_flow (idempotency ad-hoc actual debe migrar limpio)
- `brand-expert` — invariantes brand_summary_regen debounce (depends on after-commit dispatch)

**Tu output: `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/CONTRACT.md`** siguiendo template `docs/pm-nico/process/pr-folder-template/CONTRACT.md`.

**Decisiones arquitectónicas a tomar (responder explícito en CONTRACT):**

1. **Outbox table schema concreto:**
   - Columnas: id (UUID), tenant_id (NOT NULL, indexed), event_name (str), payload (JSONB), idempotency_key (str, unique with tenant_id), status (enum: pending/dispatched/failed), retry_count (int), last_error (text), created_at, dispatched_at
   - Índices: (status, created_at) para dispatcher, (tenant_id, idempotency_key) unique constraint
   - Migration 109 idempotente raw SQL (regla `backend-migrations.md`)

2. **OutboxService.enqueue() API exacta:**
   - Firma: `async enqueue(event: DomainEvent, *, session: AsyncSession, idempotency_key: str | None = None) -> None`
   - Comportamiento: insert dentro de la transacción del session pasado. Sin session → AsyncSession standalone con auto-commit. Caller responsable de commit
   - Si `idempotency_key` colisiona en (tenant_id, key) → log warning + skip (no error: at-least-once con dedupe garantiza exactly-once efectivo)

3. **OutboxDispatcher arquitectura:**
   - Decisión: ARQ worker dedicado vs in-process scheduler (ambas son válidas)
   - Recomendación: ARQ worker `dispatch_outbox` cron `*/10 * * * * *` (cada 10s) — consistente con stack actual, scale-out gratis cuando se necesite
   - Claim semantics: `SELECT ... FOR UPDATE SKIP LOCKED` para concurrent dispatchers
   - Retry: exponential backoff. Max retries 5, después `status='failed'` (DLQ S2)

4. **EventBusAdapter compat layer:**
   - `EventBusAdapter.publish(event, session)` mira flag `USE_OUTBOX_PATTERN_{MODULE_UPPER}` → si ON enqueue outbox + skip in-memory dispatch; si OFF → legacy `EventBus._dispatch(event)`
   - Mecanismo flag por módulo emisor: env var O `feature_flags` table (decisión architect)
   - PR-1 ship con TODAS flags OFF por default. Cutover incremental en PR siguiente (S0 cierre o S1)

5. **IdempotencyKey VO + decorator:**
   - VO: namespace + key + ttl
   - Decorator: `@idempotent(key_fn: Callable[..., str], ttl: int = 86400, namespace: str)` — first call execute + cache result, repeats return cached
   - Soft-fail Redis: si Redis unavailable → log warning + permitir ejecución (regla `tessl__graceful-degradation`)
   - Cached result: solo ID + status simple (no full payload — webhooks no necesitan response replay)

6. **`agent_kind="campaign"` registration:**
   - Path: `backend/src/modules/campaigns/observability/__init__.py` (módulo nuevo)
   - Mirror copilot schema: `campaign_llm_call` + `campaign_trace_event`
   - Env vars retention: `CAMPAIGN_LLM_CALL_RETENTION_DAYS=90`, `CAMPAIGN_TRACE_RETENTION_DAYS=30`
   - `has_lead_id=True` (campaign tasks per lead)

7. **Architecture fitness tests nuevos (allowlist ratchet):**
   - `test_outbox_invariants.py` — toda query `domain_event_outbox` filtra `tenant_id`. Sin allowlist
   - `test_idempotency_used_at_webhooks.py` — `@router.post("/webhooks/...")` tiene `@idempotent`. Allowlist inicial = call sites legacy hoy sin idempotencia (poblado por architect tras grep)

**Reglas duras:**
- NO escribas código de implementación. Solo schemas + interfaces + migration plan + decisiones arquitectónicas.
- SQLA 2.0 async + Pydantic v2 + structlog (no `print`/`logging`).
- Migrations idempotentes raw SQL `IF NOT EXISTS`.
- Cada query con `tenant_id` filter (regla `tenant-isolation.md`).
- response_model obligatorio (no aplica esta PR — sin endpoints API).
- Si detectás gap funcional en PR.md → flag en sección "Open questions for PM" y NO inventes solución.

**Al terminar:**
1. Escribir CONTRACT.md completo (schemas tabla + API interfaces sub-deliverable + migration outline + adapter pattern + flag rollout plan + open questions si las hay).
2. Última línea de tu respuesta debe ser EXACTAMENTE:
   `<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-1 architect done" para review. -->`
3. Reportar a Chris brief < 200 palabras: qué decidiste + qué quedó como open question.
```

## Cómo usar

1. Spawn `nicolify-architect` vía Agent tool con este prompt entero como `prompt`, o copiá-pegá en sesión Claude Code nueva
2. Architect produce `CONTRACT.md` y termina con marker `@pm`
3. Volvé a `/pm` o ejecutá `prompts/02-builder-start.md` para arrancar implementación
