# KICKOFF-PROMPT — S3-mvp-telegram (PI-1-campaigns-module)

> Pegá el bloque ``` siguiente en una conversación nueva Claude Code para arrancar S3 autónomo end-to-end. Mismo paradigma que S2 (orchestrator + builder + auditor sub-spawns).

```
Sos main orchestrator. Ejecutá S3-mvp-telegram de PI-1-campaigns-module **autónomo end-to-end** con paradigma producto-vs-proyecto Nicolify.

**Framing Chris (CRÍTICO toda decisión arquitectónica):** "Hoy pocos clientes, mañana 1000. Robusto + escalable. Cuesta menos corregir hoy que mañana." → Cero deuda técnica, decisiones production-grade desde día 1.

**Estado pre-S3 (verificá `git log --oneline -30` + `current-state/campaigns.md`):**
- S0-foundation done: PR-1 outbox/idempotency PASS, PR-2 billing/compliance PASS
- S1-domain-campaigns done: PR-3 domain+repos PASS, PR-4 application+API PASS
- S2-orchestrator done: PR-5 orchestrator+workers PASS, PR-6 consumers-cutover PASS
- Surface disponible:
  - `shared/billing/`: PlanService, BudgetGuard, OutboundRateLimiter, plan_config table editable Streamlit
  - `shared/compliance/`: ComplianceService 4 policies (WABA24h + OptIn DB-backed + Blacklist + CountryBlock)
  - `shared/domain_events/outbox/`: OutboxService.enqueue + dispatcher + EventBusAdapter (3 flags ON: sales_agent + copilot + brand)
  - `shared/idempotency/`: @idempotent decorator + IdempotencyStore
  - `shared/billing/application/llm_guards.py`: BudgetGuardingChatModel + BudgetGuardingLLMService wrappers
  - `shared/billing/infrastructure/pricing_snapshot_repo_async.py`: LRU TTL cache
  - `shared/agent_observability/`: agent_kind="campaign" registrado
  - `modules/campaigns/`: domain + 4 application services + 23 endpoints REST + CampaignOrchestrator REAL + 4 ARQ workers + TelegramChannelRouter v1 + ChannelRouterRegistry + CB Redis-backed + audit log retention 90d
  - `modules/sales_agent/`: ConversationPipeline DI budget_guard wired
  - `modules/copilot/`: build_deep_agent_graph DI budget_guard + tenant_id wired
- Riesgos abiertos:
  - DR-7 brand BudgetGuard wiring 7 LLM callsites diferido → S3
  - `_resolve_telegram_id` STUB en TelegramChannelRouter → S3 wirea real CRM lookup
  - `format_message_for_tenant_locale` placeholder → S3 wirea tenant timezone/currency real
  - sales_agent OutboundOrchestrator NO existe (objetivo principal S3)
  - Inbound reply recognition NO existe (objetivo S3)
  - 4 stale assertions `test_outbox_adapter_integration.py FlagOff` follow-up no bloqueante

**Lectura obligatoria al iniciar:**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S2-orchestrator/handoff.md` — surface heredada S2
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S3-mvp-telegram/sprint.md` — plan tentativo 3 PRs
3. `docs/pm-nico/pis/active/PI-1-campaigns-module/PI.md` — visión PI
4. `docs/pm-nico/current-state/{campaigns,copilot,sales-agent,iam,brand,offer,crm,connections}.md`
5. `.claude/rules/{backend-ddd,tenant-isolation,backend-migrations,architectural-fitness,master-data,currency-handling,parallel-safety,git-safety,tdd-mandatory,sales-agent-brand-voice}.md`
6. **Schema vivo** sales_agent (architect lee ANTES escribir CONTRACT):
   - `backend/src/modules/sales_agent/application/orchestrator/conversation_pipeline.py` (DI patrón)
   - `backend/src/modules/sales_agent/application/orchestrator/state.py` (AgentState shape)
   - `backend/src/modules/sales_agent/application/orchestrator/chat.py` (ChatOrchestrator)
   - `backend/src/modules/sales_agent/application/agents/sales/nodes.py` (specialist nodes)
   - `backend/src/modules/sales_agent/application/orchestrator/compose.py` (slot system)
7. Schema vivo campaigns:
   - `backend/src/modules/campaigns/application/services/orchestrator.py` (CampaignOrchestrator)
   - `backend/src/modules/campaigns/infrastructure/channels/telegram.py` (_resolve_telegram_id STUB)
   - `backend/src/modules/campaigns/workers/execution_task.py`
   - `backend/src/modules/campaigns/api/routers/campaigns_router.py` (launch endpoint)

**S3 = 3 PRs:**

