# PR-5-orchestrator-and-workers

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-5-orchestrator-and-workers |
| Sprint padre | S2-orchestrator |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | infra + feature |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | 2026-04-30 — orchestrator main, paths `modules/campaigns/{application,infrastructure,workers,api}` + `alembic/versions/113_*` + `workers/settings.py` (extend) |

## Problema (user-facing)

PR-3 + PR-4 entregaron el data plane completo + servicios CRUD + 23 endpoints REST. Pero `Campaign.launch()` es **STUB** — emite `CampaignLaunched` event al outbox, marca `launched_at`, **no ejecuta ningún envío real**.

- Sin orchestrator real: `POST /campaigns/{id}/launch` no produce CampaignTasks ni dispatch a canales.
- Sin workers ARQ: ningún consumer del outbox event. CampaignTasks nunca se procesan.
- Sin ChannelRouter impl: el port `ChannelRouter` (PR-3) sólo es Protocol — sin implementación física.
- Sin circuit breaker: cada llamada Telegram puede degradar el sistema entero si la API se cae (regla `data-reliability.md`).
- Sin audit log: imposible debugear "¿por qué este lead no recibió mensaje?" — tabla dedicada `campaigns_audit` permite respuesta concreta con retención 90d.
- Sin schedule worker: `scheduled_at` en futuro nunca se activa. UI muestra "scheduled" eternamente.
- Sin segment refresh worker: campañas con `segment_type=STATIC` requieren snapshot inicial automático cuando transitionan a running.

JTBD interno: "Como builder de Nicolify, cuando S3 implemente el `OutboundOrchestrator` sales_agent y PI-2 conecte al copilot subagent, quiero un pipeline ejecución end-to-end production-grade (orchestrator + 3 workers + ChannelRouter Telegram + circuit breaker + audit log) listo para 1000 clientes — sin refactor — para que esas piezas hereden infraestructura robusta y solamente agreguen capabilities sobre canales adicionales (WhatsApp, Email PI-2)."

## Outcome esperado

Pipeline ejecución completamente funcional para Telegram, scoped a:

1. **`CampaignOrchestrator`** (`application/services/orchestrator.py`) — REAL, no stub:
   - `launch(campaign_id)` → resolve segment (snapshot opt-in si STATIC) → idempotent batch INSERT `CampaignTask` por (lead, step) via DAG steps → emit `CampaignLaunched` event al outbox → ARQ enqueue del job de dispatch para `step.delay_minutes=0` tasks.
   - Idempotente con `@idempotent(key_fn=lambda c: f"campaign-launch:{c.id}")` (S0.2 primitive) — re-launch silencioso si dentro TTL.
   - Emite `CampaignTasksGenerated(campaign_id, total_tasks)` event tras INSERT.
2. **3 ARQ workers** registrados en `backend/src/workers/settings.py`:
   - **`run_campaign_execution_task(ctx, campaign_task_id)`** — consume `CampaignTask` específica via id (encolada por orchestrator o scheduler). Hace: lock row con `FOR UPDATE SKIP LOCKED` (worker queue partial idx PR-3) → ChannelRouter dispatch → update task status → audit log → retry exponencial backoff si falla recuperable.
   - **`run_campaign_scheduler_tick(ctx)`** — cron cada minuto. Busca campaigns con `status='scheduled' AND scheduled_at ≤ utc_now()` → invoca `CampaignOrchestrator.launch(campaign_id)` por cada una. Idempotente por @idempotent en orchestrator.
   - **`run_segment_refresh_tick(ctx)`** — cron cada 15 min. Busca segments con `segment_type=STATIC` linked a campaigns `status='running'` SIN snapshot reciente (>15min) → ejecuta `SegmentService.snapshot()` por cada una. Solo aplica a campaigns con steps pendientes (`scheduled_at` futuro y task aún no creada).
3. **ChannelRouter v1 Telegram-only** (`infrastructure/channels/`):
   - **`TelegramChannelRouter`** implementa `ChannelRouter` Protocol PR-3.
   - `select_channel(tenant_id, lead_id, priority)` → si `lead.telegram_id` existe y `"telegram" in priority` → "telegram"; else None.
   - `send(...)` → llama `httpx.AsyncClient.post(f"{TELEGRAM_API}/bot{token}/sendMessage", json={...})` con timeout 10s + retry circuit breaker. Idempotency-Key opt-in via `@idempotent` decorator (S0.2). Aplica `ComplianceService.check` + `OutboundRateLimiter.check` PRE-send (gates wiring real este PR).
   - **`ChannelRouterRegistry`** — singleton holding registered routers por canal. `register("telegram", router)` + `get("telegram") -> ChannelRouter`. Extensible para WhatsApp/Email PI-2 sin modificar consumer (orchestrator/worker).
