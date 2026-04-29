# Synthesis — Campaigns Foundation Research

> Compresión del research legacy `docs/pm/campaigns/` para consumo ágil. Original sigue como referencia trazable.

## Inputs sintetizados

| Carpeta | Tema | Decisiones clave |
|---|---|---|
| `00-framework/architecture.md` | Patrón Strategy+Command, Campaign domain conceptual | Strategy separa canal de lógica, Command encola tasks con estado |
| `00-framework/campaign-types.md` | Taxonomía 4 tipos × 3 tiers (10 patterns total) | Tier 1: AGENT_CONV + EVENT_TRIGGER + RETARGETING + EMAIL_DRIP + TIKTOK_DM. Tier 2: PUSH + REFERRAL + VOICE. Tier 3 descartado: SMS, Twitter DM, LinkedIn (con caveats), AI video |
| `01-conversacional/research.md` | WABA rules, ManyChat capabilities, Respond.io patterns | ManyChat = bridge transitorio (D8). 24h window + HSM template para WA fuera ventana |
| `02-email-marketing/research.md` | MailerLite deep dive: groups, automations, webhooks | 7 trigger mappings lifecycle → group. Webhook events → JourneyEvent + scoring |
| `03-otros-tipos/research.md` | Webinar templates, retargeting, push, referral, voice | launch-4day = 9 steps multi-canal. Retargeting CRM list = +29%-73% ROI vs cold |
| `04-integracion-nicolify/connections-map.md` | Cómo campaigns conecta con CRM, Sales Agent, Copilot, Landing, Advertising | Campaign Orchestrator = puente. CRM = data layer. Copilot = único punto contacto emprendedor (D7) |
| `05-arquitectura-agente/FOUNDATION.md` | Pre-código architectural foundation (D1-D9 confirmadas) | Sales Agent extension non-breaking, OutboundOrchestrator paralelo, Campaign Orchestrator service ARQ, Commercial Director = Copilot subagent (D4) |

## Mental model resultante (1 párrafo)

Campaign = **plan + audience + agent**. CampaignTask = **una ejecución por contacto × step**. CampaignOrchestrator (servicio, no AI) traduce Campaign + Segment → CampaignTask[] → ARQ worker que rutea por `campaign.type` a Sales Agent (outbound conv) o MailerLite (email) o OneSignal (push) o Meta API (retargeting export). El Sales Agent NUNCA habla con emprendedor (D5); Copilot SÍ (D7) y delega creación de campañas a Marketing Campaign Subagent (D4).

## Modelo de dominio (compactado de FOUNDATION §2)

```
Campaign
├── id, tenant_id, name, type, status
├── segment_id (FK Segment) | segment_snapshot (list[contact_id] al lanzar)
├── channel_priority: list["telegram","whatsapp","email"]
├── agent_instructions (texto libre — Sales Agent personaliza)
├── mailerlite_group_slug | anchor_event_date | scheduled_at
└── created_by ("copilot" | "api" | "manual")

CampaignStep (solo EVENT_TRIGGER)
├── step_index, offset_hours (negativo antes / positivo después)
├── channel, template_slug | agent_instructions
└── condition (opcional: "score_gte:60" filtro)

CampaignTask (ejecución por contacto)
├── campaign_id, contact_id (CustomerProfile.id), step_index
├── status: PENDING → EXECUTING → SENT → RESPONDED → CONVERTED → FAILED → SKIPPED
├── channel_used, compliance_check JSONB
├── enrollment_id (attribution)
└── scheduled_at, executed_at, failed_reason, retries

Segment
├── tenant_id, name, type (DYNAMIC | STATIC)
├── filters: list[SegmentFilter] (AND logic)
└── estimated_size, last_calculated_at

SegmentFilter
├── field ("lifecycle_stage" | "lead_score" | "last_activity_at" | "traits.{key}")
├── operator (eq, gte, lte, in, not_in, is_null, contains)
└── value
```

