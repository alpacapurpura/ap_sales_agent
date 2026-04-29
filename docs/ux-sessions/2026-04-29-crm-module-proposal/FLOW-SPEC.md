# CRM Hub Module — Flow Spec
**Session:** 2026-04-29-crm-module-proposal
**Mode:** New Module Proposal (functional scope)
**Scope:** CRM Hub como submódulo estratégico dentro de Sales (Closer Studio)

---

## 1. Audit Summary

### Estado actual del stack de contactos/leads

| Capa | Qué existe | Estado |
|---|---|---|
| BE Domain | `CustomerProfile` + `CustomerIdentity` + `Lead` + lifecycle scoring | Sólido ✅ |
| BE Services | `LifecycleService`, `IdentityService`, `LeadService`, `SaleService` | Sólido ✅ |
| BE API | `/crm/leads`, `/crm/pipeline`, `/crm/sales`, `/crm/cdp` | Parcial ⚠️ |
| FE Sales Studio | Inbox, Pipeline (Kanban), Frozen, Enrollments | Operativo ✅ |
| FE Contactos | Stub "Próximamente" en `/sales/contactos` | Vacío ❌ |
| Copilot | `crm/copilot_provider/` existe, `sales_agent/copilot_provider/` existe | Conectado parcial ⚠️ |
| Segmentos | No existe UI ni API de segment builder | Ausente ❌ |
| Campañas outbound | No existe API de campaign enrollment | Ausente ❌ |
| Contact health | `rfm_segment` field en DB, sin lógica ni UI | Ausente ❌ |

### Lo que Sales Studio YA hace (no duplicar)
- Inbox: gestión de conversaciones activas en tiempo real
- Pipeline (Kanban): leads por etapa de embudo (rapport → closing)
- Frozen: conversaciones auto-pausadas
- Enrollments: ciclo inscription → payment → attended
- WebSocket KPIs en tiempo real (activas, AI/manual, hot/warm/cold)

---

## 2. Posicionamiento del CRM Hub

```
SALES STUDIO HOY
└── Closer Studio
    ├── Studio → Operativo (conversaciones en curso, pipeline caliente)
    ├── Contactos → [STUB] → Propuesta: CRM Hub estratégico
    └── Inscripciones → Enrollment lifecycle

PROPUESTA
└── Closer Studio
    ├── Studio → Operativo (sin cambios)
    ├── CRM Hub → Estratégico (nuevo)
    │   ├── Personas (base de contactos)
    │   ├── Segmentos (listas dinámicas)
    │   ├── Campañas (outbound)
    │   ├── Pulso (contact health)
    │   └── [Contacto individual → timeline unificado]
    └── Inscripciones → Enrollment lifecycle (sin cambios)
```

**Principio rector:**
- Studio = "¿Qué está pasando ahora?" (caliente, en curso)
- CRM Hub = "¿Quiénes son mis contactos y qué hago con ellos?" (estratégico, datos)

---

## 3. Journey Maps

### Journey A: Microempresario revisando su base de contactos
```
Entra al app / Copilot le dice: "Tienes 12 leads calientes sin contactar en 5 días"
    ↓
CRM Hub > Pulso — ve el dashboard de salud: distribución lifecycle, queue "Necesitan atención"
    ↓
Filtra "hot + sin actividad > 3 días" → ve 8 contactos
    ↓
Selecciona 8 → crea campaña outbound "Seguimiento precio"
    ↓
Sales Agent recibe la campaña → ejecuta mensajes personalizados por canal
    ↓
Microempresario recibe notificación: "3 de 8 respondieron"
    ↓
Entra al Studio > Inbox para ver las conversaciones activas que generó la campaña
```

### Journey B: Acción desde Copilot (no está en la compu)
```
Copilot (desde móvil o WhatsApp): "¿Quiénes son mis mejores clientes?"
    ↓
Copilot lee CRM via copilot_provider: "Tienes 4 clientes EVANGELIST: María, Juan, Ana, Carlos"
    ↓
Usuario: "Manda un descuento especial a mis clientes evangelist"
    ↓
Copilot crea campaña en CRM Hub → Sales Agent / Email Agent la ejecuta
    ↓
Copilot: "Listo, mensaje enviado a 4 contactos por WhatsApp"
```