4. **Circuit breaker custom** (`infrastructure/resilience/circuit_breaker.py`):
   - Custom asyncio-native (cero dep new — pybreaker es sync, aiobreaker abandoned). 80 LOC.
   - 3 estados: CLOSED / OPEN / HALF_OPEN.
   - Default config: 5 fail / 60s rolling window → OPEN. Tras 60s → HALF_OPEN (1 probe). Probe ok → CLOSED. Probe fail → OPEN otros 60s.
   - Tunable via env: `CAMPAIGNS_CB_FAIL_THRESHOLD=5`, `CAMPAIGNS_CB_OPEN_DURATION_SECONDS=60`, `CAMPAIGNS_CB_HALF_OPEN_PROBES=1`.
   - Por (channel, tenant_id) key — un Telegram fail no afecta otro tenant. Estado en Redis (multi-pod safe).
   - `OPEN` raises `CircuitBreakerOpenError` → worker marca task `failed` con `error_code='circuit_open'` + audit log + ARQ retry NO se aplica (espera scheduler tick siguiente para retry orchestrator-level).
5. **Audit log dedicado** (`campaigns_audit` tabla nueva, migration 113):
   - Schema: `id UUID PK`, `tenant_id UUID NOT NULL`, `campaign_id UUID FK`, `campaign_task_id UUID FK NULL`, `event_type VARCHAR(50) NOT NULL`, `actor VARCHAR(50) NOT NULL` (worker/scheduler/api/system), `payload JSONB NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`.
   - Event types: `campaign_launched`, `tasks_generated`, `task_dispatched`, `task_sent`, `task_failed`, `task_skipped`, `circuit_opened`, `circuit_closed`, `compliance_blocked`, `rate_limited`.
   - Retention 90d (mirror `copilot_trace_event` PR-1) — worker dedicated `purge_old_campaigns_audit` cron diario 04:30 UTC.
   - Indices: `(tenant_id, campaign_id, created_at DESC)` para "todos los eventos de esta campaña" + `(created_at)` para retention purge.
6. **Wiring real `OutboundRateLimiter.check` / `ComplianceService.check`** en `TelegramChannelRouter.send`:
   - `OutboundRateLimiter.check(tenant_id)` PRE-send. Fail → audit `rate_limited` + task status `pending` + reschedule scheduler tick siguiente.
   - `ComplianceService.check(contact, channel, campaign)` PRE-send. Block → audit `compliance_blocked` + task status `skipped` (NO retry — opt-out es definitivo).
   - `BudgetGuard.check` NOT wired aquí — campaigns no invoca LLM directo (eso es S3 sales_agent OutboundOrchestrator). PR-6 wirea copilot/sales_agent LLM call sites.
7. **Métricas:**
   - `/test-backend` 13 gates verde + 4 nuevos arch tests.
   - Smoke E2E: crear campaign DRAFT con 1 step Telegram → schedule (now+5s) → wait scheduler tick → verificar `CampaignTask.status='sent'` + audit row `task_sent` + Telegram API mock recibió payload con tenant locale formatting aplicado.
   - p95 launch (segment 100 leads) < 2s (orchestrator + INSERT batch + outbox enqueue).
   - p95 task dispatch (single task lock + send) < 500ms (excluye Telegram API roundtrip).
   - Worker pool: queue dedicada `arq:campaigns_execution` con `max_jobs=20` + queue default conservada para etl/copilot/sales_agent existentes.
   - Cero conflicto con workers existentes (ETL, copilot, sales_agent) — verificado via test integración con WorkerSettings full functions list.
8. **Sin sales_agent OutboundOrchestrator** — diferido S3.
9. **Sin FE** — diferido post PI-1.
10. **Sin WhatsApp/Email** — diferido PI-2.
11. **Sin inbound reply recognition** — diferido S3.

## Walking skeleton (mínimo viable cohesivo)

PR amplio cohesivo (Opus 4.7[1M]). Layout:

```
backend/src/modules/campaigns/
├── application/
│   ├── services/
│   │   ├── orchestrator.py                          (NEW — CampaignOrchestrator.launch())
│   │   └── audit_log_service.py                     (NEW — campaigns_audit writer)
│   └── dtos/
│       └── audit_log_dtos.py                        (NEW — AuditLogEntryDTO Pydantic)
├── infrastructure/
│   ├── channels/
│   │   ├── __init__.py                              (NEW)
│   │   ├── registry.py                              (NEW — ChannelRouterRegistry singleton)
│   │   ├── telegram.py                              (NEW — TelegramChannelRouter)
│   │   └── shared.py                                (NEW — common dispatch helpers + tenant locale)
│   ├── repositories/
│   │   └── audit_log_repo.py                        (NEW)
│   ├── models/
│   │   └── campaign_audit.py                        (NEW — SQLA model campaigns_audit)
│   └── resilience/
│       ├── __init__.py                              (NEW)
│       └── circuit_breaker.py                       (NEW — asyncio Redis-backed CB)
├── workers/
│   ├── __init__.py                                  (NEW)
│   ├── execution_task.py                            (NEW — run_campaign_execution_task ARQ fn)
│   ├── scheduler_tick.py                            (NEW — run_campaign_scheduler_tick ARQ fn)
│   ├── segment_refresh_tick.py                      (NEW — run_segment_refresh_tick ARQ fn)
│   └── audit_retention_task.py                      (NEW — purge_old_campaigns_audit ARQ fn)
└── api/
    └── campaigns.py                                  (MOD — replace launch() stub w/ orchestrator.launch())

backend/src/workers/settings.py                      (MOD — register 4 new functions + 3 cron jobs)
backend/alembic/versions/
└── 113_campaigns_audit_log.py                       (NEW — idempotente raw SQL CREATE TABLE IF NOT EXISTS)

backend/tests/modules/campaigns/                     (extend)
├── application/
│   ├── test_orchestrator.py                         (NEW — RED por capa)
│   ├── test_orchestrator_idempotency.py             (NEW)
│   └── test_audit_log_service.py                    (NEW)
├── infrastructure/
│   ├── test_channel_router_registry.py              (NEW)
│   ├── test_telegram_channel_router.py              (NEW — mock httpx)
│   ├── test_circuit_breaker.py                      (NEW)
│   └── test_audit_log_repo.py                       (NEW)
├── workers/
│   ├── test_execution_task.py                       (NEW — ARQ ctx fixture)
│   ├── test_scheduler_tick.py                       (NEW)
│   ├── test_segment_refresh_tick.py                 (NEW)
│   └── test_audit_retention_task.py                 (NEW)
├── integration/
│   └── test_e2e_telegram_campaign_smoke.py          (NEW — sin mocks de service, mock solo httpx Telegram API)
└── api/
    └── test_campaigns_launch_real.py                (MOD — launch() ya no es stub, integra orchestrator)

backend/tests/architecture/                          (extend)
├── test_campaigns_orchestrator_idempotent.py        (NEW — gate: orchestrator.launch decorated @idempotent)
├── test_campaigns_workers_registered.py             (NEW — gate: 4 functions + 3 crons en WorkerSettings)
├── test_channel_router_registry_invariants.py       (NEW — gate: TelegramRouter implements ChannelRouter Protocol)
└── test_campaigns_audit_log_retention.py            (NEW — gate: 90d retention worker exists)
```

## Soluciones consideradas

### Decisión D15 — Circuit breaker library

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Custom asyncio-native (Redis-backed state, ~80 LOC)** | Cero dep new (regla pip-audit). Async-first desde día 1. Multi-pod safe (Redis state). Tunable env. Match patrón `OutboundRateLimiter` (PR-2). | Mantenimiento código propio. | **ELEGIDA** |
| B — `pybreaker` | Mature, bien testeado | Sync-only. Wrapping async = anti-pattern. No multi-pod state. | descartada |
| C — `aiobreaker` | Async-native | Abandoned 2021. Single-pod state. | descartada |
| D — `purgatory` | Async + multi-storage | Dep nuevo. Curva learning. | descartada (custom suficiente, menos riesgo) |

### Decisión D16 — ARQ worker pool topology

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Queue dedicada `arq:campaigns_execution` (separada del default), max_jobs=20. Scheduler/refresh van al pool default existente** | Production-grade 1000 clientes. Outbound dispatch no compite con ETL workers. Container-separable día 1 (futuro). | Config WorkerSettings más compleja (2 named queues). | **ELEGIDA** |
| B — Single pool, todas funciones en `WorkerSettings.functions` con `max_jobs=30` | Simple. Misma config existente. | ETL extraction de 1 tenant grande puede saturar pool y bloquear campaign sends de otros 100 tenants. Anti-pattern 1000 clientes. | descartada |
| C — Process separado dedicado `campaigns_worker.py` con `WorkerSettings` propio | Aislamiento total | Container nuevo. Out of scope PR-5 (deploy infra change). | descartada (queue named alcanza, deploy decision later) |