**PR-7-outbound-orchestrator** (esfuerzo L)
- `sales_agent/application/orchestrator/outbound_orchestrator.py` NEW: paralelo a ChatOrchestrator (non-breaking)
- `AgentState` extension: campos opcionales `campaign_id: UUID | None`, `campaign_instructions: str | None`, `outbound_mode: bool = False`
- `compose.py`: nuevo slot `CAMPAIGN_CONTEXT` (después de slot 5 BRAND_VOICE) — inyecta campaign_instructions cuando outbound_mode=True
- Supervisor routing: `outbound_mode=True` + `score≥40` → skip qualifier, ir directo a closer
- `campaigns/infrastructure/external/sales_agent_adapter.py` NEW: bridge CampaignTask → OutboundOrchestrator (consume CampaignTask en execution_task worker)
- Wire real `_resolve_telegram_id` via CRM port (cierra DR-7 PR-5 stub)
- Wire `format_message_for_tenant_locale` real lookup tenant timezone/currency (cierra DR-7 PR-5 placeholder)
- Voice fidelity grader threshold ≥0.7 prod en tests
- Tests integration F-7 sin mocks (política PR-4)
- 2 arch tests: outbound_orchestrator non-breaking + campaign_state slots additive

**PR-8-inbound-recognition-and-inbox-tag** (esfuerzo M)
- `sales_agent/application/orchestrator/chat.py` MOD: inbound reply recognition — busca CampaignTask SENT últimas 24-48h por (tenant_id, lead_id) → inyecta campaign_id en AgentState pre-routing
- `crm/api/inbox.py` MOD: tag "campaña: {name}" en conversaciones cuando AgentState.campaign_id presente
- `frontend/src/features/inbox/` MOD: render tag campaign en conversation list + detail
- `campaigns/api/routers/campaigns_router.py` NEW endpoint: `GET /api/v1/campaigns/{id}/stats` (SENT / RESPONDED / CONVERTED) con response_model + tenant isolation
- DTO `CampaignStatsResponse`: campos `total_tasks, sent_count, responded_count, converted_count, conversion_rate, response_rate, currency: str | None` (master-data si monetario)
- Tests integration F-7 + 1 arch test (response_model + tenant_id filter en stats query)

**PR-9-e2e-and-manual-test** (esfuerzo S)
- `frontend/e2e/campaign-launch-telegram.spec.ts` Playwright (mock Telegram API):
  - Crear campaign DRAFT → add 1 step Telegram → schedule (now+5s) → trigger scheduler tick → verify task status sent + audit row
- `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S3-mvp-telegram/manual-test-checklist.md`: proceso Chris envía campaña a 5+ contactos reales staging
- Sin nuevo código BE/FE significativo (solo test E2E + checklist).

**Decisiones architect a tomar (1000 clientes lens, ZERO open questions ideal):**
1. AgentState extension shape — additive opt-in (`campaign_id: UUID | None = None`) vs nuevo dataclass `OutboundContext` separado.
2. `outbound_mode` propagation — flag a nivel state vs derivado de `campaign_id is not None`.
3. Inbound recognition window — 24h conservador (PR.md sugería) vs 48h tunable env. Lead responde 3 días después → fallback "no campaign context" no rompe.
4. Voice fidelity grader threshold prod (≥0.7 default? tunable per-tenant?).
5. Sales_agent adapter — reuse existing `connections/external/manychat/` pattern vs nuevo módulo.
6. CampaignStats query strategy: live DB query (p95 < 200ms con index) vs MV refresh 5min (cron). Cron más resilient pero stale.
7. Inbox tag rendering — chip Shadcn + clickable link a `/campañas/{id}` o solo label estático.
8. CRM port para `_resolve_telegram_id` — extend existing `LeadQueryServiceImpl` con method `get_telegram_id(lead_id, tenant_id)` o nuevo `LeadChannelPort`.

**Workflow autónomo per PR:**

1. **Bootstrap PR folder** (mkdir + cp templates desde `docs/pm-nico/process/pr-folder-template/`)
2. **Spawn `nicolify-architect`** atomic PR.md spec + CONTRACT.md (zero open questions, framing 1000 clientes, schema vivo audit ANTES escribir)
3. **Spawn `nicolify-backend`** o `nicolify-agentic` (PR-7 LangGraph extension) TDD strict por sub-deliverable
   - Multi-spawn si pause — re-spawn focused commit-or-die
   - Cada spawn agentid → re-spawn fresh con context concreto
4. **Spawn `nicolify-frontend`** PR-8 (Inbox tag + stats endpoint si FE)
5. **Spawn `nicolify-backend-auditor`** + `nicolify-frontend-auditor` review producir REVIEW.md verdict mecánico
6. Si FAIL/WARN → spawn builder fix findings + auditor re-review hasta PASS
7. Cada PR cerrar con IMPL-LOG + current-state updates + commits docs

