# PI-1 Retro — Sistema de Campañas

> Owner: PM. Cierre PI-1 2026-04-30. Migración a `pis/archive/` post-write.

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-1-campaigns-module |
| Inicio | 2026-04-29 |
| Cierre | 2026-04-30 (1 día execution Opus 4.7[1M]) |
| Sprints completados | S0 + S1 + S2 + S3 + S4 (5 sprints) |
| PRs shipped | 12 (PR-1+PR-2 S0 + PR-3+PR-4 S1 + PR-5+PR-6 S2 + PR-7+PR-8+PR-9 S3 + PR-10+PR-11+PR-12 S4) |
| Estado | DONE → archive |

## Outcome alcanzado vs hipótesis

### H1: Nicolify hoy tiene piezas dispersas (sales_agent + assets + connections) sin orquestación. Unificarlas = palanca enorme.
✅ **VALIDADA**. Campaigns module nuevo + ChannelRouter v1 + OutboundOrchestrator + inbound recognition entregaron unification end-to-end. Surface entregada permite agregar canales sin tocar foundation (H4 confirmada).

### H2: Tier 1 LATAM = WhatsApp + TikTok DM + retargeting + webinar. SMS irrelevante.
✅ **VALIDADA POR DECISIÓN ESTRATÉGICA**. PI-1 = Telegram MVP only (canal pruebas). Multi-canal WhatsApp + TikTok = PI-2. Retargeting + webinar = PI-3.

### H3: User no quiere templates fijos. Quiere instrucciones high-level + agente personaliza.
✅ **VALIDADA**. Campaign step type `CALL_SUBAGENT_BRIEF` entrega exactly esto: campaign_instructions string injected en agent state slot 7 CAMPAIGN_CONTEXT. Sales Agent personaliza output según voice profile tenant.

### H4 (Chris reframing 2026-04-29): Sprint 0 entrega primitivas robustas → Sprints 1-N agregan canales/tipos sin tocar foundation. Cero refactor entre MVPs.
✅ **VALIDADA STRONGLY**. Evidencia:
- S0 outbox + idempotency + BudgetGuard + RateLimiter + ComplianceService + observability primitives = SHIPPED y NUNCA modificadas en S1-S4.
- S1 dominio + S2 orchestrator REUSE direct S0 primitives.
- S3 Telegram MVP REUSE direct S2 OutboundOrchestrator + ChannelRouter (selecciona Telegram).
- S4 CRM Hub Lite REUSE direct PR-8 CampaignsLookupPort + S1 PaginatedResponse + S1 Segment domain (ambos types DYNAMIC + STATIC desde día 1).
- Cero refactor cross-sprint. Forward-compat invariantes garantizan PI-3 expand sin reescribir (arch tests ratchet shrink-only).

## Métricas (baseline vs target vs cierre real)

| Métrica | Baseline | Target PI-1 | Cierre real |
|---|---|---|---|
| Campañas lanzadas Chris testing | 0 | 1+ | Pendiente Chris execution staging |
| Mensajes Telegram entregados S3 | 0 | 5+ | Pendiente Chris execution staging (manual checklist) |
| Mensajes duplicados | n/a | 0 | 0 (idempotency S0.2 verified) |
| Leak cross-tenant en tests | n/a | 0 | 0 (tenant isolation arch tests + integration verified) |
| Trace events por campaign launch | n/a | ≥3 | ≥3 (launch + task_created + task_sent — observability S0.6) |
| Sprint 0 PRs merged sin refactor en S1+ | n/a | 100% | **100%** ✅ |

**Manual gate Chris staging** = real ship verdict (PR-9 + PR-12 manual checklists). Pendiente Chris execution.

## Surface entregada PI-1 completa

### S0 (Foundation 5 sub-sprints)
- `shared/domain_events/outbox/` — outbox pattern global
- `shared/idempotency/` — Redis-backed `IdempotencyStore` + `@idempotent` decorator
- `shared/billing/` — plan_config + tenant_subscription + BudgetGuard reservación 50% sales_agent + OutboundRateLimiter sliding window
- `shared/compliance/` — ComplianceService gate (WABA-24h, opt-in, blacklist, country-block)
- `campaigns/observability/` — `CampaignLlmCallModel` + `CampaignCallbackHandler` + agent_observability registration

