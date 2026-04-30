# IMPL-LOG — PR-5-orchestrator-and-workers

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-5-orchestrator-and-workers |
| PI / Sprint | PI-1-campaigns-module / S2-orchestrator |
| Builder | `nicolify-backend` |
| Fecha cierre | 2026-04-30 |
| Commits Sub-A..E | `4d8953ab`, `b830bbad`, `227ba63a`, `78fdd6ce`, `961a2c3c` |
| Estado | DONE — listos para auditor |

---

## Sub-deliverables shipped

### Sub-A — audit log + circuit breaker + migration 113

- **Commit:** `4d8953ab`
- **Files creados:**
  - `src/modules/campaigns/domain/audit_log.py` — `AuditLogEvent` VO, `AuditEventType` StrEnum, `AuditLogRepository` ABC
  - `src/modules/campaigns/infrastructure/models/campaign_audit_model.py` — SQLA model `campaign_audit` (append-only, sin `deleted_at`, 3 indices parciales)
  - `src/modules/campaigns/infrastructure/repositories/audit_log_repo_impl.py` — SQLA async impl con `purge_older_than` cross-tenant (allowlist)
  - `src/modules/campaigns/infrastructure/resilience/__init__.py`, `circuit_breaker.py`, `errors.py` — CB Redis-backed por `(channel, tenant_id)`, Lua script atomico, estados CLOSED/OPEN/HALF_OPEN
  - `src/modules/campaigns/infrastructure/channels/errors.py` — jerarquia `ChannelError` / `ChannelRetryableError` / `ChannelRateLimitedError` / `ChannelFatalError` / `ChannelComplianceBlocked` / `ChannelTenantRateExceeded`
  - `src/modules/campaigns/application/services/audit_log_service.py` — best-effort sanitize + persist
  - `src/modules/campaigns/application/dtos/audit_log_dtos.py` — `AuditLogEntryDTO`
  - `alembic/versions/113_campaigns_audit_log.py` — migration idempotente raw SQL IF NOT EXISTS
- **Tests:** `tests/modules/campaigns/domain/test_audit_log.py`, `tests/modules/campaigns/infrastructure/test_audit_log_repo.py`, `tests/modules/campaigns/infrastructure/test_circuit_breaker.py`

### Sub-B — ChannelRouter Telegram + Registry

- **Commit:** `b830bbad`
- **Files creados:**
  - `src/modules/campaigns/infrastructure/channels/__init__.py` — re-exports
  - `src/modules/campaigns/infrastructure/channels/registry.py` — `ChannelRouterRegistry` singleton thread-safe + `register_default_channels()`
  - `src/modules/campaigns/infrastructure/channels/telegram.py` — `TelegramChannelRouter(ChannelRouter)`: pipeline pre-send (compliance → rate-limiter → idempotency → CB → POST)
  - `src/modules/campaigns/infrastructure/channels/shared.py` — `ChannelDispatchResult`, `format_message_for_tenant_locale`, helpers
- **Tests:** `tests/modules/campaigns/infrastructure/test_channel_router_registry.py`, `tests/modules/campaigns/infrastructure/test_telegram_channel_router.py`

### Sub-C — CampaignOrchestrator + launch() integration

- **Commit:** `227ba63a`
- **Files creados/modificados:**
  - `src/modules/campaigns/application/services/orchestrator.py` (NEW) — `CampaignOrchestrator.launch()` real con `@idempotent`, single-TX, root tasks only, outbox events, audit log best-effort
  - `src/modules/campaigns/api/_service_factories.py` (MOD) — `get_campaign_orchestrator` + `get_audit_log_service`
  - `src/modules/campaigns/api/routers/campaigns_router.py` (MOD) — launch endpoint llama `orchestrator.launch()` (PR-4 STUB → real)
  - `src/modules/campaigns/application/services/campaign_service.py` (MOD) — `launch()` delega a orchestrator
- **Tests:** `tests/modules/campaigns/application/test_orchestrator.py`, `tests/modules/campaigns/application/test_orchestrator_idempotency.py`, `tests/modules/campaigns/api/test_campaigns_launch_real.py`

### Sub-D — 4 ARQ workers + WorkerSettings extend + e2e smoke