## Modelo de attribution (compactado de connections-map.md)

- **First-touch** (lead nuevo): `CustomerProfile.source_campaign_id` + `source_ref` + `source_ad_id`. NUNCA sobreescribir.
- **Last-touch** (conversión): `Sale.campaign_id` opcional.
- **Campaign-level**: `JOIN campaign_tasks ct ON enrollments e ON sales s` filtrando por `ct.campaign_id`.

## ChannelRouter logic (compactado de FOUNDATION §3.1)

```
Per (Contact, Campaign):
  for channel in campaign.channel_priority:
    if channel == "whatsapp":
      lead = get_lead_by_channel(contact, "whatsapp")
      if lead and waba_in_window(lead): return ("whatsapp", lead.whatsapp_id)
      elif campaign.has_hsm_template: return ("whatsapp_hsm", lead.whatsapp_id)
    elif channel == "telegram":
      lead = get_lead_by_channel(contact, "telegram")
      if lead.telegram_id: return ("telegram", lead.telegram_id)  # No 24h limit
    elif channel == "email":
      if contact.primary_email: return ("email", contact.primary_email)
    elif channel == "manychat":
      if contact.traits["manychat_subscriber_id"]: return ("manychat", id)
  raise NoChannelAvailable
```

WABA-24h check encapsulado en `ComplianceService` (S0.5).

## Templates globales catalog (Sprint 1)

| Slug | Tipo | Canales | Steps |
|---|---|---|---|
| `welcome-sequence` | EMAIL_DRIP | email | 6 emails / 10d |
| `launch-4day` | EVENT_TRIGGER | email + WA | 9 steps con offsets |
| `webinar-sequence` | EVENT_TRIGGER | email | 6 steps anclados al webinar |
| `cold-lead-reactivation` | AGENT_CONVERSATION | WA / Telegram | 1 step (Sales Agent inicia) |
| `post-purchase-onboarding` | EMAIL_DRIP | email | onboarding + upsell |

## Segmentos predefinidos catálogo

| Slug | Filtros |
|---|---|
| `hot-leads-no-response` | stage=SQL, last_activity < now-3d |
| `warm-leads-inactive` | stage=MQL, last_activity < now-7d |
| `subscribers-no-email` | stage=SUBSCRIBER, primary_email IS NULL |
| `customers-upsell` | stage=CUSTOMER, lifetime_value < 500 |
| `churned-reactivation` | stage=CHURNED, first_conversion_at IS NOT NULL |
| `all-contacts` | sin filtros |

## Invariantes protegidos (FOUNDATION §9)

1. ChatOrchestrator (inbound) NO se modifica. OutboundOrchestrator paralelo.
2. Grafo LangGraph del Sales Agent NO se modifica. Solo campos opcionales en state.
3. DDD de módulos existentes NO se modifica. `campaigns/` nuevo y limpio.
4. Channels adapters NO se modifican.
5. Copilot provider pattern NO se modifica.
6. Tests existentes NO se rompen.

## Referencias originales

| Tema | File legacy |
|---|---|
| Arquitectura general | `docs/pm/campaigns/00-framework/architecture.md` |
| Taxonomía tipos | `docs/pm/campaigns/00-framework/campaign-types.md` |
| Conversacional research | `docs/pm/campaigns/01-conversacional/research.md` |
| Email marketing research | `docs/pm/campaigns/02-email-marketing/research.md` |
| Otros tipos research | `docs/pm/campaigns/03-otros-tipos/research.md` |
| Connections map | `docs/pm/campaigns/04-integracion-nicolify/connections-map.md` |
| Foundation arquitectónica | `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` |
| MASTER_TODO original | `docs/pm/campaigns/MASTER_TODO.md` (input no canónico) |

## Decisión de archivado

`docs/pm/campaigns/` queda como referencia histórica hasta cierre PI-1. Decisión final archivar/borrar al cierre PI-1 retro.
