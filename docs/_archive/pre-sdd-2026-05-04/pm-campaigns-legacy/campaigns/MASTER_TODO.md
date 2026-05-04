# MASTER TODO — Agentic Marketing Agency Platform
**Última actualización:** 2026-04-29
**Sistema:** Nicolify como agencia completa de marketing y publicidad

> **Regla de este documento:** Se actualiza en cada sesión de trabajo. Cuando una tarea se complete, se marca `[x]`. Cuando aparece un aprendizaje o decisión nueva, se agrega aquí antes de continuar. Este es el único lugar de verdad sobre qué hemos decidido y qué falta.

---

## Estado de Decisiones Arquitectónicas

| # | Decisión | Estado | Detalle |
|---|----------|--------|---------|
| D1 | Canales outbound: multi-canal | ✅ Confirmado | Telegram para tests, WhatsApp (ManyChat bridge) para prod, WABA directo cuando tengamos Meta |
| D2 | Mensajes: Sales Agent personaliza siempre | ✅ Confirmado | No templates fijos. Sales Agent es el experto. `campaign_instructions` = directriz, no guión. |
| D3 | Arquitectura: Foundation-first, MVPs sin refactor | ✅ Confirmado | Construir la base correcta antes del primer MVP |
| D4 | Commercial Director = Copilot subagent (#4) | ✅ Confirmado | Industry best practice: planning ≠ execution. Artisan, 11x, Luru todos separan. |
| D5 | Sales Agent = B2C conversations ONLY | ✅ Confirmado | Nunca habla con el emprendedor. Recibe `campaign_instructions` como contexto, no como estrategia. |
| D6 | `campaigns/` = módulo independiente | ✅ Confirmado | Non-breaking. Máxima escalabilidad. |
| D7 | Copilot = único punto de contacto del emprendedor | ✅ Confirmado | Todo lo que el emprendedor quiere hacer, se lo dice al Copilot. |
| D8 | ManyChat = bridge WhatsApp hasta WABA directo | ✅ Confirmado | Para los tenants que ya tienen ManyChat conectado |
| D9 | Telegram = canal de pruebas (sin aprobación Meta) | ✅ Confirmado | — |

---

## La Arquitectura en Una Imagen

```
ENTREPRENEUR (usa la app)
    │
    ↓ habla con
COPILOT (Account Manager) ← único punto de contacto
    │
    ├─ Subagent #1: audit_inspector      (ya existe)
    ├─ Subagent #2: url_analyzer         (ya existe)
    ├─ Subagent #3: data_query           (ya existe)
    └─ Subagent #4: commercial_director  (NUEVO) ← diseña campañas
                           │
                           │ crea Campaign objects en BD
                           ↓
                  CAMPAIGN ORCHESTRATOR  (service, no AI)
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
        SALES AGENT   EMAIL AGENT   [FUTUROS]
        (outbound     (MailerLite   Content Agent
         + inbound)    bridge)      Voice Agent
              │
         LEADS / CUSTOMERS
         (WhatsApp, Telegram, IG DM, TikTok DM)
```

**Invariantes permanentes:**
- Sales Agent NUNCA habla con el emprendedor
- Copilot NUNCA habla con leads
- Campaign Orchestrator no es un agente LLM — es un worker ARQ
- El Commercial Director DISEÑA; el Sales Agent EJECUTA

---

## Leyenda de Status

```
[ ] Pendiente
[~] En progreso (sesión actual)
[x] Completado
[!] Bloqueado — razón anotada
[?] Necesita decisión antes de continuar
[→] Delegado a (tool/agent/sprint)
```

Tamaño: `XS` (<1h) | `S` (2-4h) | `M` (1 día) | `L` (2-3 días) | `XL` (1 semana)

---

## FASE 0 — Arquitectura y Documentación

*Objetivo: Saber exactamente qué vamos a construir antes de escribir código.*

### Docs PM
- [x] `XS` CRM Hub UX proposal (FLOW-SPEC.md + DECISIONS.md) — `docs/ux-sessions/2026-04-29-crm-module-proposal/`
- [x] `M` Campaign knowledge base — `docs/pm/campaigns/00-04`
  - [x] Framework + taxonomía de tipos
  - [x] Investigación conversacional (ManyChat, Respond.io, WABA rules)
  - [x] Investigación email marketing (MailerLite deep dive)
  - [x] Investigación otros tipos (webinars, retargeting, push, referral, voice)
  - [x] Mapa de integración Nicolify
- [x] `M` Agentic architecture foundation — `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md`
- [x] `XS` MASTER_TODO.md (este documento) — `docs/pm/campaigns/MASTER_TODO.md`
- [ ] `S` CONTRACT.md — API contracts + DB schema definitivo para `campaigns/` module

### Decisiones pendientes de respuesta
*(Necesarias antes de escribir CONTRACT.md)*

- [?] **Segment resolver scope MVP 1:** ¿Filtros por `lifecycle_stage` + `lead_score` + `last_activity_at` son suficientes? ¿O también `traits.{key}`?
- [?] **Outbound reply recognition:** Cuando un lead responde a un mensaje de campaña, ¿cómo el ChatOrchestrator (inbound) sabe que viene de una campaña? Propuesta: verificar CampaignTask con status=SENT para ese lead en últimas 24h → poner `campaign_id` en state.
- [?] **`campaign_instructions` — ¿variables o texto libre?** MVP 1: solo texto libre ("hola, pregunta sobre el programa"). Variables `{nombre}`, `{oferta}` desde MVP 2.
- [?] **ManyChat bridge — ¿cuántos tenants actuales tienen ManyChat conectado?** Determina si va en MVP 2 o MVP 3.

---

## FASE 1 — Foundation Code (Pre-MVP)

*Objetivo: Crear las bases que ningún MVP subsecuente tenga que reescribir. Zero funcionalidad de usuario — solo infraestructura.*

*Estimado: 1.5-2 semanas de implementación.*

### 1A. Módulo `campaigns/` — Domain Layer (TDD)

- [ ] `S` TEST: `test_campaign_domain.py` — Campaign lifecycle, CampaignStep, CampaignTask states
- [ ] `S` TEST: `test_segment_resolver.py` — SegmentFilter evaluation, resolve → list[UUID]
- [ ] `S` IMPL: `campaigns/domain/campaign.py` — Campaign, CampaignStep, CampaignTask, enums
- [ ] `S` IMPL: `campaigns/domain/segment.py` — Segment, SegmentFilter, SegmentResolver
- [ ] `S` IMPL: `campaigns/domain/template.py` — CampaignTemplate, 5 global templates iniciales
- [ ] `XS` IMPL: `campaigns/domain/channel_router.py` — ChannelRouter interface (stub, implementation en 1C)
- [ ] `XS` IMPL: `campaigns/domain/events.py` — CampaignLaunched, TaskCompleted, TaskFailed

### 1B. Módulo `campaigns/` — Migrations (idempotentes)

- [ ] `S` MIGRATION: tabla `crm_segments` (segment_id, tenant_id, name, type, filters JSONB, estimated_size, last_calculated_at)
- [ ] `S` MIGRATION: tabla `campaigns` (ver schema en FOUNDATION.md §4)
- [ ] `XS` MIGRATION: tabla `campaign_steps`
- [ ] `S` MIGRATION: tabla `campaign_tasks` + índices (ix_campaign_tasks_status, ix_campaign_tasks_contact)
- [ ] `XS` MIGRATION: `customer_profiles` ADD COLUMN `source_campaign_id`, `source_ref`, `source_ad_id`, `preferred_channel`

### 1C. Módulo `campaigns/` — Infrastructure + Application

- [ ] `S` TEST: `test_campaign_repository.py`
- [ ] `S` TEST: `test_campaign_service.py` (CRUD + lifecycle: draft→scheduled→active→completed→failed)
- [ ] `S` IMPL: `campaigns/infrastructure/models/` — todos los modelos SQLA
- [ ] `S` IMPL: `campaigns/infrastructure/repositories/` — CampaignRepository, CampaignTaskRepository, SegmentRepository
- [ ] `M` IMPL: `campaigns/application/services/campaign_service.py` — CRUD + lifecycle + task creation
- [ ] `S` IMPL: `campaigns/application/services/segment_service.py` — resolve + refresh + estimate_size
- [ ] `S` IMPL: `campaigns/application/services/campaign_orchestrator.py` — launch() → resolve segment → create tasks → enqueue ARQ

### 1D. Módulo `campaigns/` — API

- [ ] `S` IMPL: `campaigns/api/campaigns.py` — GET/POST/PUT/DELETE campaigns
- [ ] `XS` IMPL: `campaigns/api/segments.py` — GET/POST segments
- [ ] `XS` IMPL: `campaigns/api/templates.py` — GET templates catalog
- [ ] `XS` IMPL: `campaigns/api/analytics.py` — GET campaign stats (SENT/RESPONDED/CONVERTED counts)
- [ ] `XS` IMPL: `campaigns/api/dto/` — DTOs con response_model (PII rule)

### 1E. ARQ Workers

- [ ] `S` IMPL: `campaigns/workers/campaign_execution_worker.py` — ARQ task: fetch PENDING tasks → route by campaign.type → execute
- [ ] `S` IMPL: `campaigns/workers/campaign_scheduler_worker.py` — ARQ task: activate campaigns at scheduled_at
- [ ] `XS` IMPL: `campaigns/workers/segment_refresh_worker.py` — ARQ task: recalculate segment sizes (cada 15min)
- [ ] `XS` Register workers en `backend/src/workers/settings.py`

### 1F. Sales Agent — Outbound Entry Point

- [ ] `XS` TEST: `test_agent_state_campaign_fields.py` — nuevos campos opcionales no rompen estado actual
- [ ] `S` TEST: `test_outbound_orchestrator.py` — start_outbound_conversation end-to-end (mock channel)
- [ ] `S` TEST: `test_campaign_context_slot.py` — compose.py genera slot CAMPAIGN_CONTEXT cuando campaign_instructions present
- [ ] `S` TEST: `test_outbound_supervisor_routing.py` — outbound_mode=True → skip qualifier para leads con score≥40
- [ ] `XS` IMPL: `sales_agent/domain/state.py` — agregar `campaign_id`, `campaign_instructions`, `outbound_mode` (opcionales)
- [ ] `S` IMPL: `sales_agent/application/prompts/compose.py` — CAMPAIGN_CONTEXT slot
- [ ] `S` IMPL: `sales_agent/application/agents/sales/nodes.py` — routing adicional para `outbound_mode`
- [ ] `M` IMPL: `sales_agent/application/orchestrator/outbound_orchestrator.py` — clase paralela a ChatOrchestrator
- [ ] `XS` IMPL: `campaigns/infrastructure/external/sales_agent_adapter.py` — bridge entre CampaignTask y OutboundOrchestrator

### 1G. Copilot — Campaign Provider (Foundation)

- [ ] `S` IMPL: `campaigns/copilot_provider/__init__.py` + `provider.py` — CopilotProvider registering module + tools
- [ ] `S` IMPL: `campaigns/copilot_provider/tools.py` — campaign_list, campaign_get_status, campaign_launch, campaign_pause (4 tools básicos)
- [ ] `XS` Register provider en Copilot discovery (el patrón ya existe via F1)

### 1H. ChannelRouter — Foundation (Telegram-only para MVP 1)

- [ ] `S` IMPL: `campaigns/domain/channel_router.py` — ChannelRouter.select_channel() → Telegram si lead tiene telegram_id
- [ ] `XS` TEST: `test_channel_router_telegram.py`

---

## FASE 2 — MVP 1: Primera Campaña Funcional (Telegram)

*Objetivo: Un emprendedor puede crear una campaña, seleccionar un segmento manual, lanzarla, y el Sales Agent envía mensajes personalizados por Telegram a cada contacto. Si el lead responde, la conversación continúa normalmente.*

*Estimado: 1 semana.*

- [ ] `S` E2E TEST: crear campaign → launch → verify Telegram messages sent (Playwright o pytest integration)
- [ ] `M` IMPL: CampaignOrchestrator.launch() completo (resolve segment → tasks → ARQ → OutboundOrchestrator → Telegram)
- [ ] `S` IMPL: CampaignTask lifecycle completo (PENDING → EXECUTING → SENT, con failed_reason en fallo)
- [ ] `S` IMPL: Inbound reply recognition — cuando lead responde a mensaje de campaña, poner `campaign_id` en AgentState via CampaignTask lookup
- [ ] `XS` IMPL: Inbox tag "campaña: {campaign.name}" en conversaciones originadas por campaña
- [ ] `S` TEST MANUAL: enviar campaña real a 2-3 contactos Telegram de prueba, verificar calidad del mensaje personalizado
- [ ] `XS` IMPL: Campaign analytics básico — endpoint GET /campaigns/{id}/stats con SENT/RESPONDED/CONVERTED

---

## FASE 3 — MVP 2: Copilot Integration (Commercial Director)

*Objetivo: El emprendedor le dice al Copilot en lenguaje natural lo que quiere, y el Commercial Director (subagent) crea la campaña correctamente. Scheduling disponible.*

*Estimado: 1.5 semanas.*

- [ ] `M` IMPL: `commercial_director` subagent (4to subagent de Copilot)
  - System prompt: experto en diseño de campañas. Conoce segmentos, tipos, mejores prácticas.
  - Tools: campaign_create, campaign_preview, segment_create, template_list
  - write_todos para flujos multi-paso (análisis del segmento → diseño → confirmación → lanzar)
- [ ] `S` IMPL: `campaign_create` tool completa (con validación y response card para el emprendedor)
- [ ] `S` IMPL: Segment builder via Copilot ("mis leads MQL de los últimos 30 días")
- [ ] `S` IMPL: Scheduling via Copilot ("programa la campaña para el lunes a las 10am")
- [ ] `S` IMPL: `template_list` + uso de templates desde Copilot ("usa el template de reactivación")
- [ ] `S` IMPL: Campaign performance queries ("¿cuántos respondieron la campaña de ayer?")
- [ ] `XS` TEST: `test_commercial_director_subagent.py` — isolation, tools disponibles, sin tools de conversación
- [ ] `S` TEST: `test_copilot_campaign_tools.py` — todos los tools de campañas registrados correctamente

---

## FASE 4 — MVP 3: Multi-canal + ManyChat Bridge

*Objetivo: Los mensajes de campaña pueden llegar por Telegram O por WhatsApp (vía ManyChat). El ChannelRouter elige automáticamente según el contacto. Se captura source_ref desde webhooks ManyChat.*

*Estimado: 1.5 semanas.*

- [ ] `M` IMPL: ChannelRouter completo — Telegram → ManyChat → email (con compliance checks)
- [ ] `S` IMPL: WABA 24h compliance check en ChannelRouter
- [ ] `S` IMPL: ManyChat bridge adapter — `CampaignTask(channel=manychat)` → ManyChat API send message
- [ ] `S` IMPL: ManyChat `subscriber.new` webhook → `CustomerProfile.traits["manychat_subscriber_id"]`
- [ ] `XS` IMPL: ManyChat `flow.triggered` webhook → capturar `ref` → `CustomerProfile.source_ref` (first-touch, no sobreescribir)
- [ ] `S` IMPL: CustomerProfile `preferred_channel` — inferir del Lead más activo por canal
- [ ] `XS` TEST: `test_channel_router_multi.py` — priority, fallback, compliance
- [ ] `XS` TEST MANUAL: campaña enviada a contacto con Telegram + ManyChat → verificar canal elegido

---

## FASE 5 — MVP 4: Email Marketing (MailerLite Bridge)

*Objetivo: El emprendedor puede crear campañas de email drip que se disparan automáticamente desde eventos del CRM (lead llega a MQL → entra a secuencia de nurturing).*

*Estimado: 2 semanas.*

### MailerLite Service (implementar stubs)
- [ ] `M` IMPL: `MailerLiteService.sync_contacts(tenant_id)` — GET /subscribers → upsert en CustomerProfile
- [ ] `S` IMPL: `MailerLiteService.add_to_group(email, group_slug)` — POST /subscribers/{id}/groups
- [ ] `S` IMPL: `MailerLiteService.update_subscriber_field(email, field, value)` — PATCH /subscribers/{id}
- [ ] `S` IMPL: `MailerLiteService.get_automation_status(email, automation_id)`
- [ ] `S` IMPL: EMAIL_DRIP campaign type en Campaign Orchestrator → call `add_to_group`

### 7 Trigger Mappings (lifecycle → MailerLite group)
- [ ] `S` IMPL: Lifecycle event handlers → MailerLite group actions
  - `SUBSCRIBER` → add to group "nuevos-suscriptores" → dispara welcome sequence
  - `MQL reached` (score≥40) → add to group "leads-calificados" → dispara nurture sequence
  - `CUSTOMER conversion` → add to group "clientes" + "compra-{oferta_slug}" → onboarding
  - `INACTIVO > 14 días` → add to group "reenganche-necesario" → re-engagement sequence
  - `webinar_attended` journey event → add to group "asistio-webinar-{slug}"
  - `webinar_registered_no_show` → add to group "no-asistio-webinar-{slug}"
  - `email_clicked` (webhook ML→Nicolify) → JourneyEvent(+3 score) → recalculate_score

### MailerLite Webhooks → JourneyEvents
- [ ] `S` IMPL: MailerLite webhook handler — `email_opened` → JourneyEvent(+2), `email_clicked` → JourneyEvent(+3)
- [ ] `XS` IMPL: `unsubscribed` → `CustomerProfile.traits["mailerlite_subscribed"] = false`
- [ ] `XS` TEST: `test_mailerlite_webhook_journey_events.py`

### Landing Page → MailerLite
- [ ] `S` IMPL: Landing page form submit → crear/actualizar suscriptor en MailerLite + source_ref tracking
- [ ] `XS` TEST: `test_landing_mailerlite_capture.py`

---

## FASE 6 — MVP 5: Event Campaigns (Webinar / Launch)

*Objetivo: El emprendedor puede crear una campaña de lanzamiento anclada a una fecha. Los pasos se envían automáticamente (D-7, D-1, D+0, D+2, etc.) por múltiples canales.*

*Estimado: 2-3 semanas.*

- [ ] `M` IMPL: EVENT_TRIGGER campaign type completo
- [ ] `M` IMPL: CampaignSchedulerWorker — calcular `scheduled_at` de cada step desde `anchor_event_date + offset_hours`
- [ ] `S` IMPL: Multi-canal por step (EMAIL step → MailerLite, WHATSAPP/TELEGRAM step → Sales Agent)
- [ ] `S` IMPL: Template "webinar-sequence" (6 steps, ver FOUNDATION.md §2.3)
- [ ] `S` IMPL: Template "launch-4day" (9 steps, ver docs/pm/campaigns/03-otros-tipos/research.md)
- [ ] `S` IMPL: Template "cold-lead-reactivation" (AGENT_CONVERSATION, 1 step)
- [ ] `S` IMPL: Copilot puede crear desde template: "crea un lanzamiento para el 15 de mayo con el template launch-4day"
- [ ] `XS` TEST: `test_event_campaign_step_scheduling.py` — offset_hours → datetime correcto
- [ ] `S` TEST: `test_event_campaign_e2e.py` — lanzamiento completo, 3 steps en distintos canales

---

## FASE 7 — MVP 6: CRM Hub Frontend

*Objetivo: El emprendedor puede ver todos sus contactos, segmentarlos, lanzar campañas, y ver el performance — todo desde la UI sin hablar con el Copilot.*

*Estimado: 2-3 semanas.*

### Backend (ya debería estar completo de fases anteriores)
- [ ] `XS` Verificar que todos los endpoints necesarios para FE existen y tienen response_model

### Frontend
- [ ] `M` FEAT: `/sales/contactos` → CRM Hub (reemplazar stub actual)
  - Tabla de contactos con columnas: nombre, lifecycle_stage, lead_score, source, último contacto
  - Filtros: lifecycle_stage, lead_score range, fuente, canal, fecha última actividad
  - Paginación
- [ ] `M` FEAT: Contact Detail View (`/sales/contactos/{id}`)
  - Unified profile: identidades, score, lifecycle, traits, source
  - Timeline de journey events
  - Historial de campañas recibidas
  - Link a conversaciones en Inbox
- [ ] `M` FEAT: Segment Builder UI (`/sales/segmentos`)
  - Crear segmentos con filtros visuales (drag-and-drop o dropdowns)
  - Preview del tamaño estimado (llamada a `GET /segments/{id}/preview`)
  - Segmentos predefinidos del catálogo
- [ ] `M` FEAT: Campaign Dashboard (`/sales/campanas`)
  - Lista de campañas con status chips (DRAFT, ACTIVE, COMPLETED)
  - Métricas por campaña: enviados, respondidos, convertidos, conversion rate
  - Action buttons: Launch, Pause, View Tasks
- [ ] `S` FEAT: Campaign Creator UI (simple form, sin builder de steps — para MVP)
  - Nombre, tipo, segmento, canal, agent_instructions textarea
  - Scheduled_at picker
- [ ] `XS` FEAT: Sidebar entry para "CRM Hub" (actualmente no existe — stub en "Contactos")

---

## FASE 8 — Retargeting (Meta Ads)

*Objetivo: El emprendedor puede exportar un segmento CRM a Meta Ads como Custom Audience o Lookalike.*

*Estimado: 1.5-2 semanas. Prerequisito: tenant tiene Meta Business Account conectado.*

- [ ] `?` DECISIÓN: ¿Cuántos tenants tienen `META_ADS_ACCOUNT` en connections? Determina prioridad real.
- [ ] `M` IMPL: `advertising/application/services/meta_ads_service.py` — completo (hoy es placeholder)
  - `create_custom_audience(name, ad_account_id)`
  - `upload_audience_members(audience_id, emails, phones)` — con SHA-256 hashing
  - `create_lookalike(origin_audience_id, countries, ratio)`
- [ ] `S` IMPL: `campaigns/` RETARGETING_EXPORT campaign type — resolve segment → hash → Meta API
- [ ] `S` IMPL: `advertising/api/audience_exports.py` — POST + GET status endpoints
- [ ] `S` IMPL: Copilot tool `export_segment_to_meta(segment_id)` + `create_lookalike(audience_id)`
- [ ] `S` FEAT FE: CRM Hub → button "Exportar a Meta Ads" en vista de segmento
- [ ] `XS` TEST: hashing correcto (SHA-256, lowercase, trimmed antes de hash)
- [ ] `XS` TEST: Meta API mock — flujo completo sin llamada real

---

## FASE 9 — Web Push (OneSignal)

*Objetivo: Las landing pages de Nicolify pueden capturar opt-in de notificaciones push. Las campañas pueden incluir pasos de push notification.*

*Estimado: 1 semana. Prerequisito: landing pages en HTTPS con dominio del tenant.*

- [ ] `?` DECISIÓN: ¿Las landing pages están en dominio propio del tenant? Push requiere HTTPS.
- [ ] `S` IMPL: `campaigns/infrastructure/external/onesignal_service.py` — send notification, get device info
- [ ] `S` IMPL: PUSH_NOTIFICATION campaign type en Campaign Orchestrator
- [ ] `S` IMPL: Landing page → OneSignal JS snippet + opt-in → `player_id` en CustomerProfile.traits
- [ ] `XS` FEAT FE: Landing page settings → "Activar notificaciones push" toggle

---

## FASE 10 — Referral / Afiliados

*Objetivo: Cada cliente puede tener un código de referido. Las conversiones referidas se trackean y el emprendedor puede ver sus afiliados activos.*

*Estimado: 1 semana.*

- [ ] `S` IMPL: `CustomerProfile.referral_code` + `CustomerProfile.referred_by_code` (migration)
- [ ] `S` IMPL: Commission record model + repository (referrer_id, referred_id, sale_id, amount, status)
- [ ] `S` IMPL: Sale event → check `referred_by_code` → create Commission record (PENDING)
- [ ] `S` IMPL: Referral dashboard endpoints (GET /crm/referrals/stats)
- [ ] `XS` FEAT FE: Dashboard de afiliados en CRM Hub

---

## FASE 11 — AI Voice Follow-up (Vapi + ElevenLabs)

*Objetivo: El Sales Agent puede iniciar llamadas telefónicas a leads warm (HOT, score>70) que no respondieron en 48-72h. Opt-in requerido.*

*Estimado: 2-3 semanas. Prerequisito: tenant opt-in activado.*

- [ ] `?` DECISIÓN: ¿Hay un tenant que quiera ser beta tester? Define prioridad real.
- [ ] `S` IMPL: `CustomerProfile.traits["voice_optout"]` — respeto del opt-in
- [ ] `M` IMPL: `connections/infrastructure/channels/vapi.py` — VoiceAdapter (Vapi API)
- [ ] `S` IMPL: Voice campaign type en Campaign Orchestrator
- [ ] `XS` IMPL: ChannelRouter — voice como último fallback (después de Telegram/WhatsApp/email)

---

## FASE 12 — Quality & Attribution

*Objetivo: Poder responder con certeza "¿cuánto revenue generó la campaña X?"*

*Estimado: 1 semana.*

- [ ] `S` IMPL: Attribution worker — cuando Enrollment.status cambia a PAID, buscar CampaignTask activo para ese contact → setear CampaignTask.enrollment_id
- [ ] `S` IMPL: `Sale.campaign_id` — last-touch attribution
- [ ] `S` IMPL: Campaign analytics endpoints completos (revenue_attributed, roi, conversion_rate)
- [ ] `S` IMPL: RFM segmentation algorithm (el campo ya existe en CustomerProfile — falta el cálculo)
- [ ] `S` IMPL: Copilot tool `campaign_roi(campaign_id)` — responde preguntas de performance

---

## FASE 13 — Futuro (No en 12 meses)

- [ ] AI Personalized Video (Tavus/HeyGen) — solo para high-ticket >$1K USD
- [ ] Google Customer Match — complemento de Meta retargeting
- [ ] LinkedIn DMs — nicho B2B coaching únicamente
- [ ] TikTok DM — cuando ManyChat TikTok Business connection esté en connections/
- [ ] Content Agent — auto-publicación en redes (cuando 3+ tenants lo pidan)
- [ ] Analytics Agent — insights proactivos y recomendaciones de campañas

---

## Dependencias entre Fases

```
FASE 0 (Docs + Decisiones)
    ↓
FASE 1 (Foundation Code) ← TODO comienza aquí
    ↓
FASE 2 (MVP 1: Telegram)
    ↓
FASE 3 (MVP 2: Copilot + Commercial Director)
    ↓
FASE 4 (MVP 3: Multi-canal)    FASE 5 (MVP 4: Email)
    ↓                               ↓
    └─────────── FASE 6 (MVP 5: Event Campaigns) ──────────┘
                                ↓
                    FASE 7 (CRM Hub Frontend)
                                ↓
         FASE 8 (Retargeting)  FASE 9 (Push)  FASE 10 (Referral)
                                ↓
                    FASE 11 (Voice — opcional)
                                ↓
                    FASE 12 (Attribution Quality)
```

---

## Estimados de Tiempo (rough order of magnitude)

| Fase | Estimado | Quién |
|------|----------|-------|
| 0 — Arquitectura | 3-4 días | PM + Claude |
| 1 — Foundation Code | 10-14 días | BE |
| 2 — MVP 1 Telegram | 5-7 días | BE |
| 3 — MVP 2 Copilot | 7-10 días | BE |
| 4 — MVP 3 Multi-canal | 7-10 días | BE |
| 5 — MVP 4 Email | 10-14 días | BE |
| 6 — MVP 5 Event | 14-21 días | BE |
| 7 — CRM Hub FE | 14-21 días | FE |
| 8 — Retargeting | 7-10 días | BE |
| 9-11 — Tier 2 | Variable | — |
| **Total Tier 1** | **~4.5 meses** | BE + FE |

---

## Decisiones Pendientes (necesitan respuesta de Chris)

Copiadas aquí para visibilidad rápida:

1. **Segment MVP 1:** ¿Solo `lifecycle_stage` + `lead_score` + `last_activity_at`? ¿O también traits?
2. **ManyChat bridge:** ¿Cuántos tenants actuales tienen ManyChat conectado en `connections/`?
3. **campaign_instructions:** ¿Texto libre en MVP 1? ¿Variables {nombre}/{oferta} desde MVP 2?
4. **Inbound reply recognition:** ¿Buscar CampaignTask activo en últimas 24h para ese contact → inyectar campaign_id en AgentState?
5. **Meta retargeting:** ¿Cuántos tenants tienen Meta Ads Account conectado?
6. **Push notifications:** ¿Las landing pages están en dominio HTTPS propio del tenant?
7. **Voice MVP:** ¿Hay tenant que quiera ser beta tester para AI Voice follow-up?

---

## Changelog

| Fecha | Cambio | Decisión |
|-------|--------|----------|
| 2026-04-29 | Creación del documento | — |
| 2026-04-29 | D1-D9 confirmadas (Chris) | Ver tabla de decisiones |
| 2026-04-29 | D4 confirmada: Commercial Director = Copilot subagent | Basado en research best practices (Artisan, 11x, Luru, Microsoft Copilot Studio guidance) |