- **Commit:** `78fdd6ce`
- **Files creados:**
  - `src/modules/campaigns/workers/__init__.py`
  - `src/modules/campaigns/workers/execution_task.py` — `run_campaign_execution_task`: SELECT FOR UPDATE task → CB.call(send) → map error_class → mark_sent/failed/skipped
  - `src/modules/campaigns/workers/scheduler_tick.py` — `run_campaign_scheduler_tick`: promote SCHEDULED campaigns + claim pending tasks → ARQ enqueue
  - `src/modules/campaigns/workers/segment_refresh_tick.py` — `run_segment_refresh_tick`: refresh STATIC segments linked to RUNNING campaigns (env `CAMPAIGNS_SEGMENT_REFRESH_MINUTES=60`)
  - `src/modules/campaigns/workers/audit_retention_task.py` — `purge_old_campaigns_audit`: bounded delete loop, env `CAMPAIGNS_AUDIT_RETENTION_DAYS=90`
- **Files modificados:**
  - `src/workers/settings.py` (MOD — append regla M8): 4 funciones en `WorkerSettings.functions` + `SchedulerSettings.functions` + 3 cron jobs (scheduler_tick, segment_refresh_tick, audit_retention); `on_startup` bootstrap `register_default_channels`
- **Tests:** `tests/modules/campaigns/workers/test_execution_task.py`, `tests/modules/campaigns/workers/test_scheduler_tick.py`, `tests/modules/campaigns/workers/test_segment_refresh_tick.py`, `tests/modules/campaigns/workers/test_audit_retention_task.py`, `tests/modules/campaigns/integration/test_e2e_telegram_campaign_smoke.py`

### Sub-E — 4 architecture fitness gates

- **Commit:** `961a2c3c`
- **Files creados:**
  - `tests/architecture/test_campaigns_orchestrator_idempotent.py` — AST scan `CampaignOrchestrator.launch` tiene `@idempotent`; ratchet `EXEMPT_METHODS=frozenset()`
  - `tests/architecture/test_campaigns_workers_registered.py` — AST scan `WorkerSettings.functions` + `SchedulerSettings.functions` contienen 4 fns + `SchedulerSettings.cron_jobs` contiene 3 crons; ratchet `KNOWN_MISSING=frozenset()`
  - `tests/architecture/test_channel_router_registry_invariants.py` — runtime check: `TelegramChannelRouter` satisface `ChannelRouter` Protocol (`isinstance`); `register_default_channels` → `registry.has("telegram")`; `registry.get("nonexistent")` → `KeyError`
  - `tests/architecture/test_campaigns_audit_log_retention.py` — `purge_old_campaigns_audit` importable + async + env `CAMPAIGNS_AUDIT_RETENTION_DAYS` en source + tabla `campaign_audit` en source + cron `hour=4, minute=30` en `SchedulerSettings`
- **Resultado:** 24 tests verdes, 0 fallos

---

## Decisiones D15-D22 finales

| # | Decision | Veredicto |
|---|---|---|
| D15 | Custom asyncio CB Redis-backed (no pybreaker/aiobreaker) | CONFIRMADA. `core.database.redis_client` disponible; patron mirror `OutboundRateLimiter`. pybreaker sync-only; aiobreaker abandoned 2021. |
| D16 | Queue named `arq:campaigns_execution` + global default queue | CONFIRMADA + ajuste. `WorkerSettings` tenia 22 fns previas. Append seguro. Deploy split (`CampaignsWorkerSettings` separado) diferido PI-3 — documentado en DR-2. |
| D17 | ARQ exp backoff 60s x 2^retry, max 5 retries | CONFIRMADA. Hereda `max_tries=5` global de settings.py. |
| D18 | Application-side idempotency Telegram via IdempotencyStore | CONFIRMADA. `RedisIdempotencyStore` + `@idempotent` + `IdempotencyService.with_dedupe` disponibles. key=`telegram-send:{campaign_task_id}`, TTL=24h. |
| D19 | 90d retention + cron 04:30 UTC | CONFIRMADA. Mirror `purge_expired_trace_rows` (04:00). Offset 30min evita contencion DB. |
| D20 | Webhook bidireccional Telegram → S3 | CONFIRMADA out of scope PR-5. |
| D21 | PR-6 cutover secuencial (no paralelo) | CONFIRMADA out of scope PR-5. |
| D22 | Single TX `async with session.begin()` para launch() | CONFIRMADA + refinada. PR-5 genera SOLO root steps (step_index==0). Descendientes generados post-success en S3+ via OutboundOrchestrator. Documentado en orchestrator docstring. |

