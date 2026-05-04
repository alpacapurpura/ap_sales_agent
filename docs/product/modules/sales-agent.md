---
module: sales-agent
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/sales-agent/"
  stories_dir: "../stories/sales-agent/"
  domain_doc: "../../domains/module_sales-agent.md"
  legacy_pm_nico: "../../pm-nico/current-state/sales-agent.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
capability_registry_status: bootstrapped-2026-05-04
capabilities_count: 5
stories_count: 10
agentic_eval_suite_path: null                   # GAP: no agentic_evals/sales_agent/ — flagged CRÍTICO en gap-report-2026-05-04-group-c
---

# sales_agent — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo (en mejora — PI-3) |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_sales_agent.md` |

## Qué hace por el user
AI SDR autónomo. Conversa con leads en canales conectados, pre-califica, maneja objeciones, agenda citas, envía links de pago, da seguimiento. Reemplaza función de un setter humano.

## Capacidades actuales
- Multi-canal (IG/FB DM vía Manychat, WhatsApp via TODO)
- Conversación con tone propio del tenant (vía PersonalityProfile compilado)
- Pre-calificación de leads (extrae fit con buyer persona)
- Manejo objeciones (RAG + brand authority)
- Agendamiento (integra scheduling module)
- Envío link pago (Mercado Pago / Stripe / etc)
- Follow-up engine
- Specialist agents (closer, follow-up, eval-loop)
- Semantic router → tier pricing (Kimi K2.5 / DeepSeek V3 / GPT-4o por complejidad)
- Trazabilidad turn-a-turn
- Eval loop con goldens
- Per-tenant prompt caching (cache hit rate optimizado)
- Outbox migration ready behind `USE_OUTBOX_PATTERN_SALES_AGENT` flag (OFF default; PI-1 S0 PR-1) — emisores (`event_bus`, `scheduling/payment_event_handlers`, tools, orchestrator, workers, webhooks) routean vía `EventBusAdapter` que detecta flag y enquea a `domain_event_outbox` cuando ON

### Cap: BudgetGuard SA pool reservado + OutboundRateLimiter + ComplianceService — gating primitivas
- Introducida: PR-2 (PI-1, S0, commits `dbc367f2` + `e21dc2a0`, 2026-04-29) — **primitivas expuestas; wiring a specialists diferido S2**
- Estado: primitivas disponibles en `shared/billing/` + `shared/compliance/`
- Operable copilot: no directamente (infra pre-LLM-call + pre-send)
- **BudgetGuard** (SA bucket): `agent_kind="sales_agent"` consume del pool reservado (`plan_config.llm_budget_total_usd * sales_agent_reserved_pct`, default 50%). SA exhausto NO bloquea copilot (pools independientes). Firma: `await budget_guard.check(tenant_id, agent_kind="sales_agent", estimated_cost_usd=Decimal("..."))`
- **OutboundRateLimiter**: Redis sliding window 24h, cap `plan_config.max_outbound_msg_per_day`. `None` cap = unlimited. Fail-open si Redis unavailable. Firma: `allowed = await outbound_rate_limiter.check(tenant_id)`
- **ComplianceService**: policy chain (WABA24h → OptIn DB-backed → Blacklist → CountryBlock). Fast-fail primer bloqueo. Firma: `result = await compliance_service.check(tenant_id, recipient_phone, channel_type)`
- Wiring S2: BudgetGuard → cada specialist node LLM; OutboundRateLimiter + ComplianceService → `output_manager.py` pre-`process_response()`. No modifica §3-protected surfaces (Closer Studio, BufferService, OutputManager.process_response chunking intocados).

### Cap: Outbox cutover ON + BudgetGuard wiring single point ConversationPipeline (PR-6 PI-1 S2)
- Introducida: PR-6 Sub-B (PI-1, S2, commit `7b2de359`, 2026-04-30)
- Estado: live
- `USE_OUTBOX_PATTERN_SALES_AGENT=True` default — emisores routean a `domain_event_outbox` table via `EventBusAdapter`
- `BudgetGuardingChatModel` wired single point en `ConversationPipeline.__init__(budget_guard, tenant_id)` DI optional. Cuando provided wraps LLM service, gating todos LLM callsites en sales nodes transparentemente (1000 clientes — single enforcement point, callsite nuevo gates auto)
- Tests F-7 sin mocks: 13 verde (outbox cutover + budget_guard_wiring + SA pool isolation + soft-warn + proxy attrs)
- Operable copilot: no PR-6 (infra cutover)

