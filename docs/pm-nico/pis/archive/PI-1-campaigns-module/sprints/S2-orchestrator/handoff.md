# S2 Handoff — Orchestrator + Cutover → S3 MVP Telegram

> Owner: PM. Cierre sprint S2, input para S3.

## Sprint cerrado

| Campo | Valor |
|---|---|
| Sprint ID | S2-orchestrator |
| Estado | done |
| Cierre real | 2026-04-30 |
| PRs shipped | PR-5 (PASS post Sub-G) + PR-6 (PASS post Sub-G) |
| Commits totales | ~16 (PR-5: 8 + Sub-G fix) + ~8 (PR-6: 6 + Sub-G + REVIEW iter-2) |

## Surface disponible post-S2 (consumible por S3)

### Execution pipeline campaigns (PR-5)

- `CampaignOrchestrator.launch(campaign_id, tenant_id)` REAL — single-TX (lock + resolve segment + INSERT batch root tasks step_index==0 + outbox events + ARQ enqueue + audit log + commit). `@idempotent` ttl=300s.
- 4 ARQ workers registrados:
  - `run_campaign_execution_task` — FOR UPDATE SKIP LOCKED + ChannelRouter dispatch + retry exp backoff + audit log
  - `run_campaign_scheduler_tick` — cron offset minute={5,15,25,35,45,55} → orchestrator.launch
  - `run_segment_refresh_tick` — cron horario tunable env CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS
  - `purge_old_campaigns_audit` — cron 04:30 UTC retention 90d tunable env CAMPAIGNS_AUDIT_RETENTION_DAYS
- `TelegramChannelRouter` v1 (httpx 10s + idempotency + circuit breaker per (channel, tenant_id) + ComplianceService + OutboundRateLimiter wired)
- `ChannelRouterRegistry` singleton extensible (PI-2: WhatsApp/Email/IG DM)
- Circuit breaker custom asyncio Redis-backed (3 estados + per-(channel,tenant) key + tunable env)
- Audit log `campaign_audit` table (retention 90d, sanitize_payload PII)

### Cutover S0 → consumers reales (PR-6)

- `BudgetGuardingChatModel` + `BudgetGuardingLLMService` wrappers (`shared/billing/application/llm_guards.py`) — single enforcement point pattern.
- `PricingSnapshotRepoAsync` async repo + LRU TTL cache 256/300s.
- `BudgetExceeded` exception + `cost_estimator` (input + max_output tokens × pricing).
- Wiring puntos:
  - sales_agent: `ConversationPipeline.__init__(budget_guard, tenant_id)` DI optional
  - copilot: `build_deep_agent_graph(budget_guard, tenant_id)` DI optional → wrap llm antes de create_deep_agent
  - brand: outbox flag flip ON, BudgetGuard wiring DIFERIDO DR-7 (Sub-D-2/S3)
- 3 flags ENV `USE_OUTBOX_PATTERN_{SALES_AGENT,COPILOT,BRAND}` default `True`. Eventos routean a `domain_event_outbox` via `EventBusAdapter`.
- 2 architecture fitness gates ratchet shrink-only:
  - `test_budget_guard_pre_llm_call.py` — KNOWN_UNGUARDED 5 entries (brand 3 + workers 2)
  - `test_no_legacy_event_bus_publish.py` — KNOWN_DIRECT_LEGACY_EMITTERS empty (seeded clean)

## Decisiones architect tomadas (framing 1000 clientes)

| # | Decisión | Razón |
|---|---|---|
| 13 | Custom asyncio CB Redis-backed (vs pybreaker sync / aiobreaker abandoned) | cero dep new + multi-pod + match OutboundRateLimiter patrón |
| 14 | ARQ named queue `arq:campaigns_execution` dedicada | outbound dispatch no compite con ETL workers |
| 15 | ARQ exp backoff 60s × 2^retry max 5 | match patrón ETL workers existentes |
| 16 | Application-side idempotency Telegram (sendMessage no native) | reusa S0.2 IdempotencyStore TTL 24h |
| 17 | Audit retention 90d cron 04:30 UTC | mirror copilot_trace_event + offset evita stack |
| 18 | Single-TX launch — root tasks step_index==0 only | descendientes DAG diferidos S3+ post-success handler |
| 19 | Error class hierarchy provider vs tenant | solo provider-side cuenta CB (anti-noisy-neighbor 1000 clientes) |
| 20 | Decorator @idempotent additive Pydantic BaseModel | cero deuda futuro Pydantic consumers (669 tests no reg) |
| 21 | Migration 113 down_revision linear `2b2756aca7f6` | single-head invariant Alembic |
| 22 | Cutover order secuencial sales_agent → copilot → brand | blast radius bajo + rollback 1 line change |
| 23 | BudgetGuard estimation via model_pricing_snapshot | reservación 50% SA pool invariante |
| 24 | Wrapper pattern `BudgetGuardingChatModel`/`Service` (3 wiring points vs 18 callsites) | 1000 clientes — single enforcement, callsite nuevo gates auto |
| 25 | Retire policy = flag flip + cero direct emit | emisores YA usan adapter — flag flip ya retire |
| 26 | Brand BudgetGuard wiring DIFERIDO Sub-D-2 (DR-7) | sync LLMFactory.generate_response requiere per-callsite refactor |
| 27 | quality_eval workers en KNOWN_UNGUARDED (DR-8) | separate cron path no DI via __init__ |

## Riesgos abiertos S2 (input S3)