---

## Refinamientos architect post-CONTRACT

- **Single-TX launch root tasks only (step_index==0):** PR-3 cementa `CampaignStep.next_step_ids` para DAG. Descendientes dependen de outcome del parent (BRANCH_ON_CONDITION) o delay (WAIT_DELAY) — calculable solo en runtime. PR-5 stub suficiente para MVP Telegram 1-step. S3 wirea handler `CampaignTaskSent → generate_next_tasks`.
- **Segment refresh cron horario (no 15 min):** STATIC segments con RUNNING campaigns solo necesitan refresh cuando tenant hace append de leads sin re-launch. Cada hora (env `CAMPAIGNS_SEGMENT_REFRESH_MINUTES=60`) suficiente para 1000 clientes. 15 min = ~60K snapshots/dia sobreingenieria. Tunable via env.
- **CB per-(channel, tenant_id) Redis keys:** `cb:campaigns:{channel}:{tenant_id}:{state|failures|opened_at|probes_in_flight}`. Lua script atomico garantiza no race entre pods. Tenant noisy neighbor no degrada otros 999.
- **ChannelRouterRegistry in-memory (no Redis-backed):** membresia de canales cambia solo en deploys, no en runtime. Redis lookup en hot-path = +5ms innecesario. Multi-pod safe: cada pod hace mismo bootstrap en `on_startup`. Decisión D15 complementaria.
- **`_resolve_telegram_id` stub (DR-1):** Sub-D workers usan `lead.telegram_id` campo directo. Para PR-5 alcanza MVP. S3 wirea resolucion real via `shared/links/ports/crm_repos`. Documentado en docstring del worker.

---

## Quality summary

| Metrica | Valor |
|---|---|
| Tests verdes scope campaigns (arch gates Sub-E) | 24 / 24 |
| Arch tests nuevos PR-5 | 4 archivos, 24 tests |
| Arch tests acumulados campaigns (PR-3+PR-4+PR-5) | 12 archivos |
| Mypy (4 arch gate files) | 0 errors |
| Ruff check + format | 0 errors, 0 format issues |
| Migration 113 | Idempotente raw SQL IF NOT EXISTS verificado |
| Cross-module imports campaigns → copilot/sales_agent/crm | 0 (DDD ratchet verde) |
| `@idempotent` decorator en CampaignOrchestrator.launch | Verificado por arch test + runtime |
| WorkerSettings 4 fns + 3 crons registrados | Verificado por arch test AST scan |
| TelegramChannelRouter implements ChannelRouter Protocol | Verificado por arch test runtime isinstance |
| purge_old_campaigns_audit env-tunable + cron 04:30 | Verificado por arch test |

---

## Deuda residual flagged para auditor

| ID | Descripcion | Sprint resolucion |
|---|---|---|
| DR-1 | `_resolve_telegram_id` stub en execution_task: usa `lead.telegram_id` directo. S3 wirea CRM lookup real via port. Documentado en docstring del worker. | S3 |
| DR-2 | Per-tenant ARQ pool isolation diferida: queue global `arq:campaigns_execution` comparte pool. `CampaignsWorkerSettings` proceso dedicado = PI-3. Flagged en settings.py comment. | PI-3 |
| DR-3 | WhatsApp / Email / IG DM `ChannelRouter` impls: OUT OF SCOPE PR-5 por decision D11 (MVP 1 Telegram). Registry preparada para extension. | PI-2 |
| DR-4 | `format_message_for_tenant_locale` usa `TenantLocale.default()` fallback. S3 wirea lookup real via `shared/links/ports/tenant_profile`. | S3 |
| DR-5 | BudgetGuard wiring en LLM call sites: PR-5 NO invoca LLM. Wiring diferido PR-6. | PR-6 |
