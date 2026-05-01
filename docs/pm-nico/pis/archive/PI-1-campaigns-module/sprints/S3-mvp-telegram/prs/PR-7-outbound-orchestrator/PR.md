# PR-7-outbound-orchestrator

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-7-outbound-orchestrator |
| Sprint padre | S3-mvp-telegram |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | feature |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | — |

## Problema (user-facing)

Hoy `CampaignOrchestrator` (S2) entrega Telegram outbound como mensaje plano via `TelegramChannelRouter` con `_resolve_telegram_id` STUB → `None` → tarea SKIPPED. El user (creador LATAM) no ve outbound conversacional con voz de marca: ningún sales_agent corre con su `PersonalityProfile`, sus offers, su agent_identity. Las campañas type `AGENT_CONVERSATION` están bloqueadas en producción.

PR-7 cierra el MVP Telegram outbound: cuando `CampaignStep.step_type == CALL_SUBAGENT_BRIEF`, el worker dispatch va a `OutboundOrchestrator` (paralelo a `ChatOrchestrator` inbound) que reusa `agent_app` LangGraph + `ConversationPipeline.build_initial_state` + el slot system v2 con un nuevo Slot 6 `CAMPAIGN_CONTEXT` que NO rompe el cache prefix per-tenant.

## Outcome esperado

- Tenant lanza campaign `AGENT_CONVERSATION` Telegram → ARQ worker dispatcha → `SalesAgentAdapter` → `OutboundOrchestrator.send_outbound` → `agent_app.ainvoke(state, config={callbacks: [...]})` → `OutputManager.process_response` envía con voz de marca tenant.
- Voice fidelity grader prod ≥ 0.7 outbound (paridad con inbound).
- Brand `KNOWN_UNGUARDED` ratchet shrink **5 → 2** (3 brand callsites guarded; quality_eval workers stay si Sub-H deferral).
- DR-7 (`_resolve_telegram_id` STUB) cerrado: real CRM lookup `LeadModel.telegram_id`.
- Tenant locale real lookup en `_resolve_tenant_locale` (no más `TenantLocale.default()` hardcoded).
- ZERO regresión inbound (`outbound_mode=False` es default → chat path actual sin cambio).

Métrica: `sales_agent_quality_eval` weekly cron post-merge debe reportar ≥0.7 voice fidelity tanto inbound como outbound (1 fixture + golden conversación tenant real).

## Walking skeleton (mínimo viable cohesivo)

L cohesivo. Aprovecha Opus 4.7[1M] = scope amplio, módulos relacionados se diseñan junto:

1. `AgentState` extendido additive (`campaign_id`, `campaign_instructions`, `outbound_mode` opcionales) — sin tabla ni migración.
2. `compose.py` Slot 6 `CAMPAIGN_CONTEXT` — solo se inyecta cuando `outbound_mode=True`. Va DESPUÉS de Slot 5 `BRAND_VOICE` para preservar cache prefix per-tenant intacto (slots 1-5 contiguos invariantes per-tenant).
3. `OutboundOrchestrator` (NEW) — clase static paralela a `ChatOrchestrator` que reusa `ConversationPipeline.build_agent_identity / build_brand_voice / build_initial_state` (extendido para aceptar campaign fields).
4. Supervisor routing extension: `outbound_mode=True` AND `lead_score >= 40` → directo a `closer`. Sino routing normal (sin tocar inbound default).
5. `SalesAgentAdapter` (NEW en `campaigns/infrastructure/external/`) — bridge `CampaignTask + CampaignStep` → `OutboundOrchestrator.send_outbound`.
6. `execution_task.py` worker dispatch: `if step.step_type == StepType.CALL_SUBAGENT_BRIEF: SalesAgentAdapter.dispatch(...) else: registry.get(channel).send(...)` (existing path).
7. CRM port — extend `crm_repos.py` con `get_lead_telegram_id(db, tenant_id, lead_id)` lazy import. Wire en `TelegramChannelRouter._resolve_telegram_id`.
8. Tenant locale real lookup — `_resolve_tenant_locale` busca en `TenantModel.config_json["tenant_locale"]` o `tenant_profile`. Best-effort fallback.
9. Brand BudgetGuard 7 callsites guarded via `_get_guarded_llm_service(tenant_id)` helper en `shared/billing/application/llm_guards.py` (extend, NO new file).
10. Voice fidelity threshold ENV `SALES_AGENT_VOICE_FIDELITY_THRESHOLD` default `0.7`.
11. Tests + 2 arch tests + IMPL-LOG + current-state.

