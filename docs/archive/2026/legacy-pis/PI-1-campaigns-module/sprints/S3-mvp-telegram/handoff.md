# S3 Handoff — MVP Telegram → PI-2 Multi-canal Expansion

> Owner: PM. Cierre sprint S3, input para S4 (paralelo posible) + PI-2.

## Sprint cerrado

| Campo | Valor |
|---|---|
| Sprint ID | S3-mvp-telegram |
| Estado | done |
| Cierre real | 2026-04-30 |
| PRs shipped | PR-7 + PR-8 + PR-9 (3 PRs) |
| Commits totales | 16 (12 PR-7 + 3 PR-8 + 1 PR-9) + close docs |

## Surface disponible post-S3 (consumible por S4 + PI-2)

### Outbound conversational pipeline (PR-7)

- `OutboundOrchestrator.send_outbound(*, db, tenant_id, lead_id, campaign_id, campaign_instructions, channel_type, channel_adapter, budget_guard)` — single async entrypoint paralelo a ChatOrchestrator.
- `SalesAgentAdapter.dispatch(*, session, task, step, budget_guard)` — bridge CampaignTask + CampaignStep(step_type=CALL_SUBAGENT_BRIEF) → OutboundOrchestrator.
- AgentState additive: `campaign_id: UUID | None`, `campaign_instructions: str | None`, `outbound_mode: bool` (default False).
- Slot 7 `CAMPAIGN_CONTEXT` en `compose.py` POST `CHANNEL_FORMAT_HINT` — solo se inyecta cuando `outbound_mode=True`. Cache prefix slots 1-6 byte-equal across inbound/outbound preserve.
- Supervisor outbound skip-qualifier: `outbound_mode=True + lead_score>=40 → closer` BEFORE LLM call.
- `_resolve_telegram_id` real CRM port (cierra DR-7 STUB).
- `_resolve_tenant_locale` real `TenantModel.config_json["tenant_locale"]` + LRU cache 5min (cierra DR-7 placeholder).
- `get_guarded_llm_service(tenant_id, agent_kind, budget_guard, model_hint)` architectural seam en `shared/billing/application/llm_guards.py` — caller-provided DI pattern.
- ENV `SALES_AGENT_VOICE_FIDELITY_THRESHOLD` default 0.7 (golden test gate).

### Inbound recognition + stats + inbox tag (PR-8)

- `CampaignsLookupPort` ABC + `create_campaigns_lookup_port` factory en `shared/links/ports/campaigns.py` — DDD port for cross-module reads.
- `chat.py::process_chat_flow` injects `campaign_id` cuando lead responde dentro de `CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS` (default 24, [1,72]). NO activates outbound_mode (inbound real).
- `inbox_campaign_enrichment` service enriquecen closer_studio conversation list/detail con `campaign_id` + `campaign_name` optional fields.
- `CampaignTag.tsx` Shadcn Badge chip clickable to `/campañas/{id}` en `frontend/src/features/closer-studio/components/inbox/`.
- Endpoint `GET /api/v1/campaigns/{campaign_id}/stats` con `CampaignStatsResponse`: total_tasks, sent_count, responded_count (proxy), converted_count (DEFER=0 attribution_method enum), response_rate, conversion_rate, currency (master-data).

### E2E + manual gate (PR-9)

- Playwright spec `frontend/e2e/specs/regression/sales/campaign-launch-telegram.spec.ts` — 2 sanity tests + 1 full flow test.skip (infra gap documentado).
- Manual test checklist Chris staging real — 8 sections + verdict gate.

## Decisiones architect tomadas (S3 — D-28 a D-47)

Ver `learnings.md` § "Decisiones tomadas durante S3" tabla. Append a `pis/active/PI-1-campaigns-module/decisions.md` pendiente PM.

## Riesgos abiertos S3 (input PI-2 / S4)