### Journey C: Preparar campaña outbound para nuevo lanzamiento
```
Emprendedor va a lanzar nuevo programa
    ↓
CRM Hub > Segmentos → crea segmento "Leads calificados sin convertir"
    (lifecycle=MQL OR SQL, sin sale en últimos 90 días)
    ↓
CRM Hub > Campañas → nueva campaña "Lanzamiento Programa X"
    → tipo: outbound, canal: WhatsApp
    → elige segmento: "Leads calificados sin convertir" (34 personas)
    → redactar mensaje o dejar que el Sales Agent lo personalice
    ↓
Sales Agent recibe cola de 34 contactos con contexto de cada uno
    → envía mensajes personalizados por canal preferido
    → gestiona respuestas en Studio > Inbox normalmente
    ↓
CRM Hub > Campañas → métricas de campaña: enviados, respondidos, conversiones
```

---

## 4. Gap Analysis

### 4.1 Funcionalidades ausentes (críticas)

| Gap | Impacto | Esfuerzo | Prioridad |
|---|---|---|---|
| Contact database UI con búsqueda y filtros | Alto — es la base de todo | Medio | P1 |
| Segment builder (filtros dinámicos guardados) | Alto — habilita campañas | Medio | P1 |
| Campaign enrollment API (CRM → Sales Agent) | Alto — conecta todo | Alto | P1 |
| "Attention queue" / Pulso diario | Alto — retención microempresario | Medio | P1 |
| Contact timeline (historial unificado) | Alto — contexto completo | Medio | P1 |
| RFM segmentation engine | Medio — campo existe, falta lógica | Bajo | P2 |
| Enrichment waterfall (IG → email → web) | Medio — mejora calidad datos | Alto | P2 |
| Notes y recordatorios por contacto | Medio — VA replacement | Bajo | P2 |
| Campaign performance metrics | Medio — ROI visible | Medio | P2 |
| Copilot: queries CRM en lenguaje natural | Alto — multicanal | Medio | P1 |
| Copilot: trigger campañas desde conversación | Alto — diferenciador | Alto | P2 |
| Export lista (CSV) | Bajo — workaround siempre | Bajo | P3 |
| Lookalike finder ("contactos como X") | Bajo — nice to have | Alto | P3 |

### 4.2 Lo que ya existe y NO hay que construir
- Modelo de datos `CustomerProfile` + scoring — ✅ sólido
- Lifecycle stages con transiciones automáticas — ✅ funciona
- `LifecycleService` con umbrales y decay — ✅ bien diseñado
- Sales Agent como ejecutor de conversaciones — ✅ es el "outreach engine"
- `crm/copilot_provider/` — ✅ existe, ampliar

---

## 5. Capacidades Funcionales Propuestas (CRM Hub)

### MÓDULO 1: Personas (Contact Database)

**Propósito:** Ver y buscar todos los contactos del sistema en un solo lugar.

**Capacidades:**
- Lista paginada de `CustomerProfile` con búsqueda full-text (nombre, email, teléfono, handle)
- Filtros rápidos: lifecycle stage, temperatura, canal de origen, lead_source, is_inactive, rfm_segment
- Vista columnas configurables: mostrar/ocultar campos
- Perfil de contacto (detalle):
  - Identidades multi-canal (email, WhatsApp, IG, Telegram)
  - Scoring actual (lead_score, fit_score, intent_score) con tendencia
  - Lifecycle stage con fecha de última transición
  - Historial de mensajes/conversaciones (desde `messages` + `leads`)
  - Enrollments/compras (desde `sale` + `enrollment`)
  - Agenda/citas (desde `appointments`)
  - Journey events (timeline de acciones del contacto)
  - Notas manuales del emprendedor
  - Tags personalizados
- Acciones desde el perfil:
  - Iniciar conversación (envía a Sales Agent)
  - Agregar a segmento
  - Agregar a campaña
  - Agregar nota
  - Cambiar lifecycle stage (manual override)
  - Ver conversación activa en Studio

**Datos disponibles en backend (ya existen):**
- `CustomerProfile` + `CustomerIdentity` + `JourneyEvent` + `Lead` + `Sale` + `Enrollment` + `Appointment`

**Lo que hay que construir:**
- API: `GET /api/v1/crm/contacts` con filtros completos + paginación
- API: `GET /api/v1/crm/contacts/{id}/timeline` (eventos unificados ordenados por fecha)
- API: `POST /api/v1/crm/contacts/{id}/notes`
- API: `POST /api/v1/crm/contacts/{id}/tags`
- FE: feature `crm-hub/`, vista Personas

