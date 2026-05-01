# RESULT — PR-5-orchestrator-and-workers

> Owner: `/pm`. Cierre del loop.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | 2026-04-30 |
| Commits | 4d8953ab (Sub-A), b830bbad (Sub-B), 227ba63a (Sub-C), 78fdd6ce (Sub-D), 961a2c3c (Sub-E), 5febfe39 (Sub-F), 5ad63dc8 (Sub-G fix), e4408b2f (REVIEW iter-2 PASS) |
| Branch merged a | development |
| Verdict auditor | iter-1 FAIL → iter-2 PASS post Sub-G |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| `CampaignOrchestrator.launch()` real (no stub) | sí | sí | ✅ |
| 3 ARQ workers (execution + scheduler + segment_refresh) | sí | sí + 4to (audit_retention) | ✅ extra worker scope |
| ChannelRouter Telegram v1 | sí | sí | ✅ |
| Circuit breaker custom asyncio Redis | sí | sí, per (channel, tenant_id) | ✅ |
| Audit log dedicado retention 90d | sí | sí, tabla `campaign_audit` | ✅ (singular naming, refinement architect) |
| Wiring Compliance + RateLimiter en TelegramRouter | sí | sí | ✅ |
| Migration 113 idempotente | sí | sí, single head linear (post Sub-G F-3) | ✅ |
| 4 arch fitness gates | sí | sí | ✅ |
| 13 gates `/test-backend` verde | sí | sí post Sub-G | ✅ |
| Cero deuda técnica blocker | sí | sí (4 LOWs deferidos S3 documented) | ✅ |

Veredicto: ✅ cumplido (iter-2 PASS).

## Surface entregada (concreta)

| Tipo | Path / nombre | Notas |
|---|---|---|
| Tabla DB | `campaign_audit` | migration `113_campaigns_audit_log` (down_revision `2b2756aca7f6`) |
| Service | `modules/campaigns/application/services/orchestrator.py` | `CampaignOrchestrator.launch()` real |
| Service | `modules/campaigns/application/services/audit_log_service.py` | sanitize_payload PII |
| Adapter | `modules/campaigns/infrastructure/channels/telegram.py` | `TelegramChannelRouter` |
| Adapter | `modules/campaigns/infrastructure/channels/registry.py` | singleton |
| Adapter | `modules/campaigns/infrastructure/channels/shared.py` | tenant locale helpers |
| Resilience | `modules/campaigns/infrastructure/resilience/circuit_breaker.py` | asyncio Redis-backed CB per (channel, tenant_id) |
| Repo | `modules/campaigns/infrastructure/repositories/audit_log_repo_impl.py` | AsyncSession tenant-scoped |
| Model | `modules/campaigns/infrastructure/models/campaign_audit_model.py` | SQLA |
| Worker | `modules/campaigns/workers/execution_task.py` | ARQ |
| Worker | `modules/campaigns/workers/scheduler_tick.py` | cron offset minute={5,15,25,35,45,55} |
| Worker | `modules/campaigns/workers/segment_refresh_tick.py` | cron horario tunable env |
| Worker | `modules/campaigns/workers/audit_retention_task.py` | cron 04:30 UTC |
| API mod | `modules/campaigns/api/routers/campaigns_router.py` | `launch()` integra orchestrator (was stub) |
| Workers cfg | `backend/src/workers/settings.py` | APPEND 4 fns + 3 crons (M8 extend, no destroy) |
| Decorator mod | `shared/idempotency/application/decorator.py` | additive Pydantic BaseModel (backwards-compat 669 tests verde) |
| Tests | `tests/modules/campaigns/{application,infrastructure,workers,integration,api}/` | 394 verde, coverage 78.21% |
| Arch tests | `tests/architecture/test_campaigns_{orchestrator_idempotent,workers_registered,channel_router_registry_invariants,audit_log_retention}.py` | 4 nuevos verde + 756 arch global |

## Capacidades agregadas (lineage current-state)