ARQ named queue = añadir `queue_name="arq:campaigns_execution"` al ARQ pool config + decoradar `@redis_pool.enqueue_job` con `queue_name`. WorkerSettings nuevo `CampaignsWorkerSettings` consume esa queue. Documenta deploy multi-process en `IMPL-LOG.md` para futuro.

**Default deploy hoy:** ambos workers (default + campaigns_execution) corren en mismo container actual. Future split = 1 línea en `docker-compose.yml`.

### Decisión D17 — CampaignTask retry policy

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Exponential backoff (60s base × 2^retry, max 5 retries, max 1h backoff). ARQ-native via `arq.cron.retry`** | ARQ built-in. Configurable per-job. Match patrón ETL workers existentes. | Hard cap 5 retries fixed. | **ELEGIDA** |
| B — Linear retry 5min × 5 | Simple | Mata API en falla cascade (no respeta backoff) | descartada |
| C — DLQ tras N fails | Production-grade | Out of scope (necesita queue infra). DLQ entry implícito vía `task.status='failed'` + audit log. | descartada (PR-5: usa status field; queue DLQ puede agregarse PI-2) |

**Mapping retry → CampaignTask:**
- ARQ retry transparente al worker; worker no sabe el número de attempt.
- `CampaignTask.failed_at` + `CampaignTask.error_message` actualizados solo tras 5to fail (max_tries exhausted).
- `CampaignTask.status='dispatched'` durante retries — UI muestra "enviando..." sin indicar attempt#.

### Decisión D18 — Idempotency-Key Telegram dispatch

`Telegram Bot API sendMessage` no soporta header Idempotency-Key nativo. Solución:

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Application-side idempotency: `IdempotencyStore.set_if_not_exists(f"telegram-send:{campaign_task_id}", external_msg_id, ttl=86400)`. Pre-send check; si existe → return cached result (no llamar API)** | Idempotente reescritura segura. TTL 24h cubre retry window. Reusa S0.2. | Race entre 2 workers en task duplicada (improbable: `FOR UPDATE SKIP LOCKED` ya previene) | **ELEGIDA** |
| B — Telegram Bot API `disable_notification + reply_to_message_id` proxy | No es idempotency real | descartada |
| C — Skip idempotency (dedup at task level via UNIQUE) | UNIQUE en `campaign_task` ya existe (`(campaign_id, lead_id, step_id)`) | Si fail post-send pre-update, retry duplica msg | descartada (riesgo dup msg) |

### Decisión D19 — Audit log retention

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — 90d retention, daily purge cron 04:30 UTC, mirror `copilot_trace_event` (PR-1)** | Match patrón observability cementado. Suficiente debug histórico campaña típica (ciclo lead < 90d). | Tabla puede crecer 100K rows/día con 1000 clientes activos × 100 events/día. Manejable con index `(created_at)`. | **ELEGIDA** |
| B — 30d retention | Tabla más chica | Demasiado corto para post-mortem campañas largas (launch 4-day + post-purchase 30d). | descartada |
| C — Sin retention (forever) | Histórico completo | 36M rows/año = índices degradan + backups crecen. Anti-1000-clientes. | descartada |

**Tunable env:** `CAMPAIGNS_AUDIT_RETENTION_DAYS=90`. Worker `purge_old_campaigns_audit` cron diario respeta env.

### Decisión D20 — Webhook bidireccional Telegram (inbound replies)

**OUT OF SCOPE PR-5** — diferido S3.

S3 implementa `OutboundOrchestrator` sales_agent + inbound reply recognition (ChatOrchestrator busca `CampaignTask SENT últimas 24h` → inyecta `campaign_id` en AgentState). PR-5 solo outbound dispatch. Decisión architect S3.

### Decisión D21 — Cutover order (PR-6 paralelo vs secuencial)

PR-6 hace 3 flag flips: `USE_OUTBOX_PATTERN_SALES_AGENT`, `USE_OUTBOX_PATTERN_COPILOT`, `USE_OUTBOX_PATTERN_BRAND`.

Decisión: **secuencial** un flag por commit + smoke test entre cada flip. Razón: blast radius bajo. Si sales_agent rompe, revertir flag = 1 line change. Paralelo: 3 cosas rotas simultáneo. Detalle en PR-6 PR.md.