NO se splittea: cada paso depende del anterior y todos deben merge-juntos para que el outbound funcione end-to-end con voz de marca + cache + budget guard + tenant isolation.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A: `OutboundOrchestrator` paralelo a `ChatOrchestrator` reusando `ConversationPipeline`** | Reusa LangGraph/cache/budget/voz; cero regresión inbound; código orphan-resistant via DI explícito | +1 archivo orchestrator | **ELEGIDA** |
| B: extender `ChatOrchestrator` con flag `outbound: bool` | 0 archivos nuevos | Mezcla inbound (webhook-driven) con outbound (cron-driven); rompe cohesión §3 SACRA Closer Studio webhook path | descartada |
| C: Adapter directo desde `execution_task.py` saltea orchestrator → invoca `agent_app.ainvoke` directo | menos capas | Duplica fetch_tenant_config + build_identity + build_brand_voice + checkpoint logic; viola SSoT | descartada |
| D: Crear nuevo subgraph `outbound_app` separado del `agent_app` | aislamiento extremo | Duplica StateGraph+nodes; supervisor logic divergente; voice fidelity puede driftear | descartada (NO duplicar StateGraph — sales-agent-expert §3 SACRA) |

## Validación técnica preliminar (Technical Sanity Check)

- **Modules afectados**: `sales_agent` (orchestrator + prompts + state + nodes + voice grader fixture), `campaigns` (adapter + worker dispatch + telegram resolve), `crm` (port extension), `brand` (budget guard wiring), `shared/billing` (helper extend), `shared/domain/locale` (real lookup wiring).
- **Blockers conocidos**: ninguno — todos los pre-requisitos S2 (CampaignOrchestrator + 3 ARQ workers + ChannelRouter + BudgetGuard primitivas + IdempotencyService + ComplianceService + OutboundRateLimiter) están live.
- **Tiempo estimado**: 1 sesión Opus 4.7[1M] (12-16h elapsed).
- **Alternativas técnicas**: ver tabla arriba.

## Existing systems audit (architect-mandatory ANTES de proponer nueva capa)

> NO NEW LAYER rule. Cero capas nuevas duplicadas — todas las decisiones EXTEND.

### Audit cross-module ejecutado

```bash
grep -rn "agent_app\|StateGraph\|sales_app" backend/src/modules/sales_agent/
grep -rn "ChatOrchestrator\|ConversationPipeline" backend/src/modules/sales_agent/
grep -rn "build_initial_state\|create_initial_state" backend/src/modules/sales_agent/
grep -rn "BudgetGuardingLLMService\|_get_guarded" backend/src/shared/billing/
grep -rn "telegram_id" backend/src/shared/infrastructure/models/ backend/src/modules/crm/
grep -rn "TenantLocale\|format_message_for_tenant_locale" backend/src/shared/ backend/src/modules/campaigns/
grep -rn "PromptFragment\|compose_system_prompt\|CACHEABLE_FRAGMENTS" backend/src/modules/sales_agent/
```

### Sistemas existentes encontrados — todos EXTEND