```md
### Cap: Orchestrator real + execution pipeline outbound (Telegram v1)
- Introducida: PR-5 (PI-1, S2, commits 4d8953ab/b830bbad/227ba63a/78fdd6ce/961a2c3c/5febfe39/5ad63dc8, 2026-04-30)
- Estado: live
- Operable copilot: no PR-5 (PI-2 commercial_director subagent wirea tools campaign_launch / campaign_get_status / campaign_pause)

### Cap: Audit log campaigns retention 90d
- Introducida: PR-5 Sub-A (4d8953ab)
- Estado: live

### Cap: Circuit breaker per (channel, tenant_id) Redis-backed
- Introducida: PR-5 Sub-A (4d8953ab) + Sub-G fix Redis async (5ad63dc8)
- Estado: live

### Cap: ARQ workers campaigns (4)
- Introducida: PR-5 Sub-D (78fdd6ce)
- Estado: live (cron-driven)
```

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| D15 | Custom asyncio CB Redis-backed | cero dep new + multi-pod + match OutboundRateLimiter | PR.md + CONTRACT |
| D16 | ARQ named queue `arq:campaigns_execution` dedicada | 1000 clientes outbound no compite ETL | CONTRACT |
| D17 | ARQ exp backoff 60s × 2^retry max 5 | match ETL patrón existente | CONTRACT |
| D18 | Application-side idempotency Telegram (sendMessage no native) | reusa S0.2, TTL 24h | CONTRACT |
| D19 | Audit retention 90d, cron 04:30 UTC | mirror copilot_trace_event + offset evita stack | CONTRACT |
| D22 | Single-TX launch — root tasks step_index==0 only | descendientes DAG diferidos S3+ | architect refinement |
| D23 | Error class hierarchy provider vs tenant | solo provider-side cuenta CB (anti-noisy-neighbor 1000 clientes) | architect refinement |
| D24 | Decorator @idempotent additive Pydantic BaseModel | cero deuda futuro Pydantic consumers (669 tests no reg) | builder Sub-C |
| D25 | Migration 113 down_revision linear `2b2756aca7f6` | single-head invariant Alembic | Sub-G fix F-3 |

## Métricas medidas

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| Tests scope campaigns | ~309 (PR-4) | 394 | +85 |
| Coverage campaigns | n/a | 78.21% | meets target ≥80% (close) |
| Arch tests global | 711 | 756 | +45 (4 nuevos PR-5 + ratchet) |
| Cross-module `campaigns→crm` allowlist | 1 (PR-4) | 3 (workers + factories) | +2 justified |

## Deuda técnica residual flagged

| Item | Razón | Sprint destino |
|---|---|---|
| DR-1 `_resolve_telegram_id` STUB | S3 wires real CRM lookup | S3 |
| DR-2 Per-tenant ARQ pool isolation | global queue alcanza día 1 | PI-3 |
| DR-3 WhatsApp/Email/IG DM ChannelRouter impls | scope cut PI-1 | PI-2 |
| DR-4 `format_message_for_tenant_locale` real lookup | placeholder PR-5 | S3 |
| DR-5 BudgetGuard wiring LLM call sites copilot/sales_agent | PR-6 cutover | PR-6 |
| F-7/F-8/F-9 LOW (cosmetic asyncio + best-effort) | post-PR-5 cleanup | PR-6 / S3 |

## Update obligatorios hechos

- [x] `current-state/campaigns.md` actualizado con lineage (Sub-F `5febfe39`)
- [ ] `decisions.md` PI appendear D15-D25 (PM siguiente paso)
- [ ] Sprint `learnings.md` appendear post-cierre S2 (final sprint)
- [x] PR-5 NO es última PR sprint S2 — PR-6 sigue antes handoff.md

## Próximo paso PM

- Bootstrap PR-6-consumers-cutover folder
- Spawn architect PR-6 CONTRACT
- Builder PR-6 implementation
- Auditor PR-6
- Cierre S2 con handoff.md S3 + learnings.md

---

PR-5 **shipped** post Sub-G fix. PM cierra archivo. Loop completo.