---

### MÓDULO 2: Segmentos (Dynamic Lists)

**Propósito:** Definir audiencias (grupos de contactos que comparten características) para usarlas en campañas y análisis.

**Capacidades:**
- **Segmentos dinámicos:** filtros guardados que se actualizan automáticamente
  - Condiciones: lifecycle stage, temperatura, lead_score (rango), rfm_segment, tags, canal origen, has_sale, last_activity_at, offer comprado, custom traits
  - Operadores: AND / OR / NOT
  - Preview en tiempo real (count de contactos que aplican)
  - Nombre + descripción + ícono de color
- **Segmentos estáticos:** listas manuales (add/remove específicos)
  - Útil para: "Clientes VIP de este lanzamiento", "Lista de espera manual"
- **Segmentos preconstruidos (sistema):**
  - Hot leads sin contactar > 3 días
  - Leads calificados sin convertir (MQL+SQL sin sale)
  - Clientes que pueden hacer upsell (CUSTOMER + RFM alto)
  - En riesgo de churn (is_inactive=true + CUSTOMER)
  - Evangelistas (EVANGELIST)
  - Base completa de suscriptores

**Datos disponibles:** todos los campos de `CustomerProfile` + joins a `Sale`, `Enrollment`, `Journey Events`

**Lo que hay que construir:**
- BE Domain: `Segment` (name, description, type=DYNAMIC|STATIC, filter_config JSONB, contact_ids[] para estáticos)
- BE Service: `SegmentService.resolve_members(segment_id)` → lista de contact IDs
- BE API: CRUD de segmentos + `GET /api/v1/crm/segments/{id}/members`
- FE: filter builder UI (similar a Attio/HubSpot listas), preview count

---

### MÓDULO 3: Campañas (Outbound Actions)

**Propósito:** Ejecutar acciones masivas/segmentadas sobre un grupo de contactos. El Sales Agent (o futuros agentes) son los ejecutores.

**Capacidades:**
- Crear campaña:
  - Nombre + objetivo (description)
  - Audiencia: elige segmento (dinámico o estático) o selección manual
  - Canal: WhatsApp | Telegram | IG DM | Email (cuando haya Email Agent)
  - Tipo: outbound_sales (Sales Agent), outbound_email (Email Agent), manual (exportar lista)
  - Mensaje plantilla (o dejar al agente personalizar con contexto del CRM)
  - Programación: inmediata / fecha+hora
  - Límites: máx N por día, horario permitido
- Estado de campaña: DRAFT → SCHEDULED → RUNNING → PAUSED → COMPLETED
- Vista de progreso:
  - Enviados / Pendientes / Fallidos
  - Respondidos (vinculados a conversaciones en Studio > Inbox)
  - Conversiones atribuidas (enrollments generados desde conversación de campaña)
- Acciones de campaña en curso: pausar, reanudar, cancelar

**Integración Sales Agent:**
- Campaña crea "outbound_task" queue: cada contacto del segmento → un task
- Sales Agent lee queue: para cada contacto, busca su contexto CRM (profile + historial) y redacta mensaje personalizado
- Sales Agent envía por canal preferido del contacto
- Si el contacto responde → flujo normal de conversación en Studio > Inbox (con tag de "campaña origen")
- Attribution: si la conversación genera un Enrollment → la campaña recibe el crédito

**Integración futuros agentes:**
- Email Agent: misma API de campaña, diferente `agent_type`
- Content Agent: puede generar el copy de la campaña en base al brief del emprendedor
- La campaña es el "brief" que el emprendedor da y el agente ejecuta

**Lo que hay que construir:**
- BE Domain: `Campaign` (name, segment_id, channel, agent_type, template_message, status, schedule_at)
- BE Domain: `CampaignTask` (campaign_id, contact_id, status, sent_at, response_received, enrollment_id)
- BE Service: `CampaignService.launch(campaign_id)` → genera CampaignTask queue
- BE: worker/integration que conecta CampaignTask → Sales Agent (outbound initiation)
- BE API: CRUD campañas + metrics
- FE: campaign builder, progress view, metrics