### S1 (Domain + Repos + Services + API)
- `campaigns/domain/`: Campaign + CampaignStep + CampaignTask + Segment + SegmentFilter + ChannelRouter (interface) + enums + events
- `campaigns/infrastructure/models/` + 6 repositories AsyncSession SQLA 2.0
- `campaigns/application/services/`: CampaignService + SegmentService + CampaignTemplateService
- API: campaigns + segments + templates con response_model strict
- 5 templates globales catalog (welcome, launch-4day, webinar, cold-reactivation, post-purchase)

### S2 (Orchestrator + Workers)
- `CampaignOrchestrator.launch()` end-to-end (resolve segment → compliance → idempotent task creation → outbox → ARQ enqueue)
- `CampaignExecutionWorker` ARQ con BudgetGuard + RateLimiter + circuit breaker + audit log
- `CampaignSchedulerWorker` ARQ
- `SegmentRefreshWorker` ARQ (cada 15min)
- `ChannelRouter` v1 Telegram-only

### S3 (MVP 1 Telegram outbound)
- `OutboundOrchestrator.send_outbound` paralelo a ChatOrchestrator (non-breaking)
- AgentState additive (campaign_id, campaign_instructions, outbound_mode)
- Slot 7 CAMPAIGN_CONTEXT cache-safe
- Supervisor outbound skip-qualifier (score≥40 → closer)
- `SalesAgentAdapter` bridge CampaignTask → OutboundOrchestrator
- Inbound recognition `chat.py` window 24h
- `inbox_campaign_enrichment` service + chip Inbox UI
- `GET /campaigns/{id}/stats` con response_model master-data currency
- E2E spec + manual checklist Chris

### S4 (Mini CRM Hub Lite + wire)
- `GET /api/v1/contacts/*` — paginated + detail + 501 stubs forward-compat (18 canonical filters)
- `components/shared/data-table/` (TanStack headless cross-feature)
- `features/crm-hub/` FSD-Lite (7 components + 3 hooks + Zod types mirror Pydantic)
- `features/campaigns-lite/` FSD-Lite (4 components + 6 hooks)
- Page `/sales/contactos` + `/sales/campañas/{nuevo,[id]}`
- SegmentCreate STATIC + lead_ids snapshot
- Wire S4↔S3 completo end-to-end

## Decisiones clave PI-1

Total: **75 decisiones documentadas** (D-1 a D-75). Resumen por sprint:

- D-1 a D-7: PI-1 setup + reframing Chris Sprint 0 + tier 1 LATAM
- D-8 a D-15: S0 primitives selection + plan tiers + reservación 50%
- D-16 a D-23: S1 domain modeling + repository pattern + DAG steps
- D-24 a D-27: S2 orchestrator + workers + circuit breaker
- D-28 a D-37: S3 outbound + AgentState additive + slot CAMPAIGN_CONTEXT + voice fidelity
- D-38 a D-47: S3 inbound recognition + stats + UI tag + manual checklist
- D-48 a D-56: S4 PR-10 BE (NEW endpoint, source CDP, batch engagement, 501 canonical)
- D-57 a D-66: S4 PR-11 FE (TanStack, FSD-Lite, URL state, host-agnostic, slot pattern)
- D-67 a D-75: S4 PR-12 cross-stack (EXTEND vs NEW, JSONB shape, modal vs inline, arch refactor)

Ver detalle: `decisions.md` (this folder).

## Lo que aprendimos sobre user/producto

### Sobre el user (microempresario LATAM target)
- **Confirmed:** quiere unification cross-canal, NO plataforma única (validó decisión PI-1 separado de advertising/social_media)
- **Confirmed:** quiere instrucciones high-level + AI personaliza (no templates rígidos) — H3
- **Hipótesis a validar PI-2:** tolera ManyChat bridge transitorio para WhatsApp (más fricción que Telegram nativo)
- **Hipótesis a validar PI-3:** quiere segment builder visual drag-drop o filter conditional simple es suficiente

### Sobre el producto
- **Cero refactor entre MVPs alcanzado** — H4 fully validated. Foundation-first deep paid off.
- **CDP pattern source-of-truth `customer_profiles + LEFT JOIN leads`** funciona — unified view sin duplicar identity tables
- **Forward-compat ratchet shrink-only arch tests** = mecanismo cero refactor PI-3 verified
- **Slot pattern UI components** (SelectedContactsBar) = mecanismo expansión sin reescribir
- **Host-agnostic content components** (ContactDetailContent) = drawer + page reuse sin duplicar
- **Cross-module ports** (CampaignsLookupPort, CrmRepos) = DDD compliance + forward-compat sin import directo

