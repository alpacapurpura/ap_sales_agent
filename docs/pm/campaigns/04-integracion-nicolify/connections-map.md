# Mapa de Conexiones: Campaign System ↔ Nicolify
**Fecha:** 2026-04-29
**Status:** Borrador — para iterar juntos

---

## El sistema de campañas como columna vertebral

```
                    EMPRENDEDOR
                        │
              ┌─────────┴─────────┐
         CRM Hub              COPILOT
    (decisiones visuales)  (conversacional)
              │                   │
              └─────────┬─────────┘
                        │
               CAMPAIGN ORCHESTRATOR
               (qué, a quién, cuándo)
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    SALES AGENT    EMAIL AGENT    [FUTUROS]
   (outbound conv) (email flows)  Content Agent
         │              │              │
    ┌────┴────┐    ┌────┴────┐
    WhatsApp  │    MailerLite│
    Telegram  │              │
    TikTok DM │              │
    IG DM     │              │
              │
        CRM DATA LAYER
    (CustomerProfile + Segments
     + JourneyEvents + Attribution)
```

---

## Módulos afectados por el sistema de campañas

### 1. CRM Hub (nuevo módulo frontend + ampliación backend)

**Lectura:** El Campaign Orchestrator consulta el CRM para:
- Resolver members de un segmento
- Obtener preferred_channel por contacto
- Leer historial de conversaciones/objeciones (para personalización del Sales Agent)
- Verificar compliance (¿está en ventana de 24h WABA?)

**Escritura:** El Campaign Orchestrator escribe al CRM:
- `CampaignTask.status` (SENT, FAILED, SKIPPED)
- `CampaignTask.enrollment_id` (si generó una inscripción)
- `CustomerProfile.source_campaign_id` (en primer contacto)
- `CustomerProfile.source_ref` (ref de ManyChat/landing)
- `JourneyEvent("campaign_message_sent", campaign_id)` (para scoring)

### 2. Sales Agent (extensión de outbound)

**Nuevo entry point:** `start_outbound_conversation(tenant_id, contact_id, campaign_id, context)`
- Carga perfil CRM del contacto
- Lee `campaign.agent_instructions` (override del flow normal)
- Genera mensaje inicial personalizado
- Envía por `ChannelAdapter` elegido por el router
- Si el contacto responde → el hilo vive en Studio > Inbox con `campaign_id` tag

**Source-aware treatment:**
- Cuando llega un inbound y el contacto tiene `source_campaign_id` → el agente carga las `agent_instructions` de esa campaña
- Esto permite "tratar diferente" a los leads de una campaña específica sin configuración per-lead

### 3. MailerLite Integration (ampliación de connections/)

**Acciones que Nicolify debe poder ejecutar:**
```python
# Agregar suscriptor a grupos (dispara automations de MailerLite)
mailerlite.add_to_groups(email, groups=["MQL-calificados", "landing-webinar-enero"])

# Actualizar campo del suscriptor
mailerlite.update_field(email, field="lifecycle_stage", value="CUSTOMER")

# Verificar si el suscriptor tiene automation activa
mailerlite.get_automation_status(email, automation_id)

# Crear campaña one-shot (para broadcasts)
mailerlite.create_campaign(name, subject, groups, content_html)
```

**Webhook de MailerLite → Nicolify (bidireccional):**
```
email_opened → JourneyEvent("email_opened", +2 score)
email_clicked → JourneyEvent("email_clicked", +3 score)
unsubscribed → CustomerProfile.traits["mailerlite_subscribed"] = false
automation_step_sent → (log para analytics)
```

### 4. Copilot (ampliación de copilot_provider)

El Copilot debe poder:

**Queries:**
- "¿Cuántos leads están recibiendo la secuencia de bienvenida?" → query a MailerLite via CRM provider
- "¿Cuántas personas entraron a la campaña de lanzamiento?" → query CampaignTask table
- "¿Cuál es la tasa de apertura del email de hoy?" → query MailerLite analytics

**Acciones:**
- "Lanza la campaña de lanzamiento ahora" → `CampaignService.launch(campaign_id)`
- "Pausa la campaña de retargeting" → `CampaignService.pause(campaign_id)`
- "¿A quiénes les enviamos el broadcast de ayer?" → `CampaignService.get_tasks(campaign_id)`
- "Exporta mis mejores clientes a Meta Ads" → `MetaAdsService.export_segment(segment_id)`

