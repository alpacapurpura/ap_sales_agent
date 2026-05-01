# Prompt — Architect kickoff PR-5

> Spawn `nicolify-architect` vía Agent tool. PM ya pre-coció contexto.

```
Sos `nicolify-architect`. Trabajo: producir CONTRACT.md para PR-5-orchestrator-and-workers.

**Framing CRÍTICO (toda decisión arquitectónica):**
"Hoy pocos clientes, mañana 1000. Robusto + escalable. Cuesta menos corregir hoy que mañana." → Cero deuda técnica, decisiones production-grade desde día 1. ZERO open questions ideal — autonomía completa.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S2-orchestrator/prs/PR-5-orchestrator-and-workers/PR.md` — problema + soluciones elegidas D15-D22 + scope
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S1-domain-campaigns/handoff.md` — surface heredada PR-3+PR-4
3. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S1-domain-campaigns/prs/PR-4-campaigns-application-and-api/CONTRACT.md` — contrato application heredado (orchestrator complementa)
4. `docs/pm-nico/pis/active/PI-1-campaigns-module/PI.md` — visión PI
5. `docs/pm-nico/current-state/campaigns.md` — capabilities S0+S1 shipped
6. Schema vivo SQLA — leer ANTES de escribir CONTRACT (atrapa drift early):
   - `backend/src/modules/campaigns/domain/{campaign,campaign_step,campaign_task,segment,segment_filter,channel_router}.py`
   - `backend/src/modules/campaigns/infrastructure/models/*.py` (PR-3)
   - `backend/src/modules/campaigns/infrastructure/repositories/*.py` (PR-3)
   - `backend/src/modules/campaigns/application/services/*.py` (PR-4)
   - `backend/src/modules/campaigns/api/campaigns.py` — método `launch()` actual stub
7. Surface S0 a consumir REAL este PR:
   - `backend/src/shared/domain_events/outbox/` (OutboxService)
   - `backend/src/shared/idempotency/` (`@idempotent` decorator + `IdempotencyStore`)
   - `backend/src/shared/billing/` (PlanService, BudgetGuard, OutboundRateLimiter)
   - `backend/src/shared/compliance/` (ComplianceService 4 policies)
   - `backend/src/shared/agent_observability/` (`agent_kind="campaign"`)
8. ARQ patterns existentes:
   - `backend/src/workers/settings.py` — WorkerSettings + SchedulerSettings (extend, not replace)
   - `backend/src/modules/sales_agent/workers/*.py` — patrón reference
9. Reglas:
   - `.claude/rules/backend-ddd.md`
   - `.claude/rules/backend-migrations.md` (idempotente raw SQL)
   - `.claude/rules/tenant-isolation.md`
   - `.claude/rules/master-data.md` (DateTime tz=True, utc_now(), tenant locale)
   - `.claude/rules/architectural-fitness.md` (ratchet allowlists shrink-only)
   - `.claude/rules/data-reliability.md` (4 layers verify; circuit breaker patrón)
   - `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` (response_model + audit JSONB sanitize)

**Skills a invocar:**
- `tessl__graceful-degradation` (ANTES diseñar circuit breaker semantics; states/transitions/probe)
- `tessl__pytest-api-testing` (fixture patrones ARQ worker testing)
- `backend-expert` (DDD inside-out, async patterns)

**Tu output: CONTRACT.md completo en**
`docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S2-orchestrator/prs/PR-5-orchestrator-and-workers/CONTRACT.md`

**Secciones obligatorias CONTRACT.md:**

1. **Module surface (DDD inside-out)** — paths exactos new + mod, layer ownership.
2. **Domain interfaces / Protocols** — `ChannelRouterRegistry` API, `CircuitBreaker` interface, `AuditLogService` interface, `CampaignOrchestrator` interface.
3. **SQLA models concretos** — `campaign_audit` columns + types + indices (mirror existing patrones brand/sales_agent).
4. **Pydantic DTOs v2** — `AuditLogEntryDTO`, `OrchestratorLaunchResult`, `ChannelDispatchResult`, exhaustivos con `model_config = ConfigDict(...)`.
5. **Migration 113 schema** — raw SQL CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS exact statements + downgrade.
6. **ARQ functions concretos** — `run_campaign_execution_task`, `run_campaign_scheduler_tick`, `run_segment_refresh_tick`, `purge_old_campaigns_audit` — signatures + retry params + cron schedules + queue name decision.
7. **Circuit breaker semantics** — exact state machine spec, Redis keys schema (`cb:campaigns:{channel}:{tenant_id}`), env vars defaults, error class hierarchy.
8. **TelegramChannelRouter API surface** — class signature, httpx client config, idempotency-key strategy, ComplianceService + RateLimiter wiring callsites.
9. **Decisiones D15-D22 confirmadas** — copia decisiones PR.md + cualquier ajuste tras ver schema vivo.
10. **Test strategy detallado** — fixtures necesarios (ARQ ctx, httpx mock, Redis mock), TDD order RED por capa, integration test sin mocks política F-7.
11. **Architectural fitness gates** — exact AST scan logic + ratchet rules.
12. **Cross-cutting concerns** — tenant isolation invariants, master-data formatting points, PII sanitization en audit JSONB, structlog event schemas.
13. **Open questions for PM** — IDEAL VACÍA. Si surge gap → describilo + alternativa proposed + razón pregunto.

**Reglas duras:**
- NO escribas código de implementación. Solo schemas + interfaces + decisiones arquitectónicas en CONTRACT.md.
- SQLA 2.0 async + Pydantic v2 + structlog SIEMPRE.
- Migrations idempotentes raw SQL IF NOT EXISTS (NUNCA op.create_table()).
- Cada query con `tenant_id` filter.
- response_model obligatorio cada endpoint (PR-5 no agrega endpoints, pero `launch()` MOD respeta).
- Cero deuda técnica. Si decisión "rápida ahora costoso después" → opción más robusta.
- Cada decisión arquitectónica documenta razón "1000 clientes" + alternativa considerada + por qué rechazada.

**Al terminar:**
1. Escribir CONTRACT.md completo (single file).
2. Última línea EXACTA:
   `<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-5 architect done" para review. -->`
3. Reportar a Chris brief < 200 palabras: decisiones tomadas + open questions (IDEAL: cero) + cualquier drift detectado en schema vivo vs PR.md.
```

## Cómo usar

PM ejecuta vía Agent tool con `subagent_type=nicolify-architect`, este prompt entero.
