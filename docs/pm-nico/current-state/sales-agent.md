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
| Observabilidad | sólido | trazas + cost tracking + cycle billing 25-25 |
| Multi-canal | parcial | IG/FB OK, WhatsApp pendiente |
| Prompt cache | sólido | Per-tenant key |

## Conexiones cross-módulo
- **Lee de:** crm, brand, offer, connections, scheduling
- **Lo lee:** copilot, connections

## Dolor user / oportunidades detectadas
_Pendiente captura._

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| sales-agent-redesign-s12 | Redesign completo, 12 sprints | 2026-04 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04-28 | Voz vive en personality_profile compilado, slot 5 BRAND_VOICE | SSoT + cache per-tenant + sin fine-tune |
| 2026-04 | Tier pricing semantic routing | Optimizar costo (Kimi 200k context tier) |