| Sistema | Path | Decisión | Justificación |
|---|---|---|---|
| `ConversationPipeline` static class | `sales_agent/application/orchestrator/conversation_pipeline.py` | EXTEND | `build_initial_state` ya acepta `budget_guard` opcional — agregamos `campaign_id/instructions/outbound_mode` opcionales mismo signature pattern. |
| `agent_app` LangGraph subgraph | `sales_agent/application/orchestrator/graph.py` + `agents/sales/graph.py` | REUSE no-op | invocado via `agent_app.ainvoke(state, config=...)` — sin cambio. |
| Slot system `compose.py` v2 | `sales_agent/application/prompts/compose.py` | EXTEND | nuevo enum value `CAMPAIGN_CONTEXT` POST `BRAND_VOICE` (slot 6) → cache prefix per-tenant slots 1-5 invariante. |
| `BudgetGuardingLLMService` + `BudgetGuardingChatModel` | `shared/billing/application/llm_guards.py` | EXTEND | agregar helper `_get_guarded_llm_service(tenant_id, agent_kind)` mismo archivo. NO new file. |
| `crm_repos.py` lazy port | `shared/links/ports/crm_repos.py` | EXTEND | agregar function `get_lead_telegram_id(db, tenant_id, lead_id)` mismo patrón lazy-import. |
| `LeadModel.telegram_id` column | `shared/infrastructure/models/crm.py:160` | REUSE | columna ya existe + index unique. Cero migration. |
| `TenantLocale` VO + `format_message_for_tenant_locale` | `shared/domain/locale.py` + `campaigns/infrastructure/channels/shared.py` | EXTEND `_resolve_tenant_locale` | reemplazar `TenantLocale.default()` placeholder por lookup real `TenantModel.config_json["tenant_locale"]`. |
| `build_sales_agent_callback_handler` | `sales_agent/observability/recording/factory.py` | REUSE no-op | invocado con `role="agent"` en outbound (mismo handler). |
| `node_sales_supervisor` routing | `sales_agent/application/agents/sales/nodes.py:94` | EXTEND | leer `outbound_mode` + `lead_score` antes de LLM call → skip qualifier si umbral. |
| `execution_task.py` ARQ worker | `campaigns/workers/execution_task.py` | EXTEND | branch en `step.step_type == StepType.CALL_SUBAGENT_BRIEF` antes del dispatch a `ChannelRouterRegistry.get(channel)`. |
| `TelegramChannelRouter._resolve_telegram_id` | `campaigns/infrastructure/channels/telegram.py:422` | EXTEND | wirea CRM port — cierra DR-7. |
| `KNOWN_UNGUARDED` ratchet | `tests/architecture/test_budget_guard_pre_llm_call.py:29` | SHRINK | 5 → 2 (3 brand callsites guarded; expected_max bump 5→2). |

### Decisión por sistema

Cero NEW layer. Cero archivo orphan.

## Decisiones diferidas (explícitas)

- **DR-8 quality_eval workers BudgetGuard**: incluido condicionalmente (Sub-H). Si callsites son cron-only sin DI clean → wirealos in-place via helper. Si requieren refactor mayor de cron context → diferir a S4 (campañas Email/Multi-canal). Decision Sub-H se toma en build, NO en architect.
- **Outbound supervisor skip-qualifier umbral fino**: PR-7 setea `lead_score >= 40` literal. Si telemetría post-merge muestra falsos positivos (closer prematuro), ajustar en PR follow-up via ENV `SALES_AGENT_OUTBOUND_CLOSER_MIN_SCORE`. NO per-tenant tunable (1000 clientes invariant).
- **Multi-canal outbound (WhatsApp, IG)**: fuera de S3 MVP Telegram. Sin embargo `OutboundOrchestrator.send_outbound(channel_type=...)` acepta ya el param para extensibilidad zero-cost en S4.

## Out of scope

- WhatsApp/IG outbound (S4)
- Campaign A/B testing (PI-3)
- Voice fidelity per-tenant tunable threshold (1000 tenants invariant — fijo ENV global)
- Brand voice fine-tuning (sales-agent-brand-voice.md SACRA — wont-fix)
- `quality_eval` workers refactor mayor (decisión Sub-H build-time)
- Migration nueva — NINGUNA esperada (audit: AgentState es TypedDict in-memory; CampaignStep ya tiene `step_type=CALL_SUBAGENT_BRIEF`; LeadModel.telegram_id ya existe)

## Copilot-first checklist