**Cierre S3 (PI-1 cierre potencial):**
1. Escribir `sprints/S3-mvp-telegram/handoff.md` (surface S3 → PI-2 multi-canal)
2. Escribir `sprints/S3-mvp-telegram/learnings.md`
3. Update `sprints/S3-mvp-telegram/sprint.md` Estado → done
4. **Si S4-crm-hub-lite también shipped:** PI-1 cierra completo
   - Escribir `pis/active/PI-1-campaigns-module/retro.md`
   - Mover folder completo a `pis/archive/PI-1-campaigns-module/`
   - Update roadmap.md: PI-1 → Done section
5. Commit final `docs(pm): cerrar sprint S3-mvp-telegram + handoff PI-2 + learnings + (PI-1 retro si aplica)`
6. Reportar status PI-1 (S0 + S1 + S2 + S3 done; S4 paralelo o pendiente)

**Reglas duras (siempre):**
- PROHIBIDO `git add .|-A|-u`. Stage por nombre exacto.
- `git pull` PROHIBIDO (regla parallel-safety M5). Si push falla non-fast-forward → STOP, reportar Chris.
- NO tocar files de sesiones paralelas (verificá `git status` cada inicio + boundaries M1).
- NO `--ignore`/`xfail`/`skip` para pasar CI. Fix root cause.
- NO `git stash` en sesiones paralelas (lección S2 — perdió WIP otra sesión).
- response_model OBLIGATORIO endpoints (regla pii-sanitisation).
- Tenant isolation cada query (regla tenant-isolation).
- AsyncSession código nuevo (regla backend-ddd).
- structlog (no print/logging).
- Native WSL ruff/mypy/pytest (no `docker exec`). Docker permitido SOLO `alembic upgrade` runtime.
- Migrations idempotentes raw SQL `IF NOT EXISTS`.
- Spanish neutro LATAM en docstrings/UI strings (excepto sales_agent output que respeta voz tenant).
- **sales-agent-brand-voice.md regla SACRA:** NO crear tabla brand_voice_summary, NO fine-tuning per tenant, NO voice-rewriter LLM pass post-generación, NO hardcodear voz, NO inyectar `{tenant_name}` mid-block cache prefix. Voz tenant SSoT = `personality_profiles.system_instruction`.

**Sesiones paralelas:** verificá al inicio `git log --oneline -10` + `git status --short`. Identificar files M ajenos (PI-2 S3 PR-1 cleanup-modeltier-convergence puede estar activo) — NO TOCAR. Boundaries M1: PR siguiente debe ser módulo distinto cuando posible.

**Contexto Opus 4.7 1M:** tenés ~700k tokens libres. Spawn agents productivos sin restricciones excesivas. Si builder pause >2 spawns en mismo issue → diagnostic exacto desde main session + spawn quirúrgico.

**Filosofía cero deuda:** auditor catch findings → builder fix antes ship. Patrón política dual: unit tests con mocks + 1 integration test sin mocks per surface crítica (lección F-2 PR-4 + lección PR-5 Sub-G F-1/F-2/F-3 caught real bugs enmascarados).

**Patrón architect autónomo cristalizado:**
- Lee schema vivo SQLA + sales_agent state shape + LangGraph compose ANTES escribir CONTRACT (atrapa drift early)
- Cada decisión arquitectónica documenta razón "1000 clientes" + alternativa considerada + por qué rechazada
- ZERO open questions PM ideal — autonomía completa con framing claro
- Si drift detectado entre PR.md spec y schema real → flag + resolve PM main session

**Cierre cuestiones DR S2:**
- DR-7 brand BudgetGuard 7 callsites — incluir en S3 PR-7 (1000 clientes lens, no más diferral)
- DR-8 quality_eval workers BudgetGuard — incluir en PR-7 follow-up scope
- DR-9 nest_asyncio dep tracking — solo doc, sin acción
- 4 stale assertions outbox_adapter_integration FlagOff — Sub-deliverable PR-8 quick fix

**Reportá a Chris brief tras cada hito (architect done / builder done / auditor done / sprint cerrado).** Caveman mode terse OK. Si bloqueante real → pausá + reportá opciones (no continúes infinito).

Empezá leyendo handoff.md S2 + sprint.md S3 + verificando estado git limpio. Después bootstrap PR-7 folder + spawn architect.
```

## Cómo usar

1. Abrí nueva conversación Claude Code en repo `/home/chris/AISALESHT`
2. Activa caveman mode si querés (`/caveman` o automático)
3. Pegá el bloque ``` arriba completo
4. Claude arranca S3 autónomo

**Path de este archivo:** `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S3-mvp-telegram/KICKOFF-PROMPT.md`