### Decisión D22 — `CampaignOrchestrator.launch()` SQL strategy

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Single transaction: `BEGIN; SELECT FOR UPDATE Campaign; INSERT batch CampaignTask; INSERT outbox event; COMMIT;`** | Atomicidad perfecta. Si falla algo → rollback total. No tasks huérfanas. | Lock long en Campaign row (microseg, irrelevante). | **ELEGIDA** |
| B — Múltiples txns (resolve segment → tx insert tasks → tx insert event) | Granularidad fina | Estado intermedio inconsistente posible (tasks creadas, event no enviado) | descartada |
| C — Saga pattern | Robusto edge cases | Complejidad O(20x) sobre escala actual. Premature. | descartada |

`CampaignOrchestrator.launch` usa `async with session.begin():` block — atomic.

## Validación técnica preliminar (Technical Sanity Check)

**Estado actual `campaigns/`:**
- `domain/` shipped (PR-3, PASS).
- `infrastructure/{models,repositories}/` shipped (PR-3, PASS) — falta `models/campaign_audit.py` + `repositories/audit_log_repo.py` + `infrastructure/{channels,resilience}/`.
- `application/services/{campaign,segment,template,segment_filter_evaluator}.py` shipped (PR-4, PASS) — falta `orchestrator.py` + `audit_log_service.py`.
- `api/campaigns.py launch()` STUB (PR-4) → MOD para integrar orchestrator.
- `workers/` NO existe → PR-5 lo crea.
- `observability/` shipped (PR-1) — REUSADO sin modificar.

**Primitivas S0 disponibles (consumidas PR-5):**
- `OutboxService.enqueue_async_from_sync_caller(event, *, session=...)` — usado en orchestrator + workers.
- `@idempotent(key_fn, ttl)` — usado en orchestrator.launch + telegram dispatch.
- `IdempotencyStore.set_if_not_exists(key, value, ttl)` — usado en telegram_router para application-side dedup.
- `OutboundRateLimiter.check(tenant_id)` — wired en `TelegramChannelRouter.send`.
- `ComplianceService.check(contact, channel, campaign)` — wired en `TelegramChannelRouter.send`.

**Primitivas codebase reusables:**
- `httpx.AsyncClient` patrón (existe en `connections/external/*` Telegram bot mgmt PR previo) — confirmar reuso si hay; si no, nuevo client.
- `arq.cron` + `WorkerSettings.functions` (existe en `backend/src/workers/settings.py`).
- `redis_client` ya en `core.database` — usado para circuit breaker state + idempotency.
- `utc_now()` + `DateTime(timezone=True)` (master-data).
- `structlog.get_logger(__name__)` (no print).
- `get_tenant_locale(tenant_id)` (master-data) — formatting Telegram message.

**Modules afectados:** SOLO `modules/campaigns/{application,infrastructure,workers,api}/` + `alembic/versions/113_*.py` + `backend/src/workers/settings.py` (extend functions list + cron). Cero touch en otros modules.

**Tests críticos no romper:**
- 4 arch tests PR-3 (domain) + 4 arch tests PR-4 (application/api) = 8 frozen.
- `test_ddd_boundaries.py` (ratchet 22 frozen).
- `test_outbox_invariants.py` (events emitted via OutboxService).
- `test_master_data_compliance.py` (DateTime tz=True).
- `test_no_new_copilot_module_imports.py` (campaigns NO importa copilot).

**Conflicto sesiones paralelas:** PI-2 (voice/suggestions/backfill) opera en `copilot/`, `sales_agent/`, `voice/`. PR-5 toca `campaigns/` exclusivamente + 1 archivo `backend/src/workers/settings.py` (potencial colisión semántica si PI-2 también extend functions list). Mitigación: builder VERIFICA `git status` antes de cada commit + lectura `workers/settings.py` actual + APPEND functions sin remover existentes (regla M8 "extend, no destroy"). Conflicto Telegram bot integration: revisar `connections/` modules pre-impl.

**Tiempo estimado:** L (1 architect + 1 builder denso TDD por capa + 1 auditor + posible re-spawn fix-loop).

## Decisiones diferidas (explícitas)