**Punto de integración Sales Agent (crítico):**
El Sales Agent necesita un nuevo entry point para conversaciones iniciadas outbound:
- Input: `(tenant_id, contact_id, campaign_id, template_context)`
- Sales Agent usa perfil CRM del contacto como contexto
- Diferencia vs. inbound: el agente inicia, no espera

---

### MÓDULO 4: Pulso (Contact Health & Attention Queue)

**Propósito:** El dashboard que responde "¿Qué hago hoy?" — priorización automática para el microempresario.

**Capacidades:**
- **Attention Queue** (lo más importante):
  - Lista priorizada de contactos que necesitan acción HOY
  - Algoritmo: ponderación de días sin actividad + temperatura + lifecycle stage + score trend
  - Cada ítem muestra: nombre, última interacción, qué pasó ("preguntó precio hace 3 días"), acción sugerida
  - Acciones rápidas: "Iniciar campaña a este grupo", "Marcar para seguimiento", "Ver perfil"
- **Lifecycle Distribution:**
  - Chart: cuántos contactos en cada stage
  - Click en stage → filtra Personas por ese stage
- **Actividad reciente** (feed):
  - Nuevos leads captados hoy/semana
  - Conversiones recientes
  - Contactos que escalaron de stage
  - Alertas: leads en riesgo de churn
- **Score Trend:**
  - Contactos cuyo score bajó >20% en 7 días (en riesgo)
  - Contactos cuyo score subió (oportunidad)
- **Source Attribution:**
  - De dónde vienen los contactos (IG DM vs landing vs manual vs referral)
  - Conversión por canal de origen

**Lo que hay que construir:**
- BE Service: `PulseService.get_attention_queue(tenant_id)` — scoring de prioridad
- BE API: `GET /api/v1/crm/pulse` → {attention_items[], lifecycle_distribution, activity_feed, trend_alerts}
- FE: dashboard de Pulso con los widgets

---

### MÓDULO 5: Contacto Individual (Timeline Unificado)

**Propósito:** Ver la historia completa de un contacto — el "perfil 360".

**Capacidades:**
- Header: nombre, avatar (generado), identidades multi-canal, lifecycle stage badge, temperatura
- Scoring panel: lead_score (trend), fit_score, intent_score, rfm_segment
- Timeline cronológico (todos los eventos del contacto):
  - Mensajes intercambiados (preview + link a conversación en Studio)
  - Journey events (email abierto, página vista, formulario enviado)
  - Stage transitions (con fecha y motivo)
  - Enrollments/compras (monto, producto, fecha)
  - Citas agendadas (status: completada/no show)
  - Campañas en las que participó
  - Notas manuales del emprendedor
- Panel de datos:
  - Profile data extraído por el agente (ocupación, pain point, goal, persona asignada)
  - Traits (de ManyChat, MailerLite, etc.)
  - Historial de objeciones (`key_objections_history`)
- Acciones:
  - "Iniciar/Retomar conversación" → abre chat en Studio
  - "Agregar a campaña"
  - "Agregar nota"
  - "Cambiar stage" (manual override)
  - "Blacklist"

**Lo que hay que construir:**
- BE API: `GET /api/v1/crm/contacts/{id}/timeline` — eventos unificados paginados
- BE: join de Messages + JourneyEvents + LifecycleTransitions + Enrollments + Appointments
- FE: contact detail page con timeline

---

## 6. Impacto en Copilot

El Copilot debe poder responder queries CRM y ejecutar acciones de campaña. Ampliar `crm/copilot_provider/` con:

### Queries que debe responder:
- "¿Cuántos leads tengo?" / "¿Cuántos clientes?"
- "¿Quiénes son mis leads más calientes?"
- "¿Quién no ha respondido en 5 días?"
- "¿Cuánto llevo vendido este mes?"
- "¿Quiénes son mis mejores clientes?"
- "¿Qué contactos están en riesgo de irse?"
- "¿Cuántos nuevos leads entré esta semana?"

### Acciones que debe poder ejecutar:
- "Manda seguimiento a los que vieron el precio" → crea campaña
- "Agrega a María al segmento VIP"
- "Muéstrame el perfil de Juan García"
- "¿Cuándo fue la última vez que hablé con Ana?"
- "Agenda un recordatorio para llamar a Pedro mañana"

