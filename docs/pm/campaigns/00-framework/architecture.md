# Arquitectura General del Sistema de Campañas

**Estado:** Decidido (2026-04-29)

---

## El problema que resuelve

Queremos que el emprendedor pueda actuar sobre un grupo de contactos (segmento del CRM) a través de diferentes canales y con diferentes tipos de ejecución (outbound blast, secuencia drip, instrucciones al agente), sin tener que aprender un sistema diferente por canal.

El sistema debe poder crecer (añadir Email Agent, Content Agent, voz AI) sin reescribir la lógica central.

---

## Patrón: Strategy + Command

### ¿Por qué Strategy?

Una campaña tiene:
1. **Qué hacer** → contenido, plantilla, mensaje
2. **A quién hacérselo** → segmento del CRM
3. **Cómo hacerlo** → el canal + el tipo de agente que ejecuta

El "cómo" varía. El "qué" y el "a quién" no. El patrón Strategy separa el canal de la lógica de campaña.

```
Campaign (invariante)
    ↓ defines: audience, content, schedule, goal
    
ChannelRouter (decides qué canal usar por contacto)
    ↓
ChannelAdapter (ejecuta en el canal específico)
    ├── WhatsAppAdapter    → vía Cloud API / Evolution
    ├── TelegramAdapter    → vía Bot API
    ├── InstagramDMAdapter → vía ManyChat webhook
    ├── EmailAdapter       → vía MailerLite API
    ├── TikTokDMAdapter    → vía ManyChat TikTok
    ├── PushAdapter        → vía OneSignal (futuro)
    └── VoiceAdapter       → vía Vapi (futuro)
```

### ¿Por qué Command para el agente?

Cuando el ejecutor es un agente AI (Sales Agent, Email Agent), la "ejecución" no es un envío directo — es un **task** que el agente procesa con contexto CRM. El patrón Command permite encolar tareas con estado.

```
Campaign.launch() 
  → for each contact in segment:
      CampaignTask(campaign_id, contact_id, channel, context)
  → enqueued to ARQ worker
  → AgentExecutor.process(task)
      → load CRM context (profile + history + objections + score)
      → generate personalized message
      → dispatch via ChannelAdapter
      → record result
      → write back to CRM
```

---

## Modelo de datos: Campaign Domain (conceptual)

```
Campaign
  id, tenant_id
  name, description
  type: BROADCAST | DRIP_SEQUENCE | AGENT_CONVERSATION | EVENT_TRIGGER
  agent_type: SALES_AGENT | EMAIL_AGENT | CONTENT_AGENT | NONE (direct send)
  status: DRAFT → SCHEDULED → RUNNING → PAUSED → COMPLETED
  
  # Audiencia
  segment_id → Segment (dinámico o estático)
  
  # Ejecución
  channel_priority: ChannelType[]   # orden de preferencia por contacto
  template_message: str | None      # plantilla fija. Si null → agente personaliza
  schedule_at: datetime | None      # null = inmediata
  
  # Configuración de agente (solo si agent_type != NONE)
  agent_instructions: str | None    # "trata a estos leads como si vinieron del webinar X"
  offer_context_id: UUID | None     # qué oferta presentar
  
  # Para campañas de evento (webinar, launch)
  anchor_event_date: datetime | None   # fecha del evento
  steps: CampaignStep[]                # pasos relativos al anchor

CampaignStep (para DRIP_SEQUENCE y EVENT_TRIGGER)
  id, campaign_id
  step_index: int
  offset_hours: int    # ej: -72 = 72h antes del evento, +24 = 24h después
  channel: ChannelType
  template: str
  condition: str | None   # solo ejecutar si [condición CRM se cumple]

CampaignTask (ejecución unitaria por contacto)
  id, campaign_id, contact_id, tenant_id
  step_index: int | None
  status: PENDING → EXECUTING → SENT → FAILED → SKIPPED
  sent_at: datetime | None
  response_received: bool
  enrollment_id: UUID | None    # si generó una inscripción
  channel_used: ChannelType
  error_message: str | None

# Attribution (en CustomerProfile)
source_campaign_id: UUID | None   # campaña que originó este contacto
source_ref: str | None            # ref param del landing/ad (ManyChat ref o UTM)
source_ad_id: str | None          # Meta ad_id si vino de CTWA/CTDM
```

---

## Los 4 tipos de campaña