- [ ] ¿Operable conversacional desde copilot? → SÍ (default). Copilot tool `start_outbound_campaign(campaign_id)` queda en backlog PR-8 (post outbound funcional).
- [ ] ¿Qué tools nuevos requiere? → ninguno PR-7. `OutboundOrchestrator.send_outbound` es API interna invocada por ARQ worker, no por copilot end-user.
- [ ] ¿Cards/UI nueva? → ninguna FE. Streamlit admin `/copilot-quality` y `/sales-agent-quality` heredan voice fidelity outbound. Dashboard surface campaigns sigue PR-8/PR-9.
- [ ] Si NO copilot → razón documentada: PR-7 es backend-only orchestration. Surface FE va a PR-8 + S4.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` (Opus, este PR) | `prompts/01-architect-start.md` | `CONTRACT.md` (este archivo + PR.md) |
| Implementation | `nicolify-agentic` (Opus 1M, surface sales_agent + campaigns) | `prompts/02-builder-start.md` | code + tests + `IMPL-LOG.md` |
| Audit | `nicolify-agentic-auditor` (Opus) — agentic surface | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/{campaigns,sales-agent,brand}.md` update |

**Surface owner único**: `nicolify-agentic` builder (sales_agent + copilot-touching surfaces) + `nicolify-backend` (campaigns adapter + crm port + brand budget wiring) co-trabajando en mismo branch `development`. Arch test ratchet enforce non-breaking inbound — auditor lo valida.

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Domain TypedDict | `sales_agent/application/orchestrator/state.py::AgentState` | EXTEND additive (`campaign_id`, `campaign_instructions`, `outbound_mode`) |
| Helper | `sales_agent/application/orchestrator/state.py::create_initial_state` | EXTEND signature additive |
| Application | `sales_agent/application/orchestrator/conversation_pipeline.py::build_initial_state` | EXTEND signature additive (campaign fields) |
| Application (NEW) | `sales_agent/application/orchestrator/outbound_orchestrator.py` | NEW file, static class paralelo a `ChatOrchestrator` |
| Application | `sales_agent/application/agents/sales/nodes.py::node_sales_supervisor` | EXTEND routing condition outbound |
| Prompts | `sales_agent/application/prompts/compose.py` | EXTEND enum + slot 6 builder |
| Adapter (NEW) | `campaigns/infrastructure/external/sales_agent_adapter.py` | NEW file, bridge campaign→sales_agent |
| Worker | `campaigns/workers/execution_task.py` | EXTEND step.step_type branch |
| Channel | `campaigns/infrastructure/channels/telegram.py::_resolve_telegram_id` | EXTEND CRM port wire |
| Locale | `campaigns/infrastructure/channels/shared.py::_resolve_tenant_locale` | EXTEND real lookup |
| CRM port | `shared/links/ports/crm_repos.py` | EXTEND `get_lead_telegram_id` |
| Billing helper | `shared/billing/application/llm_guards.py` | EXTEND `_get_guarded_llm_service(tenant_id, agent_kind)` |
| Brand callsites | `brand/application/voice_fidelity/grader.py`, `brand/application/agents/style_analyzer/nodes.py`, `brand/application/services/personality_service.py` | WIRE helper (3 files, 7 callsites) |
| Arch test ratchet | `tests/architecture/test_budget_guard_pre_llm_call.py` | shrink 5 → 2 + brand entries removed |
| Arch test (NEW) | `tests/architecture/test_outbound_orchestrator_non_breaking.py` | NEW |
| Arch test (NEW) | `tests/architecture/test_campaign_state_additive.py` | NEW |
| Voice fidelity ENV | `backend/src/shared/billing/application/...` o `backend/src/modules/sales_agent/...` (test-only consumer) | NEW ENV consumed by golden test |
| current-state | `current-state/{campaigns,sales-agent,brand}.md` | append capability lineage |
| Migration | (none) | confirmed zero-migration PR |

## Tests requeridos (TDD)