| Riesgo | Mitigación S3 | Owner |
|---|---|---|
| Brand 7 LLM callsites unguarded (DR-7) | S3 wirea per-callsite con `BudgetGuardingLLMService` o helper `_get_guarded_llm_service` | architect S3 |
| `_resolve_telegram_id` STUB en TelegramChannelRouter (PR-5) | S3 wirea real CRM lookup via LeadQueryServiceImpl | builder S3 |
| `format_message_for_tenant_locale` real lookup (PR-5) | S3 wirea tenant timezone/currency real | builder S3 |
| Quality eval workers BudgetGuard (DR-8) | Sub-G follow-up: wrap workers individually | builder follow-up |
| 4 stale assertions `test_outbox_adapter_integration.py FlagOff` | follow-up no bloqueante `chore(tests): update outbox flag-default assertions post-cutover` | builder follow-up |
| sales_agent OutboundOrchestrator NO existe | S3 implementa primer end-to-end Telegram outbound real | architect S3 |
| Inbound reply recognition NO existe | S3 implementa ChatOrchestrator busca CampaignTask SENT 24h → inyecta campaign_id en AgentState | builder S3 |
| FE `/campañas/*` UI NO existe | post PI-1 (S4 mini CRM Hub paralelo) | frontend |

## Commits PR-5 (8 + Sub-G fix + REVIEW iter-2)

- `4d8953ab` — Sub-A audit log + circuit breaker + migration 113
- `b830bbad` — Sub-B ChannelRouter Telegram + registry + compliance/rate-limiter wiring
- `227ba63a` — Sub-C CampaignOrchestrator.launch() real + API integration
- `78fdd6ce` — Sub-D 4 ARQ workers + WorkerSettings extend + e2e smoke
- `961a2c3c` — Sub-E 4 architecture fitness gates
- `5febfe39` — Sub-F IMPL-LOG + current-state
- `5ad63dc8` — Sub-G fixes F-1/F-2/F-3/F-4/F-5/F-6 (LeadQueryServiceImpl import + DDD allowlist + migration linear chain + test rewrite + Redis async + RedisSettings)
- `e4408b2f` — REVIEW.md iter-2 PASS

## Commits PR-6 (6 + Sub-G fix + REVIEW iter-2)

- `f8a4b3e5` — Sub-A BudgetGuardingLLMService + BudgetGuardingChatModel + PricingSnapshotRepoAsync
- `7b2de359` — Sub-B sales_agent flag flip + BudgetGuard wiring single point
- `8d2aed36` — Sub-C copilot flag flip + BudgetGuard wiring single point deep_agent
- `97780627` — Sub-D brand flag flip (BudgetGuard wiring DIFERIDO DR-7)
- `fb2683d0` — Sub-E 2 architecture fitness gates
- `6b8fcb11` — Sub-F IMPL-LOG + current-state
- `d3fbe665` — Sub-G fixes F-1 RUF100 + F-4 type-ignore comment
- `03d423c7` — REVIEW.md iter-2 PASS

## Recommended skills S3

- `nicolify-architect` — CONTRACT OutboundOrchestrator + AgentState campaign_id slot + supervisor routing
- `nicolify-agentic` — LangGraph integration sales_agent OutboundOrchestrator
- `sales-agent-expert` — voz brand + invariantes pool + non-breaking add OutboundOrchestrator paralelo a ChatOrchestrator
- `nicolify-frontend` — Inbox UI tag "campaña: {name}"
- `chrome-devtools-verify` — E2E browser verify

## Quality summary

- **Tests:** 394 verde scope campaigns (post-PR-5) + 29 nuevos integration F-7 (PR-6) = ~423 module tests
- **Arch tests:** 766 global verde (PR-5: 4 nuevos + PR-6: 2 nuevos = +6 ratchet expand)
- **Mypy:** 0 errors strict scope domain (campaigns + sales_agent + copilot + brand)
- **Ruff:** clean
- **Migration:** 113 idempotente single-head verificado clone-DB
- **Auditor verdicts:** PR-5 iter-1 FAIL → iter-2 PASS post Sub-G; PR-6 iter-1 WARN → iter-2 PASS post Sub-G
- **Cero deuda técnica blocker:** todos findings críticos PR-5 (F-1/F-2/F-3 CRITICAL + F-4 HIGH + F-5/F-6 MEDIUM) y PR-6 (F-1/F-4 MEDIUM) resueltos antes ship
- **Deuda residual aceptada DOCUMENTED:** DR-7 brand BudgetGuard, DR-8 quality_eval workers, DR-9 nest_asyncio tracking, audit obs F (4 stale assertions follow-up)

## Próximo sprint

S3-mvp-telegram inicio post-handoff. Prerequisito: bootstrap `prs/PR-7-{slug}/` folders cuando architect dicte firmas concretas. Foco S3:
- OutboundOrchestrator sales_agent (paralelo a ChatOrchestrator, non-breaking)
- AgentState campaign_id + campaign_instructions + outbound_mode slots
- Supervisor routing outbound_mode=True → skip qualifier para score≥40
- `campaigns/infrastructure/external/sales_agent_adapter.py` bridge CampaignTask → OutboundOrchestrator
- Inbound reply recognition (ChatOrchestrator busca CampaignTask SENT 24h → inyecta campaign_id)
- Inbox UI tag "campaña: {name}" en conversaciones (FE)
- Campaign analytics endpoint GET /campaigns/{id}/stats (SENT/RESPONDED/CONVERTED)
- E2E test crear campaign → launch → verificar Telegram messages reales
- Test manual Chris envía a 5+ contactos reales

S3 cierra cuando MVP 1 Telegram funcional end-to-end visible.