### Implementación:
- Ampliar `CRMCopilotProvider` con métodos para resolver estas queries
- Registrar nuevas tools en el tool registry del copilot:
  - `crm_get_pulse()` — attention queue + health metrics
  - `crm_search_contacts(query, filters)` — búsqueda contactos
  - `crm_get_contact_summary(contact_id)` — perfil + últimas interacciones
  - `crm_create_campaign(segment, channel, template)` — lanzar campaña
  - `crm_add_to_segment(contact_id, segment_id)` — acción sobre contacto

---

## 7. Impacto en Sales Agent

### Nuevo entry point: outbound initiation
Hoy el Sales Agent solo maneja inbound (alguien escribe primero).
Para campañas, necesita poder *iniciar* una conversación:

```python
# Nuevo método en ConversationPipeline
async def start_outbound_conversation(
    tenant_id: UUID,
    contact_id: UUID,
    campaign_id: UUID,
    template_context: dict
) -> None:
    # Carga perfil CRM del contacto
    # Construye contexto personalizado (historial, objeciones, stage)
    # Genera mensaje inicial via LLM con template + contexto
    # Envía por canal preferido del contacto
    # Registra como conversación nueva con campaign_attribution
```

### Enriquecimiento de contexto con CRM
El Sales Agent ya usa `copilot_provider` de CRM. Para campañas outbound, el contexto debe incluir:
- Historial de objeciones anteriores
- Compras previas (para no ofrecer algo ya comprado)
- Etapa en el funnel (personalizar pitch)
- Tiempo sin actividad (urgency framing)

### Attribution
- Conversaciones originadas por campaña llevan `campaign_id` en AgentState
- Enrollments generados en esas conversaciones → atribuidos a la campaña
- Sales Agent reporta evento: `campaign_conversion` → CampaignTask.enrollment_id

---

## 8. Impacto en Futuros Agentes

### Email Marketing Agent (próximo)
- Consumes el mismo `Campaign` model con `agent_type="email"`
- Lee el `Segment` para obtener lista de destinatarios con emails (via `CustomerIdentity`)
- Usa CRM profile para personalizar subject line + body
- Reporta aperturas/clics → creates JourneyEvents → actualiza lead_score

### Content Agent (próximo)
- Puede sugerir content ideas basadas en el segmento más activo del tenant
- "Tu segmento MQL está interesado en X según las conversaciones" → content idea
- Copy de campañas outbound lo puede generar el Content Agent antes de ejecutarse

### El CRM como columna vertebral (arquitectura)
```
EMPRENDEDOR
    │
    ▼
COPILOT (account manager conversacional)
    │
    ├──[queries]──► CRM Hub (leer datos)
    ├──[acciones]─► Campaign API (crear campañas)
    └──[routing]──► Agentes especializados
                        │
                        ├── Sales Agent (inbound + outbound campaigns)
                        ├── Email Agent [futuro]
                        ├── Content Agent [futuro]
                        └── ...
                            │
                            └──[write back]──► CRM Hub (journey_events, notas, scores)
```

---

## 9. Scope MVP Recomendado

### Fase 1 — "Personas" básico (2-3 semanas)
- API: `GET /crm/contacts` con filtros + paginación
- API: `GET /crm/contacts/{id}/timeline`
- FE: Contact list + Contact detail (reemplaza stub `/sales/contactos`)
- FE: Copilot tools: `crm_search_contacts`, `crm_get_contact_summary`

### Fase 2 — "Pulso" (1-2 semanas)
- BE: `PulseService.get_attention_queue()`
- API: `GET /crm/pulse`
- FE: Pulso dashboard (lifecycle distribution + attention queue)
- Copilot tool: `crm_get_pulse()`

### Fase 3 — "Segmentos" (2-3 semanas)
- BE Domain: `Segment` model + `SegmentService`
- API: CRUD segments + `GET /crm/segments/{id}/members`
- FE: Segment builder con filter conditions + preview count
- Segmentos preconstruidos del sistema

### Fase 4 — "Campañas" outbound (3-4 semanas)
- BE Domain: `Campaign` + `CampaignTask` models
- BE: `CampaignService.launch()` + worker integration
- Sales Agent: nuevo `start_outbound_conversation()` entry point
- API: CRUD campaigns + metrics
- FE: Campaign builder + progress tracking
- Copilot tool: `crm_create_campaign()`