**Nuevas tools del Copilot para campañas:**
- `campaign_get_status(campaign_id)` — estado, enviados, respondidos
- `campaign_launch(campaign_id)` — ejecutar
- `campaign_pause(campaign_id)` — pausar
- `campaign_create_from_template(type, segment_id, anchor_date)` — crear desde plantilla
- `mailerlite_get_automation_stats(automation_id)` — stats de una secuencia

### 5. Landing Page Module (landing/)

La landing page es el punto de captura más importante para campañas de email y push.

**Ampliaciones necesarias:**

```
Landing page settings:
  ├── Email capture → MailerLite group assignment
  │   └── "Nuevos suscriptores" + "landing-[page_slug]"
  ├── Push opt-in → OneSignal integration
  │   └── Prompt de permiso push + player_id capture
  ├── Source tracking → UTM param capture
  │   └── utm_source, utm_campaign → CustomerProfile.source_ref
  └── ManyChat WhatsApp link → con ref parameter
      └── "Habla conmigo" → wa.me/XXXXX?ref=landing_[page_slug]
```

**El flujo ideal (landing page → automation):**

```
1. Visitante llega a landing page
   (desde Meta Ad → utm_campaign=webinar_enero_meta)

2. Llena formulario: nombre + email

3. Nicolify:
   a. Crea CustomerProfile (si no existe)
   b. Guarda: source_ref="webinar_enero_meta", source_channel="landing_page"
   c. Llama MailerLite: crear suscriptor + agregar a grupo "landing-webinar-enero"
   d. MailerLite automation "Joins group: landing-webinar-enero" dispara
   → Email 1: "Aquí está tu lugar confirmado" (inmediato)
   → Email 2: "Prepárate para el webinar" (D-1)

4. Si optó en push:
   a. OneSignal player_id guardado en CustomerProfile.traits
   b. D-1: push notification "El webinar es mañana"
```

### 6. Advertising Module (advertising/)

El módulo `advertising/` es el candidato para alojar:

```
advertising/
  domain/
    audience_export.py    # AudienceExport + ExportTask domain models
    ad_campaign.py        # (ya existe: ad_offer_associations)
  application/services/
    audience_export_service.py   # Lógica de hashing + exportación
    meta_ads_service.py          # Meta Marketing API client
    google_ads_service.py        # Google Customer Match (futuro)
  api/
    audience_exports.py   # POST /advertising/audiences/export
                          # GET  /advertising/audiences/{id}/status
```

**El tenant ya tiene Meta Business conectado** via `connections/` (verificar). Si sí → la exportación es un API call + tracking.

---

## Attribution Model (el que debemos construir)

Para que las campañas tengan sentido, necesitamos poder responder:

1. "¿Cuántas ventas generó la campaña X?" → CampaignTask.enrollment_id + Sale.created_at
2. "¿Qué campaña trajo más leads?" → CustomerProfile.source_campaign_id
3. "¿Cuántos de mis clientes vienen de Meta Ads?" → CustomerProfile.source_ref contains "utm_source=meta"
4. "¿Cuál es el ROI de mi retargeting?" → Sale.amount WHERE source_campaign_id = retargeting_campaign_id

**El modelo de attribution:**

```
First-touch attribution (para leads nuevos):
  CustomerProfile.source_campaign_id = primera campaña que los captó
  CustomerProfile.source_ref = primer ref/UTM

Last-touch attribution (para conversiones):
  Sale.campaign_id = última campaña antes de la conversión
  (opcional: multi-touch)

Campaign-level metrics:
  SELECT COUNT(*), SUM(sales.amount)
  FROM campaign_tasks ct
  JOIN enrollments e ON e.id = ct.enrollment_id
  JOIN sales s ON s.id related to enrollment
  WHERE ct.campaign_id = :campaign_id
```

---

## Preguntas de integración clave

1. **MailerLite webhooks activos:** ¿El endpoint `/connections/mailerlite/webhooks` ya está procesando clicks/opens? Si no, activar esto antes que todo lo demás.

2. **Meta Business Account:** ¿El módulo `connections/` tiene soporte para Meta Business (Ads) además de Instagram/Facebook para mensajería? El retargeting necesita el Ads scope del Meta token.

3. **OneSignal y las landing pages:** ¿Las landing pages de Nicolify están en un dominio HTTPS controlado? El push necesita service workers en el dominio.

4. **MailerLite group naming convention:** ¿Hay una convención ya establecida para los group names del tenant? Propongo: `nicolify:{tipo}:{slug}` para separar los grupos que Nicolify crea de los que el tenant crea manualmente.

5. **Campaign attribution en AgentState:** ¿Hay un campo `campaign_id` en `AgentState`? Si el Sales Agent inicia una conversación por una campaña, ese `campaign_id` debe persistir en el estado para attribution correcta.