| Riesgo | Mitigación PI-2/S4 | Owner |
|---|---|---|
| Brand 7 callsites BudgetGuard runtime wiring DEFERRED | S4: FastAPI provider + ARQ worker startup DI para construir BudgetGuard request-scope | architect S4 |
| Sub-H quality_eval workers BudgetGuard wiring DEFERRED | S4: ARQ WorkerSettings.on_startup DI | architect S4 |
| Voice fidelity outbound multi-turn runner xfail | S4: `SalesAgentJudge.evaluate_conversation` extension multi-turn aggregation | builder S4 |
| Exact `converted_count` attribution proxy (defer) | PR follow-up post S3: cross-module payment + scheduling lookup integration | architect post S3 |
| chat.py PLR0915 noqa | Cleanup post PI-1: refactor `_recognize_inbound_campaign` helper | builder cleanup |
| Routes `/campañas/nuevo` + `/campañas/{id}` placeholder | S4 / PI-3: actual CRM hub UI implementation | frontend S4/PI-3 |
| ARQ scheduler tick manual trigger endpoint pendiente | Cleanup post PI-1: admin-only `/api/v1/_test/scheduler-tick` endpoint | backend cleanup |
| DB seed helper tenant + lead + telegram_id staging | Cleanup post PI-1: reusable fixture across E2E specs | E2E setup cleanup |

## Commits PR-7 (12)

- `9200b6cc` — feat(sales-agent): PR-7 Sub-A AgentState outbound additive
- `90ad4d64` — feat(sales-agent): PR-7 Sub-A.5 slot CAMPAIGN_CONTEXT compose.py
- `db9fa4b8` — feat(sales-agent): PR-7 Sub-B OutboundOrchestrator + integration test
- `32461f9c` — feat(sales-agent): PR-7 Sub-C supervisor outbound skip qualifier
- `4a3b7383` — feat(crm): PR-7 Sub-E lead_telegram_id port + Telegram channel wire
- `b308cbff` — feat(campaigns): PR-7 Sub-F tenant locale real lookup + LRU cache
- `d7fc7288` — feat(billing): PR-7 Sub-G get_guarded_llm_service helper (caller-provided DI)
- `ec446540` — feat(campaigns): PR-7 Sub-D SalesAgentAdapter + worker dispatch branch
- `db16ecc9` — test(sales-agent): PR-7 Sub-I voice fidelity outbound golden
- `f58016d7` — test(architecture): PR-7 Sub-J non-breaking + state additive arch gates
- `cfe6d062` — docs(pm): PR-7 IMPL-LOG.md + current-state updates (Sub-K)
- `9075ca2c` — docs(pm): PR-7 IMPL-LOG.md update Sub-D commit hash
- `c08abe3d` — docs(pm): PR-7 close — RESULT.md shipped + PR-folder atómico

## Commits PR-8 (3 + close)

- `e5bd8448` — feat(frontend-inbox): PR-8 Sub-C campaign tag chip + click navigation
- `7bed7dea` — feat(campaigns): PR-8 Sub-A+B+D inbound recognition + stats endpoint + inbox tag
- `bda7bb2e` — docs(pm): PR-8 close — IMPL-LOG + RESULT + PR-folder atómico

## Commits PR-9 (1)

- `fba7f591` — feat(test-e2e): PR-9 Playwright spec + manual test checklist

## Recommended skills S4 / PI-2

- `nicolify-architect` — FastAPI provider design para BudgetGuard request-scope DI (S4 destrabe DR-7 + DR-8); CRM Hub Lite contracts API forward-compatible.
- `nicolify-frontend` — `/sales/contactos` page + DataTable + filters + segment manual creation (S4).
- `nicolify-agentic` — `SalesAgentJudge.evaluate_conversation` multi-turn extension (S4 voice fidelity gate).
- `chrome-devtools-verify` — Live verification staging post-merge.

## Quality summary

- **Tests:** PR-7 94 verde + PR-8 59 verde (52 BE + 7 FE) + PR-9 2 sanity = ~155 nuevos S3.
- **Arch tests:** suite global verde post-S3 con +3 nuevos (PR-7 +2 + PR-8 +1).
- **Ruff:** clean post-fix loops.
- **Mypy:** strict scope domain verde.
- **Migrations:** 0 nuevas en todo S3.
- **Auditor verdicts:** PR-7 PASS (REVIEW.md fallback main session — auditor agent paused) + PR-8 PASS (fallback) + PR-9 PASS (manual gate Chris).
- **Cero deuda técnica blocker:** todos findings críticos / altos resueltos antes ship. M-1/M-2/etc. son medium DEFER S4 con architectural seam ready y follow-up documented.
- **Deuda residual aceptada DOCUMENTED:** ver tabla riesgos abiertos arriba.

## S3 cierre verdict

**SHIPPED** — MVP 1 Telegram outbound funcional end-to-end. Real ship verdict pendiente Chris execution manual checklist staging.

**Próximo sprint:** S4-crm-hub-lite (paralelo a follow-up cleanups). PI-1 cierre cuando S4 también shipped.