### 1. BROADCAST (Outbound blast)
- Un mensaje a un segmento en un momento dado
- Puede ser directo (template fijo) o personalizado (agente redacta)
- Canal: cualquiera del channel_priority del contacto
- Ejemplos: "oferta del Black Friday", "recordatorio de webinar", "seguimiento a leads calientes"

### 2. DRIP_SEQUENCE (Secuencia)
- Serie de mensajes a intervalos definidos
- Un contacto entra al drip → recibe mensajes day 1, day 3, day 7, etc.
- Un contacto sale si cumple exit condition (compró, respondió, se dio de baja)
- Equivalente a MailerLite Automation o Kit Sequence
- Ejemplos: "5 emails de bienvenida post-suscripción", "3 mensajes de seguimiento post-webinar"

### 3. AGENT_CONVERSATION (Outbound conversacional)
- El Sales Agent inicia una conversación outbound
- Lee perfil CRM completo del contacto
- Genera mensaje inicial personalizado
- Si el contacto responde → flujo normal en Studio > Inbox
- Attribution: todos los enrollments de esa conversación → atribuidos a la campaña
- Ejemplos: "contactar a todos los MQL sin respuesta en 15 días", "ofrecer upsell a clientes evangelist"

### 4. EVENT_TRIGGER (Orquestación de evento)
- Anclada a una fecha (webinar, launch, expiración de oferta)
- CampaignSteps con offsets relativos: -72h (reminder), -1h (urgency), +2h (replay), +48h (close)
- Multi-canal: email + WhatsApp + push coordenados
- El tipo más complejo pero también el de mayor ROI para infoproductores
- Ejemplos: "lanzamiento del programa X", "webinar en vivo", "oferta 48h"

---

## Source-Aware Treatment (tratamiento diferenciado por origen)

**El concepto más importante del sistema.**

Cuando un contacto llega desde una campaña específica (un anuncio de Meta, una landing page, un video de TikTok), el sistema sabe de dónde vino y puede tratar a ese contacto diferente.

```
Lead llega por WhatsApp
  ↓
Sistema revisa: ¿tiene source_campaign_id?
  ├── SÍ → carga las agent_instructions de esa campaña
  │         "Esta persona vino de la campaña del webinar de enero.
  │          Ofrécele primero el curso X. Menciona que vio el masterclass."
  │         → Sales Agent usa estas instrucciones como override del flow normal
  │
  └── NO → flow normal de calificación genérico
```

**Cómo se captura el origen:**
- ManyChat: `ref` parameter (landing page → ManyChat via ref slug) o `entry_point` (ad_id en CTWA)
- UTM parameters: de landing pages → journey_events
- API: cuando Nicolify mismo crea el contacto (import CSV, form fill)

**Actualmente falta en el CRM:** `source_campaign_id`, `source_ref`, `source_ad_id` en `CustomerProfile`. Los campos `lead_source` y `source_channel` son demasiado genéricos.

---

## Channel Routing Logic

Por cada contacto + campaña, el router decide el canal:

```
1. ¿Tiene canal preferido en su CustomerIdentity? → usarlo
2. ¿Cumple las compliance rules del canal?
   - WhatsApp: ¿conversación activa < 24h? SI no → necesita HSM template
   - Email: ¿está suscrito y activo? SI no → skip
3. ¿Ha interactuado en ese canal en los últimos 30 días? → preferirlo
4. Fallback: siguiente canal en la lista
5. Si ningún canal viable → log SKIPPED, no enviar
```

---

## Qué ya existe en el código

| Componente | Estado |
|---|---|
| `BaseChannel` + adapters (WhatsApp, Telegram, IG, Email) | ✅ Existe en `connections/` |
| `CustomerProfile` con lifecycle + scoring | ✅ Existe en `crm/` |
| `Enrollment` + `Sale` (para attribution) | ✅ Existe en `sales_agent/` |
| `JourneyEvent` (para triggers) | ✅ Existe en `crm/` |
| `ARQ workers` (para background execution) | ✅ Existe en `workers/` |
| MailerLite API integration | ✅ Existe en `connections/` + `analytics/` |
| `Campaign` domain model | ❌ No existe |
| `CampaignTask` + execution engine | ❌ No existe |
| `Segment` builder | ❌ No existe |
| Source-aware fields en `CustomerProfile` | ❌ Faltan `source_campaign_id`, `source_ref`, `source_ad_id` |
| Sales Agent outbound entry point | ❌ No existe |