### Cap: OutboundOrchestrator (PR-7 PI-1 S3)
- Introducida: PR-7 Sub-B (PI-1, S3, commit `db9fa4b8`, 2026-04-30)
- Estado: live
- Static class paralelo a `ChatOrchestrator`. Reusa `ConversationPipeline` helpers (fetch_tenant_config / load_checkpoint / build_agent_identity / build_brand_voice / build_initial_state / save_checkpoint / sanitize_text) + `agent_app` LangGraph + slot system v2 + voice SSoT.
- Single async entrypoint `OutboundOrchestrator.send_outbound(*, db, tenant_id, lead_id, campaign_id, campaign_instructions, channel_type, channel_adapter, budget_guard)`.
- Slot 7 `CAMPAIGN_CONTEXT` en `compose.py` (Sub-A.5 commit `90ad4d64`) — emitted ONLY cuando `outbound_mode=True`. Cache prefix slots 1-6 byte-equal across inbound/outbound preservando hit rate ≥60% per-tenant.
- Supervisor outbound skip-qualifier (Sub-C commit `32461f9c`): `outbound_mode=True` + `lead_score >= 40` → directo a closer (1000-clientes invariant, NO per-tenant tunable; ENV `SALES_AGENT_OUTBOUND_CLOSER_MIN_SCORE` follow-up adjustment si telemetry muestra falsos positivos).
- Voice fidelity grader threshold prod ENV `SALES_AGENT_VOICE_FIDELITY_THRESHOLD` default `0.7` (Decision 30 — global invariant, NOT per-tenant).
- AgentState additive (Sub-A commit `9200b6cc`): `campaign_id` / `campaign_instructions` / `outbound_mode` con defaults `None / None / False`. Inbound chat path NO se rompe. Arch tests `test_outbound_orchestrator_non_breaking.py` + `test_campaign_state_additive.py` (Sub-J commit `f58016d7`) enforzan invariantes 11/11 verde.
- Operable copilot: no PR-7 (campaign launch tools queda PR-8 PI-1 S3 wiring).

## Capacidades operables desde copilot
- Activar / pausar agente (sólido)
- Ver últimas conversaciones (parcial)
- Ajustar voz vía Brand Studio communication-style (sólido)
- **Gap:** conversación natural con copilot sobre cómo ajustar comportamiento agente

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Conversación core | sólido | Redesign 2026-04 finalizado |
| Voz marca | sólido | SSoT en `personality_profiles.system_instruction` |
| Tools (scheduler, payment) | sólido | |
| **Observabilidad traces persistence** | **live** | PR-2 (PI-1.1, S2, commit `d80d15f5`, 2026-05-01) — wire `observe_turn` lifecycle around `agent_app.ainvoke`. Pre-PR: 0 rows globalmente. Post-PR: traces reales persistidos (smoke verified +4 trace_event +2 llm_call) |
| Cost tracking sales_agent | live | PR-2 — captura cost_usd + fx_rate también en errors (best-effort) |
| Routing decisions auditables | live | PR-1 PI-7 (commit `d8226cf9`, 2026-05-01) — LLM functional, schema populated |
| Multi-canal | parcial | IG/FB OK, WhatsApp pendiente |
| Prompt cache | sólido | Per-tenant key |
| LLM call functional | **live** | PR-1 PI-7 (commits `1bdcfdc9`+`d8226cf9`, 2026-05-01) — Bug #9 LiteLLM restored (LITELLM_ENVIRONMENT propagation + memory 1536M) + Bug #7 brand_data_adapter ORM→DTO. Smoke real Chris-mediated 16:09 UTC: turn_end status='ok', 4 LLM calls (gpt-4o-mini + deepseek-reasoner) |
| Cost tracking accuracy | **degraded** | `cost_usd=0` post-fix por pricing resolution provider mapping (deepseek tagged como openai). Backlog PR follow-up |

## Conexiones cross-módulo
- **Lee de:** crm, brand, offer, connections, scheduling
- **Lo lee:** copilot, connections

## Dolor user / oportunidades detectadas
_Pendiente captura._

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| sales-agent-redesign-s12 | Redesign completo, 12 sprints | 2026-04 |
| PI-1.1-pi1-post-mortem S2 PR-2 | Lift `BaseObservabilityContext` + Bug #2 traces persistence + Bug #8 FXResolver.default | 2026-05-01 |
| PI-7-app-stability-restore S1 PR-1 | Bug #7 brand_data_adapter ORM→DTO + Bug #9 LiteLLM env propagation + memory OOM fix → sales_agent restored functional end-to-end | 2026-05-01 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04-28 | Voz vive en personality_profile compilado, slot 5 BRAND_VOICE | SSoT + cache per-tenant + sin fine-tune |
| 2026-04 | Tier pricing semantic routing | Optimizar costo (Kimi 200k context tier) |