### BE unit (con mocks)
- `tests/modules/sales_agent/application/orchestrator/test_outbound_orchestrator.py` — happy path + checkpoint reuse + voice fidelity wiring + budget guard wiring + supervisor skip-qualifier branch.
- `tests/modules/sales_agent/application/prompts/test_compose_slot_campaign_context.py` — `outbound_mode=True` → slot 6 emitted POST slot 5; `outbound_mode=False` → slot 6 ausente.
- `tests/modules/sales_agent/application/orchestrator/test_state_additive.py` — `create_initial_state` con + sin campaign_id, defaults preservados.
- `tests/modules/sales_agent/application/agents/sales/test_supervisor_outbound_skip.py` — `outbound_mode=True` + `lead_score=45` → routing direct closer; `lead_score=30` → routing normal.
- `tests/modules/campaigns/infrastructure/external/test_sales_agent_adapter.py` — adapter happy + adapter rejects non-CALL_SUBAGENT_BRIEF.
- `tests/modules/campaigns/infrastructure/channels/test_telegram_resolve_real.py` — `_resolve_telegram_id` lookup real con LeadModel mock + tenant isolation.
- `tests/modules/campaigns/infrastructure/channels/test_shared_locale_real.py` — `_resolve_tenant_locale` con TenantModel mock devuelve currency+timezone correctos.
- `tests/modules/brand/application/test_brand_budget_guard_wiring.py` — 3 brand callsites consumen helper.

### BE integration F-7 (sin mocks — política PR-4)
- `tests/integration/test_outbound_orchestrator_e2e.py` — fixture tenant + offer + lead → `OutboundOrchestrator.send_outbound` → DB checkpoint persisted + LLM mock returns canned + Telegram channel mock receives formatted text.
- `tests/integration/test_sales_agent_adapter_e2e.py` — fixture campaign DAG `CALL_SUBAGENT_BRIEF` step → ARQ worker → adapter → orchestrator → channel mock.
- `tests/integration/test_brand_budget_guard_e2e.py` — fixture brand voice fidelity grader → guard wrapper invoked → BudgetExceeded raised cuando cap exceeded.

### Arch tests (NEW + ratchet shrink)
- `tests/architecture/test_outbound_orchestrator_non_breaking.py` — chat path inbound (`outbound_mode=False` default) → AgentState shape preservada + slot 6 ausente + supervisor routing actual sin cambio.
- `tests/architecture/test_campaign_state_additive.py` — `AgentState.__annotations__` superset del baseline pre-PR-7 + nuevos campos opcionales (`| None` o default).
- `tests/architecture/test_budget_guard_pre_llm_call.py` shrink: 5 → 2 (brand entries removed; quality_eval workers stay si Sub-H deferred).

### Voice fidelity goldens
- `tests/quality/golden/test_voice_fidelity_outbound.py` — 1 fixture tenant real con `personality_profile.system_instruction` → outbound conversación → grader score ≥0.7. Threshold ENV consumed.

## Aceptación