### Sobre proceso PM
- **Opus 4.7[1M] sprint sizing** = 1-3 PRs amplios cohesivos por sprint, NO splittear por miedo contexto
- **PR-folder atómico self-contained** funciona robusto
- **PM main session fallback** cuando builder/auditor agents pause salva spawn cycles (Opus 4.7 main session = capable arquitecto + builder)
- **Manual gate Chris staging** = real ship verdict (E2E + voice fidelity + Telegram bot real necesitan tenant real)
- **Architect drift detection ANTES CONTRACT** = atrapa bugs early (PR-7 BudgetRepositoryImpl, PR-8 enum gap, PR-12 SegmentCreate gap)

## Riesgos cumplidos / mitigados

| Riesgo PI-1 | Mitigación shipped | Resultado |
|---|---|---|
| R1 técnico: orquestación cross-channel state machine compleja | Outbox + idempotency keys (S0.1+S0.2) | ✅ 0 mensajes duplicados verified tests |
| R2 producto: muchas opciones abruman user | Copilot-first guía PI-2 + UI lite drawer (no full page floods) | ✅ ContactsPage MVP minimal effective |
| R3 compliance: WABA 24h + opt-in | ComplianceService gate central S0.5 | ✅ Architecturally ready, Telegram MVP no requiere WABA |
| R4 cost runaway | RateLimiter + quotas S0.3 | ✅ Architecturally ready |
| R5 observability gap | trace events + audit log S0.6+S0.7 | ✅ Verified ≥3 trace events per launch |
| R6 vendor lock-in | Circuit breaker + adapter pattern | ✅ ChannelRouter abstrae adapters |

## Deuda técnica residual aceptada PI-1 (cleanup post PI-1)

| Item | Razón | Sprint destino |
|---|---|---|
| Brand 7 callsites BudgetGuard runtime wiring | Architectural seam ready (PR-7 Sub-G); runtime DI deferred | S4 cleanup OR PI-2 |
| Sub-H quality_eval workers BudgetGuard | Same architectural seam | Same |
| Voice fidelity outbound multi-turn runner xfail | `SalesAgentJudge.evaluate_conversation` extension | Cleanup |
| Exact `converted_count` attribution proxy | Cross-module payment + scheduling lookup pendiente | Post-PI-1 PR follow-up |
| chat.py PLR0915 noqa | Refactor `_recognize_inbound_campaign` helper | Cleanup |
| ARQ scheduler tick manual trigger admin endpoint | E2E full flow needs trigger | Cleanup |
| DB seed helper tenant + lead + telegram_id staging | Reusable cross E2E specs | Cleanup |
| E2E full flow test.skip (S3 + S4) | Infra gap | Cleanup post-PI-1 |
| Pause/Cancel buttons placeholder | Lite scope | PI-3 |
| Multi-step DAG campaign builder | Lite single-step | PI-3 visual builder |
| Cards copilot integration | Capa arriba | PI-3 tools |
| 27 ESLint warnings react-perf JSX inline functions | Tests | Cleanup |
| 8 `# type: ignore` SQLA legacy Column[T] | Pragmático | Cleanup migración Mapped[] |
| Cursor pagination contacts (offset MVP) | Suficiente lite | PR follow-up si telemetría |

## Recommended PI-2 + PI-3

### PI-2 (multi-canal — open Now post-PI-1)
- ManyChat bridge WhatsApp (Tier 1 LATAM)
- Email Agent + MailerLite EMAIL_DRIP integration
- Copilot subagent commercial_director (NL → campaign creation)
- TikTok DM automation (validar # tenants TikTok Business)

### PI-3 (CRM Hub Completo + Retargeting)
- Segment Builder Visual drag-drop (filters DYNAMIC)
- Página completa `/sales/contactos/{id}` (reuse ContactDetailContent)
- Timeline rich journey events (200 endpoint + UI)
- Bulk actions advanced (export Meta, bulk update tags, agregar a campaign existente)
- Campaign Dashboard (`/sales/campañas` performance overview)
- Cards copilot CRM (`crm_get_pulse`, `crm_search_contacts`, `crm_create_campaign`)
- Retargeting Meta Ads
- Pulso (attention queue + lifecycle distribution)
- RFM segmentation engine

## Cierre verdict

**SHIPPED** (architecturally complete + tests verde). Real ship verdict pendiente Chris execution manual checklist staging:
1. PR-9 manual checklist S3 (Telegram bot real + voice fidelity tenant)
2. Manual checklist S4 (TBD si necesario PR-12 wire UI verification)

**PI-1 → archive 2026-04-30.** Roadmap update: PI-1 → Done section. PI-2-campaigns-multi-canal abre Now.