### Fase 5 — RFM + Enriquecimiento (2-3 semanas)
- BE: RFM calculation engine (usa datos en `Sale` ya existentes)
- FE: RFM segment badges en contact profiles
- Enrichment waterfall: IG → email → web (generalizar `IgProfileEnricher`)

---

## 10. Preguntas abiertas para el usuario

1. **Outbound channels priority:** ¿El primer canal de campañas outbound debería ser WhatsApp (vía ManyChat/Baileys), Telegram, o email?

2. **Manual campaigns:** ¿El emprendedor debería poder escribir el template del mensaje, o siempre dejamos que el Sales Agent lo personalice con IA?

3. **Contactos externos:** ¿Los contactos solo vienen del Sales Agent (inbound) o el emprendedor debería poder importar una lista CSV de contactos existentes?

4. **Segmentos y privacidad:** ¿El emprendedor necesita compartir segmentos con su equipo (ej: vendedores humanos) o es solo para uso del agente?

5. **Notas y recordatorios:** ¿Las notas manuales en contactos son críticas para el MVP, o se pueden diferir?

6. **Contacto individual desde Studio:** Cuando estás en el Studio viendo una conversación, ¿debería haber un botón directo que lleve al perfil CRM de ese contacto?

---

## 11. File Changes Required (cuando se implemente)

### Backend (nuevos archivos)
```
backend/src/modules/crm/
  domain/
    segment.py                    # Segment + SegmentFilter domain models
    campaign.py                   # Campaign + CampaignTask domain models
    pulse.py                      # PulseItem + attention score logic
  application/services/
    segment_service.py            # Segment CRUD + member resolution
    campaign_service.py           # Campaign lifecycle + task queue
    pulse_service.py              # Attention queue generation
  api/
    contacts.py                   # GET /contacts, GET /contacts/{id}/timeline
    segments.py                   # CRUD /segments
    campaigns.py                  # CRUD /campaigns + metrics
    pulse.py                      # GET /pulse
    dto/
      contacts.py
      segments.py
      campaigns.py
      pulse.py
  copilot_provider/
    data_access.py                # Ampliar con segment/campaign queries
    provider.py                   # Ampliar con nuevas tools

backend/src/modules/sales_agent/
  application/orchestrator/
    outbound_pipeline.py          # Nuevo: start_outbound_conversation()
  workers/
    campaign_executor.py          # Nuevo: procesa CampaignTask queue
```

### Frontend (nuevos archivos)
```
frontend/src/
  app/(main)/[tenantId]/(dashboard)/sales/
    contactos/page.tsx            # Reemplaza stub (usar feature crm-hub)
    contactos/[contactId]/page.tsx # Contact detail
    segmentos/page.tsx            # Nueva ruta
    campanas/page.tsx             # Nueva ruta
    pulso/page.tsx                # Nueva ruta

  features/crm-hub/
    api/
      contacts-api.ts
      segments-api.ts
      campaigns-api.ts
      pulse-api.ts
    components/
      contacts/
        ContactList.tsx
        ContactCard.tsx
        ContactDetail.tsx
        ContactTimeline.tsx
        ContactFilters.tsx
      segments/
        SegmentList.tsx
        SegmentBuilder.tsx        # Filter condition builder
        SegmentPreview.tsx
      campaigns/
        CampaignList.tsx
        CampaignBuilder.tsx
        CampaignProgress.tsx
        CampaignMetrics.tsx
      pulse/
        PulseDashboard.tsx
        AttentionQueue.tsx
        LifecycleChart.tsx
        ActivityFeed.tsx
    hooks/
      use-contacts.ts
      use-segments.ts
      use-campaigns.ts
      use-pulse.ts
    types/
      contact.ts
      segment.ts
      campaign.ts
      pulse.ts
```

### Sidebar (modificación)
```typescript
// AppSidebar.tsx — ampliar Closer Studio group
{
  title: "CRM Hub",
  children: [
    { label: "Contactos", route: "/sales/contactos" },
    { label: "Segmentos", route: "/sales/segmentos" },
    { label: "Campañas", route: "/sales/campanas" },
    { label: "Pulso", route: "/sales/pulso" },
  ]
}
```

---

## 12. Prototype Reference
Prototipo HTML: pendiente (requiere alineación funcional con usuario primero)
Servidor: http://localhost:8888

---

*Generado por ux-flow-architect — 2026-04-29*