- [ ] Tests verdes nativos: `cd backend && .venv/bin/pytest tests/modules/{sales_agent,campaigns,brand}/ tests/integration/ tests/architecture/ tests/quality/ -x -q`
- [ ] Lint verde: `cd backend && .venv/bin/ruff check src/ tests/`
- [ ] Type check: `cd backend && .venv/bin/mypy src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py src/modules/campaigns/infrastructure/external/sales_agent_adapter.py`
- [ ] Arch tests +2 nuevos verdes + `test_budget_guard_pre_llm_call.py` shrink 5→2 (o 5→0 si Sub-H incluido)
- [ ] Voice fidelity outbound ≥0.7 en golden con personality_profile real fixture
- [ ] `IMPL-LOG.md` completo con cronograma sub-deliverables A-K
- [ ] `REVIEW.md` sin findings críticos (auditor agentic)
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/{campaigns,sales-agent,brand}.md` actualizado
- [ ] Decisiones 28-36 registradas en `decisions.md` PI
- [ ] Cero `git push --force`, cero migración nueva, cero archivos ajenos commiteados
- [ ] `make ci-parity` PASS antes de `git push origin development`

## Reglas duras (checklist obligatorio)

- [ ] **`response_model=` mandatory**: PR-7 NO introduce endpoints nuevos; OutboundOrchestrator es API interna BE. Endpoint `/api/v1/campaigns/stats/{campaign_id}` queda en PR-8.
- [ ] **Tenant isolation**: `_resolve_telegram_id(lead_id, tenant_id)` filtra ambos. `OutboundOrchestrator.send_outbound(tenant_id=...)` mandatory. Repos receive `tenant_id` required.
- [ ] **Voice SSoT preserved**: NO `brand_voice_summary`, NO fine-tune, NO voice-rewriter LLM pass post-gen, NO hardcode voz, NO `{tenant_name}` mid-block cache prefix. Slot 6 `CAMPAIGN_CONTEXT` va POST slot 5 BRAND_VOICE → cache prefix slots 1-5 inviolate per-tenant.
- [ ] **Idempotency on writes**: `OutboundOrchestrator.send_outbound` reusa `idempotency_key` del CampaignTask (`f"telegram-send:{task_id}"`). NO crear sesión nueva si ya hay checkpoint activo (`load_checkpoint` first).
- [ ] **AsyncSession**: nuevo código `async def`. `OutboundOrchestrator.send_outbound` es async. Worker `_process_task` ya AsyncSession.
- [ ] **structlog**: cero `print`/`logging`. Cada surface logea con `tenant_id`, `lead_id`, `campaign_id`, `agent_kind="sales_agent"`.
- [ ] **Spanish neutro LATAM**: comentarios + docstrings + structlog event_name keys. **Excepción**: output `OutboundOrchestrator` respeta voz tenant (puede tener voseo si tenant es AR — `personality_profile.system_instruction` SSoT).
- [ ] **Native WSL tests/lint**: NUNCA `docker exec ruff/pytest/tsc/vitest`.
- [ ] **NO touch §3 SACRA sales-agent**: `OutputManager.process_response`, `BufferService.smart_debounce`, Closer Studio API/WS, `agent_state_checkpoint` schema, webhook adapters.
- [ ] **SA pool reservation invariant**: outbound consume `agent_kind="sales_agent"` bucket (reserved pool, default 50%). Cero leak hacia Others pool.
- [ ] **Idempotent migrations**: NINGUNA migration esperada — confirmar con review schema.

## Criterio aceptación PR (medible)

| Métrica | Target |
|---|---|
| Tests verdes | 100% nuevos + zero regresión existing |
| Voice fidelity outbound (grader) | ≥0.7 |
| Voice fidelity inbound (regression check) | ≥0.7 baseline preserved |
| Cache hit rate inbound (regression check) | ≥60% (slots 1-5 invariantes) |
| `KNOWN_UNGUARDED` size | ≤2 (5→2 hard) |
| Arch tests delta | +2 (`test_outbound_orchestrator_non_breaking` + `test_campaign_state_additive`) |
| Migrations | 0 |
| Lint errors | 0 |
| `_resolve_telegram_id` returns None for lead without telegram_id | True (graceful skip) |
| `_resolve_tenant_locale` returns real `TenantLocale(currency, timezone)` for tenant with config | True |

## Open questions

ZERO. Todas las decisiones 28-36 resueltas en CONTRACT.md.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Cache prefix break si slot 6 va antes de slot 5 | Test `test_compose_slot_campaign_context.py` verifica orden literal (slot 6 POST slot 5); arch test `test_no_cache_prefix_break` asserta CACHEABLE_FRAGMENTS prefix invariante slots 1-5 |
| Inbound supervisor regresión por outbound branch | Test `test_supervisor_outbound_skip.py` con `outbound_mode=False` → comportamiento idéntico baseline |
| Voice fidelity drift outbound | Golden test `test_voice_fidelity_outbound.py` ≥0.7 mandatory; weekly cron `sales_agent_quality_eval` reporta drift |
| `_resolve_telegram_id` lookup adds DB call hot-path | LeadModel.telegram_id is unique-indexed column; sync `Session` query already in worker context — sub-millisecond |
| Brand BudgetGuard wiring breaks existing brand tests | TDD: ejecutar baseline brand tests RED-GREEN antes/después de wiring; helper retorna inner unchanged si `budget_guard=None` (test path) |
| `quality_eval` workers refactor scope creep | Sub-H decision build-time: si callsites simples (≤2) → incluir + ratchet 5→0; si complejo → defer S4 + ratchet 5→2 |
| `_resolve_tenant_locale` real lookup adds latency hot-path outbound | LRU cache 5min on `(tenant_id) -> TenantLocale`; cross-instance invalidation via existing pattern (PlanService.get_effective Q5) |