| Item | Razón | Cuándo |
|---|---|---|
| WhatsApp/Email/IG DM ChannelRouter impls | Out of scope PR-5 | PI-2 |
| `OutboundOrchestrator` sales_agent + AgentState `campaign_id` slot | S3 |
| Inbound reply recognition (ChatOrchestrator busca CampaignTask SENT 24h) | S3 |
| Webhook receiver Telegram (inbound) | S3 (cuando OutboundOrchestrator listo) |
| Marketing campaign subagent copilot (`commercial_director`) | PI-2 |
| FE `/campañas/*` UI | post PI-1 |
| Mini CRM Hub `/sales/contactos` | S4 paralelo |
| DLQ infra dedicada (queue separada para failed tasks) | implícito vía status field PR-5 | PI-2 |
| `CampaignTask` mutation routes HTTP (mark_sent/mark_failed) | NO requeridas — workers internos updatean | post PI-1 |
| Per-tenant ARQ pool isolation | global pool dedicated suficiente día 1 | PI-3 (tenant noisy neighbor) |

## Out of scope

- Cualquier ChannelRouter impl ≠ Telegram (WhatsApp, Email, IG DM, FB Messenger, voice) → PI-2/PI-3
- sales_agent OutboundOrchestrator → S3
- Copilot tools / subagent → PI-2
- FE → post PI-1
- Cutover real consumers BudgetGuard wiring (sales_agent/copilot LLM call sites) → **PR-6** (PR-5 wirea solo Compliance/RateLimiter en `TelegramChannelRouter.send`)
- Inbound reply recognition → S3
- Tests Playwright E2E full → S3
- Real Telegram API hitting (mock httpx en tests, dev-app smoke con bot test)

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** Default Sí, **N/A funcional PR-5**: backend pipeline shipped. PI-2 commercial_director subagent wirea las tools (`campaign_launch`, `campaign_get_status`, `campaign_pause`).
- [x] **¿Qué tools nuevos requiere?** Ninguno PR-5.
- [x] **¿Cards/UI nueva?** Ninguna PR-5 (sin FE). PI-2 introduce `CampaignProposalCard`, `SegmentPreviewCard`.
- [x] **Si NO copilot → razón documentada:** PR-5 = execution pipeline backend. Copilot consume PI-2 vía tools que invocan `POST /api/v1/campaigns/{id}/launch` (ahora real, no stub).

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` (interfaces orchestrator + workers + ChannelRouter + audit log + circuit breaker + ARQ pool config) |
| UX | — | — | N/A (no UI) |
| Implementation | `nicolify-backend` | `prompts/02-builder-start.md` | code + tests + migration 113 + IMPL-LOG |
| Audit | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` | `REVIEW.md` (13 gates `/test-backend` + 4 arch tests nuevos) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/campaigns.md` update |

**Skills módulo a invocar durante implementation/audit:**
- `backend-expert` (DDD inside-out, async patterns, arch fitness)
- `tessl__graceful-degradation` (timeouts, circuit breaker, retry — Telegram external call)
- `tessl__pytest-api-testing` (httpx async client + ARQ worker fixtures)

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Service | `backend/src/modules/campaigns/application/services/orchestrator.py` | NEW `CampaignOrchestrator.launch()` real |
| Service | `application/services/audit_log_service.py` | NEW `AuditLogService.record(...)` |
| Adapter | `infrastructure/channels/telegram.py` | NEW `TelegramChannelRouter` |
| Adapter | `infrastructure/channels/registry.py` | NEW `ChannelRouterRegistry` singleton |
| Adapter | `infrastructure/channels/shared.py` | NEW dispatch helpers + tenant locale formatting |
| Repo | `infrastructure/repositories/audit_log_repo.py` | NEW |
| Model | `infrastructure/models/campaign_audit.py` | NEW SQLA model |
| Resilience | `infrastructure/resilience/circuit_breaker.py` | NEW asyncio Redis-backed CB |
| Worker | `workers/execution_task.py` | NEW `run_campaign_execution_task` |
| Worker | `workers/scheduler_tick.py` | NEW `run_campaign_scheduler_tick` |
| Worker | `workers/segment_refresh_tick.py` | NEW `run_segment_refresh_tick` |
| Worker | `workers/audit_retention_task.py` | NEW `purge_old_campaigns_audit` |
| API | `api/campaigns.py` | MOD `launch()` ya no stub, integra `orchestrator.launch()` |
| Workers cfg | `backend/src/workers/settings.py` | MOD: append 4 fns + 3 crons + comment seccionado "S2 campaigns workers" |
| Migration | `backend/alembic/versions/113_campaigns_audit_log.py` | NEW idempotente |
| Tests | `tests/modules/campaigns/{application,infrastructure,workers,integration}/test_*.py` | NEW |
| Tests arch | `tests/architecture/test_campaigns_orchestrator_idempotent.py` | NEW |
| Tests arch | `tests/architecture/test_campaigns_workers_registered.py` | NEW |
| Tests arch | `tests/architecture/test_channel_router_registry_invariants.py` | NEW |
| Tests arch | `tests/architecture/test_campaigns_audit_log_retention.py` | NEW |
| Env vars | `CAMPAIGNS_CB_FAIL_THRESHOLD=5`, `CAMPAIGNS_CB_OPEN_DURATION_SECONDS=60`, `CAMPAIGNS_CB_HALF_OPEN_PROBES=1`, `CAMPAIGNS_AUDIT_RETENTION_DAYS=90`, `CAMPAIGNS_EXECUTION_QUEUE_NAME=arq:campaigns_execution`, `CAMPAIGNS_EXECUTION_MAX_JOBS=20`, `TELEGRAM_API_TIMEOUT_SECONDS=10` | NEW (todos opcionales con defaults sane) |
| current-state | `current-state/campaigns.md` | append capability "S2 PR-5: orchestrator real + 3 ARQ workers + ChannelRouter Telegram + circuit breaker + audit log + retention 90d" con lineage PR-5 |

## Tests requeridos (TDD)

### Layer A — Application services (RED por capa antes implementar)

- `test_orchestrator.py` — `launch(campaign_id)`: resolve segment → batch INSERT tasks → outbox event → ARQ enqueue. Verifica atomicidad (transactional). Verifica idempotency (re-launch silencioso).
- `test_orchestrator_idempotency.py` — re-launch within TTL no duplica tasks ni emite duplicate event (cumulative count idempotente).
- `test_audit_log_service.py` — `record(event_type, actor, payload)` INSERT row + tenant_id propagado + payload JSONB.

### Layer B — Infrastructure

- `test_channel_router_registry.py` — register/get/missing channel raises.
- `test_telegram_channel_router.py` — happy path (mock httpx 200) + 429 rate limit + 500 retry + idempotency-key dedup + ComplianceService block (skip task) + RateLimiter exceed (reschedule).
- `test_circuit_breaker.py` — CLOSED → 5 fails → OPEN → 60s → HALF_OPEN → probe ok → CLOSED. Probe fail → OPEN. Per-key isolation.
- `test_audit_log_repo.py` — INSERT + tenant-scoped query + 90d filter retention.

### Layer C — Workers

- `test_execution_task.py` — pickup `CampaignTask` con FOR UPDATE SKIP LOCKED + dispatch + status transition + audit row.
- `test_scheduler_tick.py` — pickup `Campaign.status='scheduled' AND scheduled_at ≤ now()` → invoke orchestrator. Idempotente (re-tick no duplica).
- `test_segment_refresh_tick.py` — STATIC segments con campaigns running → `SegmentService.snapshot()` ejecutado. Skip DYNAMIC.
- `test_audit_retention_task.py` — purge rows > 90d. Idempotent (re-run no error).

### Layer D — Architecture (introspection + AST scan)

- `test_campaigns_orchestrator_idempotent.py` — `CampaignOrchestrator.launch` decorada con `@idempotent` (AST scan).
- `test_campaigns_workers_registered.py` — `WorkerSettings.functions` contiene los 4 ARQ functions nuevos + `SchedulerSettings.cron_jobs` contiene los 3 crons (scheduler_tick + segment_refresh_tick + audit_retention).
- `test_channel_router_registry_invariants.py` — `TelegramChannelRouter` implements `ChannelRouter` Protocol (`isinstance(router, ChannelRouter)`).
- `test_campaigns_audit_log_retention.py` — `purge_old_campaigns_audit` worker function existe + retention env-tunable + cron job registrado.

### Migration

- Test idempotency clone-DB (regla `backend-migrations.md`): apply migration 113, re-apply, verify table exists once + indexes.

### Integration (sin mocks de service, política F-7 PR-4)

- `test_e2e_telegram_campaign_smoke.py` — fixture: tenant + lead con `telegram_id` + campaign DRAFT con 1 step Telegram + segment STATIC. Steps:
  1. `POST /campaigns/{id}/schedule` (now+5s).
  2. Trigger `run_campaign_scheduler_tick(ctx)` manualmente.
  3. Verifica orchestrator invocado + tasks creadas.
  4. Trigger `run_campaign_execution_task(ctx, task_id)` manualmente.
  5. Verifica `httpx mock` recibió request a Telegram API con tenant locale formatting.
  6. Verifica `CampaignTask.status='sent'` + audit rows (`task_dispatched`, `task_sent`).

## Aceptación

- [ ] `/test-backend` 13 gates verde (ruff + format + mypy strict 8 domains + arch fitness + coverage 43% + verify + integration + migration idempotency + jscpd 5% + interrogate 85% + pip-audit)
- [ ] 4 arch tests nuevos verde + 0 regresión en existentes
- [ ] Migration 113 idempotente verificada con clone DB
- [ ] Cobertura tests application + infrastructure + workers ≥ 80% del nuevo código
- [ ] Cero código en `campaigns/` que importe `sales_agent/` o `copilot/` (regla cross-module)
- [ ] `OutboundRateLimiter.check` + `ComplianceService.check` wired en `TelegramChannelRouter.send` (audit verifica callsites en REVIEW)
- [ ] Circuit breaker OPEN no causa worker crash (raises `CircuitBreakerOpenError` capturado, task marked `failed` con `error_code='circuit_open'`)
- [ ] Audit log retention 90d verificado: insert row con `created_at = utc_now() - 91d`, run worker, verify row deleted
- [ ] ARQ named queue `arq:campaigns_execution` configurada (env var) + `WorkerSettings` contiene comment con deploy split future-ready
- [ ] `IMPL-LOG.md` completo (sub-deliverables A-E + decisiones D15-D22 confirmadas + commits + decisión final ARQ pool deploy)
- [ ] `REVIEW.md` veredicto PASS
- [ ] `RESULT.md` escrito por `/pm`
- [ ] `current-state/campaigns.md` actualizado con lineage PR-5 (S2 SHIPPED)
- [ ] Decisiones D15-D22 registradas en `pis/active/PI-1-campaigns-module/decisions.md`
- [ ] Spanish neutro LATAM en docstrings + DTO descriptions + audit event_type values

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Worker pool saturated por ETL existente bloquea outbound dispatch | Queue dedicada `arq:campaigns_execution` + max_jobs=20 (D16) | architect |
| Circuit breaker OPEN per-tenant cae cascade global si bug | Test isolation per-(channel,tenant_id) key + chaos test simulado | builder |
| Custom CB bug (no production-tested) | Property-based test Hypothesis state machine + mirror semantics pybreaker docs | architect |
| Telegram API rate limit hit (30 msg/sec global, 1/sec per chat) | OutboundRateLimiter pre-send + circuit breaker on 429 + audit `rate_limited` | builder |
| Idempotency-Key Telegram race window (worker A + worker B same task) | `FOR UPDATE SKIP LOCKED` en CampaignTask query + IdempotencyStore set_if_not_exists antes de POST | architect |
| Audit log table balloon 1000 clientes | Retention 90d + index `(created_at)` para purge fast + tunable env | architect |
| Migration 113 conflicts con ALTER existing tabla | NEW table only (`campaigns_audit`), zero ALTER otras tablas → cero conflicto | builder |
| Conflict sesiones paralelas (PI-2 PR-2 suggestions-engine) | Paths disjuntos. Solo `workers/settings.py` shared — APPEND functions, no remove existing (regla M8). Pull antes commit (M5). | builder |
| Worker `run_campaign_scheduler_tick` colisiona con `run_tick_scheduler` analytics existente | Nombre distinto + cron minutes coordinated (analytics ya en `minute=set(range(60))` cada minuto; campaigns también cada minuto pero offset minute={5,15,25,35,45,55} para evitar pile-up) | architect |
| Tests integration crean rows en DB real → flaky CI | Fixture per-test usa transaction rollback + httpx mock Telegram | builder |
| `CampaignOrchestrator.launch()` lock long en Campaign row | Lock microseg en SQLA atomic block + atomic insert batch + outbox enqueue (D22). | architect |
| Master-data: Telegram message body no respeta tenant locale (timezones, currency) | `infrastructure/channels/shared.py` aplica `formatTenantDate*()` + `build_money_display()` antes de send | architect |
| Audit JSONB payload contiene PII (telegram_id leak) | Sanitizer en `AuditLogService.record(...)` redacta PII patterns (regla pii-sanitisation.md) | builder |
| `BudgetGuard` no wired aquí confunde audit | DOC explícito en docstring orchestrator: "PR-5 NO wirea BudgetGuard — campaigns no LLM. PR-6 + S3 wirean copilot/sales_agent" | architect |
