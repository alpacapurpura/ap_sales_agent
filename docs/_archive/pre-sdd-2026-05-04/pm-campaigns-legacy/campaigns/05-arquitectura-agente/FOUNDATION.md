# Agentic Architecture Foundation — Campaign System
**Fecha:** 2026-04-29  
**Última actualización:** 2026-04-29 (decisiones A/B/C confirmadas)
**Tipo:** Documento arquitectónico fundacional — PRE-CÓDIGO
**Autor:** Chris + Claude (Code Review of actual codebase: sales_agent, copilot, crm, connections)

---

## Decisiones Arquitectónicas Confirmadas

| # | Decisión | Veredicto | Razón |
|---|----------|-----------|-------|
| A | ¿Dónde vive el Commercial Director? | **Copilot subagent** (4to subagent, paralelo a audit_inspector/url_analyzer/data_query) | Industry standard: planning ≠ execution. Sales Agent = B2C only. Copilot es el único punto de contacto del emprendedor. |
| B | ¿Empezar por Telegram? | **Sí, Telegram-first** | Zero aprobaciones Meta. Ya implementado en Sales Agent. Ideal para pruebas internas. |
| C | ¿Módulo independiente? | **Sí, `campaigns/` independiente** | Máxima escalabilidad. Non-breaking para módulos existentes. |

---

## Por qué este documento existe

El patrón histórico en este proyecto: se implementa un MVP, luego llega una feature nueva que no encaja, y se hace refactoring. Este documento interrumpe ese ciclo.

**Premisa:** Antes de tocar código, definir la arquitectura agéntica completa para los próximos 12-18 meses. Cada MVP subsecuente es una extensión, no una reescritura.

---

## 1. El Sistema de Agentes — Roles y Responsabilidades

### El principio ordenador

```
ENTREPRENEUR ←→ COPILOT (Account Manager)
                    │
                    │ orquesta
                    ↓
         CAMPAIGN ORCHESTRATOR
              │         │
              ↓         ↓
       SALES AGENT   EMAIL AGENT
       (B2C conv.)  (MailerLite)
              │
       leads/customers
```

**Regla invariante:**
- El **Copilot** habla con el emprendedor. Nunca con leads.
- El **Sales Agent** habla con leads/clientes. Nunca con el emprendedor.
- Ambos existen hoy. Lo que falta es el puente: **Campaign Orchestrator**.

### 1.1 Copilot — Account Manager

**Estado actual:** Implementado (deep_agent.py, F8 rebuild).

**Rol:** Asistente operacional del emprendedor. Configura el negocio, lee métricas, propone cambios, guía el setup. **Ya tiene** 3 subagentes (audit_inspector, url_analyzer, data_query).

**Extensión para campañas:** Agregar un 4to subagente.

```python
MARKETING_CAMPAIGN_SUBAGENT = {
    "name": "marketing_campaign",
    "description": "Diseña y gestiona campañas de marketing. Crea campañas a partir de instrucciones conversacionales, consulta performance, pausa/activa campañas.",
    "system_prompt": "...",
    "tools": [campaign_create, campaign_get_status, campaign_pause, campaign_launch, ...]
}
```

**El emprendedor NO crea campañas en un formulario. Se lo dice al Copilot:**
> "Crea una campaña de seguimiento para mis leads que no respondieron en 5 días. Usa WhatsApp. El tono debe ser cercano, mencionar el programa de febrero."

El Copilot delega al `MARKETING_CAMPAIGN_SUBAGENT`, que crea el objeto `Campaign` en BD con los parámetros correctos. El emprendedor aprueba y lanza.

### 1.2 Sales Agent — Commercial Director

**Estado actual:** Implementado como SDR reactivo (inbound only). Tiene specialist routing (qualifier → product_expert → closer).

**El problema:** Hoy el Sales Agent solo reacciona cuando alguien le escribe. No puede iniciar conversaciones desde campañas.

**La extensión (NOT una reescritura):** Agregar un **outbound entry point**. El Sales Agent ya tiene toda la inteligencia (brand voice, specialist routing, channel adapters, tool registry). Solo necesita una nueva forma de activarse.

```
HOY:     Webhook → IdentityResolver → ChatOrchestrator → AgentState → Sales Graph
NUEVO:   CampaignTask → OutboundOrchestrator → AgentState(campaign_context) → Sales Graph
```

**El "Director Comercial":** No es un nuevo agente. Es el Sales Agent con `campaign_context` inyectado en su AgentState. Las `agent_instructions` de la campaña se convierten en un nuevo slot del prompt composer.

```python
# AgentState extensions (non-breaking additions)
campaign_id: UUID | None          # Si llegó por campaña
campaign_instructions: str | None  # Override de instrucciones (nuevo prompt slot)
outbound_mode: bool               # True = Sales Agent inició, False = usuario inició
campaign_channel: str | None      # Canal elegido por la campaña
```

**Supervisor routing para outbound:**

```
outbound_mode=True + primera interacción:
  → Skip qualifier (ya conocemos al lead del CRM)
  → Ir directo a product_expert o closer según temperatura del lead
  → Usar campaign_instructions como contexto adicional
```

Esto respeta la arquitectura actual. El supervisor existente ya lee `lead_score`, `temperature`, `buying_signals`. Solo agrega `outbound_mode` al condicional.

### 1.3 Email Agent — Próxima Fase (deferred)

**No construir ahora.** Hoy la estrategia correcta es: el Campaign Orchestrator llama directamente a la MailerLite API (agregar contacto a grupo → automation dispara). No necesitamos un agente para esto.

**Email Agent** tiene sentido cuando el content del email sea generado por IA (personalización 1:1 a escala). Eso es el Sprint 8+.

### 1.4 Agentes Futuros (no en roadmap inmediato)

| Agente | Rol | Cuando construir |
|--------|-----|-----------------|
| Content Agent | Genera copies, posts, visual briefs | Cuando 3+ tenants piden auto-publicación |
| Voice Agent | Follow-up telefónico (Vapi + ElevenLabs) | Cuando tenant piloto opt-in habilitado |
| Analytics Agent | Interpreta métricas, sugiere acciones | Cuando Growth Studio tenga dashboards completos |

---

## 2. El Modelo de Dominio de Campañas

### 2.1 Entidades núcleo (nuevo módulo `campaigns/`)

```python
# campaigns/domain/campaign.py

class CampaignType(StrEnum):
    AGENT_CONVERSATION  = "agent_conversation"  # Sales Agent outbound 1:1
    EMAIL_DRIP          = "email_drip"           # MailerLite group → automation trigger
    EMAIL_BROADCAST     = "email_broadcast"      # One-shot email to segment
    EVENT_TRIGGER       = "event_trigger"        # Multi-canal anclado a fecha (webinar/launch)
    PUSH_NOTIFICATION   = "push_notification"    # OneSignal (Tier 2)
    RETARGETING_EXPORT  = "retargeting_export"   # CRM → Meta Ads audience

class CampaignStatus(StrEnum):
    DRAFT     = "draft"
    SCHEDULED = "scheduled"
    ACTIVE    = "active"
    PAUSED    = "paused"
    COMPLETED = "completed"
    FAILED    = "failed"

@dataclass
class Campaign:
    id: UUID
    tenant_id: UUID
    name: str
    type: CampaignType
    status: CampaignStatus
    
    # Segmento objetivo
    segment_id: UUID | None         # Segmento dinámico CRM
    segment_snapshot: list[UUID]    # ContactProfile IDs al momento de lanzar
    
    # Configuración de canal
    channel_priority: list[str]     # ["telegram", "whatsapp", "email"]
    
    # Para AGENT_CONVERSATION
    agent_instructions: str | None  # Override de instrucciones al Sales Agent
    
    # Para EMAIL_DRIP
    mailerlite_group_slug: str | None  # Grupo MailerLite destino
    
    # Para EMAIL_BROADCAST
    mailerlite_campaign_id: str | None
    
    # Para EVENT_TRIGGER
    anchor_event_date: datetime | None
    steps: list[CampaignStep]
    
    # Attribution
    source_type: str | None         # "segment", "manual", "trigger"
    
    # Scheduling
    scheduled_at: datetime | None
    launched_at: datetime | None
    completed_at: datetime | None
    
    # Metadata
    created_by: str  # "copilot" | "api" | "manual"

@dataclass
class CampaignStep:
    """Para EVENT_TRIGGER campaigns — pasos anclados a fecha."""
    step_index: int
    offset_hours: int           # Negativo = antes del evento, positivo = después
    channel: str                # "email" | "whatsapp" | "telegram" | "push"
    template_slug: str | None   # Para canales que usan templates
    agent_instructions: str | None  # Para AGENT_CONVERSATION steps
    condition: str | None       # "enrolled" | "score_gte:60" (filtro adicional)

@dataclass
class CampaignTask:
    """Una tarea de ejecución por contacto × step."""
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    contact_id: UUID            # CustomerProfile.id
    step_index: int             # 0 para AGENT_CONVERSATION single-step
    
    status: CampaignTaskStatus  # PENDING | EXECUTING | SENT | RESPONDED | CONVERTED | FAILED | SKIPPED
    
    # Compliance checks
    channel_used: str | None    # Canal real usado al ejecutar
    compliance_check: dict      # {"waba_24h": True/False, "opted_in": True/False}
    
    # Attribution
    enrollment_id: UUID | None  # Si generó una inscripción/venta
    
    # Execution metadata
    scheduled_at: datetime
    executed_at: datetime | None
    failed_reason: str | None
    retries: int
```

### 2.2 Segmentos — First Class Citizens

Los segmentos son fundamentales. Sin segmentos, no hay campañas. Hoy el CRM tiene `CustomerProfile` con lifecycle_stage, lead_score, rfm_segment (campo, sin lógica). Necesitamos un `Segment` real.

```python
# campaigns/domain/segment.py

class SegmentType(StrEnum):
    DYNAMIC  = "dynamic"    # Se recalcula en cada ejecución
    STATIC   = "static"     # Snapshot tomado al crear la campaña

@dataclass
class SegmentFilter:
    """Un filtro AND-able para construir segmentos."""
    field: str              # "lifecycle_stage", "lead_score", "last_activity_at", "traits.{key}"
    operator: str           # "eq", "gte", "lte", "in", "not_in", "is_null", "contains"
    value: Any

@dataclass
class Segment:
    id: UUID
    tenant_id: UUID
    name: str
    type: SegmentType
    filters: list[SegmentFilter]   # AND logic
    estimated_size: int | None     # Calculado en background
    last_calculated_at: datetime | None
```

**Segmentos predefinidos (catálogo inicial):**

| Slug | Filtros |
|------|---------|
| `hot-leads-no-response` | stage=SQL, last_activity_at < now()-3d |
| `warm-leads-inactive` | stage=MQL, last_activity_at < now()-7d |
| `subscribers-no-email` | stage=SUBSCRIBER, primary_email IS NULL |
| `customers-upsell` | stage=CUSTOMER, lifetime_value < 500 |
| `churned-reactivation` | stage=CHURNED, first_conversion_at IS NOT NULL |
| `all-contacts` | No filters |

### 2.3 CampaignTemplate (reusabilidad)

Los emprendedores van a querer reusar estructuras de campañas. El Marketing Agent creará campañas desde templates.

```python
@dataclass
class CampaignTemplate:
    id: UUID
    tenant_id: UUID | None  # NULL = global template (Nicolify-provided)
    name: str
    type: CampaignType
    description: str
    default_agent_instructions: str | None
    default_steps: list[dict]  # Serialized CampaignStep list
    recommended_segments: list[str]  # Segment slugs
    tags: list[str]  # ["webinar", "launch", "reengagement"]
```

**Templates globales Nicolify (catálogo inicial):**
- `launch-4day` — Lanzamiento 4 días (EVENT_TRIGGER, EMAIL + WHATSAPP)
- `webinar-sequence` — Secuencia webinar (EVENT_TRIGGER, EMAIL)
- `cold-lead-reactivation` — Reactivación leads fríos (AGENT_CONVERSATION)
- `post-purchase-onboarding` — Onboarding post-venta (EMAIL_DRIP)
- `welcome-sequence` — Bienvenida nuevos suscriptores (EMAIL_DRIP)

---

## 3. El Campaign Orchestrator — El Puente

Este es el componente más crítico. Traduce un `Campaign` + `Segment` en `CampaignTask[]` ejecutados por los agentes correctos.

```
Campaign (ACTIVE)
    │
    ↓ CampaignOrchestrator.launch(campaign_id)
    │
    ├─ 1. Resolve segment → list[CustomerProfile]
    ├─ 2. For each contact: compliance_check (WABA 24h, opt-in, blacklist)
    ├─ 3. Create CampaignTask per contact (PENDING)
    └─ 4. Enqueue to ARQ worker

ARQ Worker: process_campaign_tasks()
    │
    ├─ Fetch PENDING tasks (batch)
    ├─ For each task:
    │   ├─ Route by campaign.type:
    │   │   ├─ AGENT_CONVERSATION → SalesAgentOutboundOrchestrator.start(task)
    │   │   ├─ EMAIL_DRIP → MailerLiteService.add_to_group(contact.email, group_slug)
    │   │   ├─ EMAIL_BROADCAST → MailerLiteService.send_campaign(ml_campaign_id)
    │   │   ├─ PUSH_NOTIFICATION → OneSignalService.send(player_id, message)
    │   │   └─ RETARGETING_EXPORT → MetaAdsService.upload_audience(contacts)
    │   │
    │   └─ Update CampaignTask.status (SENT/FAILED)
    │
    └─ When all tasks done: Campaign.status = COMPLETED
```

### 3.1 ChannelRouter — Decisión de canal por contacto

```python
class ChannelRouter:
    """Decide qué canal usar para un ContactProfile dado un Campaign."""
    
    def select_channel(
        self,
        contact: CustomerProfile,
        campaign: Campaign,
        db,
    ) -> tuple[str, str]:  # (channel_type, user_id_in_channel)
        
        # 1. Compliance check primero
        for channel in campaign.channel_priority:
            if channel == "whatsapp":
                lead = self._get_lead_by_channel(contact, "whatsapp", db)
                if lead and self._waba_in_window(lead):
                    return ("whatsapp", lead.whatsapp_id)
                # Fuera de ventana: solo si hay HSM template
                elif campaign.has_hsm_template:
                    return ("whatsapp_hsm", lead.whatsapp_id)
                    
            elif channel == "telegram":
                lead = self._get_lead_by_channel(contact, "telegram", db)
                if lead and lead.telegram_id:
                    return ("telegram", lead.telegram_id)  # No 24h limit
                    
            elif channel == "email":
                if contact.primary_email:
                    return ("email", contact.primary_email)
                    
            elif channel == "manychat":
                # ManyChat bridge para WhatsApp
                mc_id = contact.traits.get("manychat_subscriber_id")
                if mc_id:
                    return ("manychat", mc_id)
        
        # Ningún canal disponible
        raise NoChannelAvailable(contact_id=contact.id)
    
    def _waba_in_window(self, lead: Lead) -> bool:
        if not lead.last_activity_at:
            return False
        hours_since = (utc_now() - lead.last_activity_at).total_seconds() / 3600
        return hours_since < 24
```

### 3.2 ManyChat como Bridge para WhatsApp

Hasta tener acceso directo a WABA, ManyChat es el intermediario para WhatsApp. El diseño es idéntico desde el Campaign Orchestrator — solo cambia el adapter:

```
CampaignTask (channel=whatsapp) 
    ↓ ChannelRouter.select_channel()
    ↓ si manychat_subscriber_id en traits
    ↓ ManyChat API: POST /subscribers/{id}/send-message
    ↓ ManyChat reenvía a WhatsApp del suscriptor
```

**El dato clave que falta:** `manychat_subscriber_id` necesita guardarse en `CustomerProfile.traits` cuando ManyChat hace webhook de `subscriber.new`. Ya tenemos ese webhook — solo falta el handler que escriba en CRM.

**Cuando tengamos WABA directo:**
- El ChannelRouter ya prioriza "whatsapp" sobre "manychat"
- Solo necesitamos que el Lead tenga `whatsapp_id` en lugar de `manychat_subscriber_id`
- Zero cambio en Campaign Orchestrator, Campaign domain, o CampaignTask

---

## 4. El Nuevo Módulo `campaigns/`

### Estructura de directorios

```
backend/src/modules/campaigns/
├── domain/
│   ├── campaign.py           # Campaign, CampaignStep, CampaignTask, CampaignStatus enums
│   ├── segment.py            # Segment, SegmentFilter, SegmentResolver
│   ├── template.py           # CampaignTemplate
│   ├── channel_router.py     # ChannelRouter (compliance + selection logic)
│   ├── events.py             # CampaignLaunched, TaskCompleted, TaskFailed domain events
│   └── enums.py              # CampaignType, CampaignStatus, CampaignTaskStatus, ChannelType
│
├── infrastructure/
│   ├── models/
│   │   ├── campaign_model.py
│   │   ├── campaign_step_model.py
│   │   ├── campaign_task_model.py
│   │   ├── segment_model.py
│   │   └── campaign_template_model.py
│   ├── repositories/
│   │   ├── campaign_repository.py
│   │   ├── campaign_task_repository.py
│   │   └── segment_repository.py
│   └── external/
│       ├── mailerlite_service.py    # Implementar sync_contacts, add_to_group, etc.
│       ├── onesignal_service.py     # Placeholder (Tier 2)
│       └── meta_ads_service.py     # Placeholder (Tier 2)
│
├── application/
│   ├── services/
│   │   ├── campaign_service.py      # CRUD + lifecycle (draft→scheduled→active→completed)
│   │   ├── campaign_orchestrator.py # El puente — resolve segment → create tasks → enqueue
│   │   ├── segment_service.py       # Build + resolve segments
│   │   └── attribution_service.py  # CampaignTask.enrollment_id assignment
│   └── use_cases/
│       ├── launch_campaign.py
│       ├── pause_campaign.py
│       └── replay_failed_tasks.py
│
├── api/
│   ├── campaigns.py         # CRUD endpoints
│   ├── segments.py          # Segment builder endpoints
│   ├── templates.py         # Template catalog
│   ├── analytics.py         # Campaign performance endpoints
│   └── dto/
│       ├── campaign_dto.py
│       ├── segment_dto.py
│       └── analytics_dto.py
│
├── workers/
│   ├── campaign_execution_worker.py  # ARQ task: procesar CampaignTasks PENDING
│   ├── campaign_scheduler_worker.py  # ARQ task: activar campañas en scheduled_at
│   ├── segment_refresh_worker.py     # ARQ task: recalcular segment sizes
│   └── attribution_worker.py         # ARQ task: resolver enrollment_ids pendientes
│
└── copilot_provider/
    ├── __init__.py
    ├── provider.py          # CopilotProvider: expone tools + module_data al Copilot
    └── tools.py             # campaign_create, campaign_get_status, campaign_pause, etc.
```

### Migración (nueva tabla, non-breaking)

```sql
-- Idempotent migrations
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    segment_id UUID REFERENCES crm_segments(id),
    segment_snapshot JSONB DEFAULT '[]',
    channel_priority JSONB DEFAULT '["telegram","whatsapp","email"]',
    agent_instructions TEXT,
    mailerlite_group_slug VARCHAR(255),
    anchor_event_date TIMESTAMPTZ,
    scheduled_at TIMESTAMPTZ,
    launched_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_by VARCHAR(32) DEFAULT 'manual',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS campaign_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    step_index INT NOT NULL,
    offset_hours INT NOT NULL DEFAULT 0,
    channel VARCHAR(64) NOT NULL,
    template_slug VARCHAR(255),
    agent_instructions TEXT,
    condition VARCHAR(255),
    UNIQUE (campaign_id, step_index)
);

CREATE TABLE IF NOT EXISTS campaign_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    contact_id UUID NOT NULL,  -- CustomerProfile.id
    step_index INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    channel_used VARCHAR(64),
    compliance_check JSONB DEFAULT '{}',
    enrollment_id UUID,
    scheduled_at TIMESTAMPTZ NOT NULL,
    executed_at TIMESTAMPTZ,
    failed_reason TEXT,
    retries INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(32) NOT NULL DEFAULT 'dynamic',
    filters JSONB DEFAULT '[]',
    estimated_size INT,
    last_calculated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Índices críticos
CREATE INDEX IF NOT EXISTS ix_campaign_tasks_status ON campaign_tasks(tenant_id, status, scheduled_at);
CREATE INDEX IF NOT EXISTS ix_campaign_tasks_contact ON campaign_tasks(tenant_id, contact_id);
CREATE INDEX IF NOT EXISTS ix_campaigns_tenant ON campaigns(tenant_id, status);
```

---

## 5. Cambios en Módulos Existentes (Foundation)

### 5.1 CRM — CustomerProfile (non-breaking additions)

Campos que FALTAN y que son foundation para todo lo demás:

```sql
-- Agregar a customer_profiles (IF NOT EXISTS = idempotente)
ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS source_campaign_id UUID REFERENCES campaigns(id);
ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS source_ref VARCHAR(512);  -- utm_campaign, ref=landing_enero
ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS source_ad_id VARCHAR(255);  -- Meta ad_id desde CTWA
ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS preferred_channel VARCHAR(64);  -- canal preferido
```

**`source_campaign_id`:** Primera campaña que captó a este contacto. NUNCA se sobreescribe (first-touch attribution).
**`source_ref`:** El `?ref=` o UTM parameter del primer toque. NUNCA se sobreescribe.
**`preferred_channel`:** Inferido del `last_active_channel` en el Lead que más interactúa. Actualizable.

### 5.2 Sales Agent — Outbound Entry Point (nueva función, no modifica existente)

En `sales_agent/application/orchestrator/chat.py`, agregar:

```python
class OutboundOrchestrator:
    """
    Entry point para conversaciones iniciadas por campañas.
    NO modifica ChatOrchestrator (inbound). Es paralelo.
    """
    
    async def start_outbound_conversation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        contact_id: UUID,      # CustomerProfile.id
        campaign_id: UUID,
        agent_instructions: str,
        channel: str,          # Canal elegido por ChannelRouter
        channel_user_id: str,  # ID del usuario en ese canal
    ) -> bool:
        # 1. Cargar CustomerProfile + Lead
        contact = await contact_repo.get(contact_id, tenant_id)
        lead = await lead_repo.get_by_channel(contact_id, channel, tenant_id)
        
        # 2. Cargar TenantConfig (agent_identity, brand_voice)
        tenant_config = await self._build_tenant_config(db, tenant_id)
        
        # 3. Build AgentState con outbound_mode=True
        state = AgentState(
            messages=[],  # Sin historial — conversación nueva
            tenant_id=tenant_id,
            user_id=lead.id,
            session_id=str(uuid4()),
            outbound_mode=True,          # ← NUEVO
            campaign_id=campaign_id,     # ← NUEVO
            campaign_instructions=agent_instructions,  # ← NUEVO
            current_state="presentation" if lead.lead_score >= 40 else "discovery",
            lead_score=int(contact.lead_score),
            agent_identity=tenant_config.agent_identity,
            brand_voice=tenant_config.brand_voice,
            # ... demás campos del state
        )
        
        # 4. Resolver channel adapter
        adapter = ChannelAdapterFactory.create(channel, tenant_id, db)
        
        # 5. Invocar el graph (mismo graph que inbound — solo el state es diferente)
        result = await agent_app.ainvoke(state, config=...)
        
        # 6. Entregar respuesta via adapter
        await output_manager.process_response(
            channel_user_id, result["messages"][-1]["content"], adapter, channel
        )
        
        return True
```

**AgentState additions (non-breaking — nuevos campos opcionales):**

```python
# En state.py — solo agregar campos, no modificar existentes
outbound_mode: bool               # Default False (inbound)
campaign_id: UUID | None          # None = inbound
campaign_instructions: str | None  # None = no override
```

**Compose.py — nuevo slot para campaign_instructions:**

```python
# En PromptFragment enum
CAMPAIGN_CONTEXT = "campaign_context"  # Nuevo slot

# En build_specialist_system_prompt
if state.get("campaign_instructions"):
    fragments[PromptFragment.CAMPAIGN_CONTEXT] = f"""
## CONTEXTO DE CAMPAÑA
Esta conversación fue iniciada como parte de una campaña específica.
Instrucciones particulares para esta campaña:
{state["campaign_instructions"]}
"""

# Posición en el orden: entre STAGE_HINT y LEAD_SIGNALS
```

**Supervisor routing para outbound:**

```python
# En agents/sales/nodes.py — node_supervisor
# Agregar condición al routing logic (no modifica flujo inbound)

if state.get("outbound_mode") and not state.get("turn_count"):
    # Primera vuelta de outbound: ir directo a product_expert o closer
    # basado en lead_score (skip qualifier — ya conocemos al lead del CRM)
    if state.get("lead_score", 0) >= 70:
        next_node = "closer"       # SQL → ir directo a cerrar
    elif state.get("lead_score", 0) >= 40:
        next_node = "product_expert"  # MQL → mostrar propuesta de valor
    else:
        next_node = "qualifier"   # LEAD → aún necesita calificación
```

### 5.3 Copilot — Campaign Provider (nueva provider, no modifica existente)

```python
# campaigns/copilot_provider/provider.py

class CampaignCopilotProvider(CopilotProvider):
    
    def module_data(self) -> ModuleData:
        return ModuleData(
            module_id="campaigns",
            label="Campañas",
            description="Gestiona campañas de marketing: outbound conversacional, email drip, lanzamientos.",
            route_prefix="campaigns",
            keywords=["campaña", "campaign", "broadcast", "lanzamiento", "webinar", "email sequence"],
        )
    
    def tool_provider(self) -> ToolProvider:
        return ToolProvider(
            tool_groups={
                "campaign": [
                    campaign_get_status,    # read
                    campaign_list,          # read
                    campaign_get_tasks,     # read
                    campaign_launch,        # action
                    campaign_pause,         # action
                    campaign_create,        # action (via Marketing Campaign Subagent)
                    segment_list,           # read
                    segment_create,         # action
                ]
            }
        )
    
    def subagent(self) -> dict | None:
        """El Marketing Campaign Subagent vive aquí."""
        return MARKETING_CAMPAIGN_SUBAGENT
```

### 5.4 ManyChat Webhook — Enriquecimiento CRM (completar handler existente)

El webhook de `subscriber.new` ya existe en `connections/api/marketing_webhooks.py`. Falta escribir el `manychat_subscriber_id` en el CRM:

```python
# En _resolve_manychat_profile (marketing_webhooks.py)
# Completar con:
if event_type == "subscriber.new":
    # Guardar manychat_subscriber_id en CustomerProfile.traits
    if customer_profile:
        customer_profile.traits["manychat_subscriber_id"] = payload.get("id")
        customer_profile.traits["manychat_phone"] = payload.get("phone")
        
    # Capturar source_ref si viene del webhook
    if ref := payload.get("ref"):
        if not customer_profile.source_ref:  # First-touch: no sobreescribir
            customer_profile.source_ref = ref
```

---

## 6. El Canal de Pruebas — Telegram First

### Por qué Telegram para el MVP

| Criterio | Telegram | WhatsApp (WABA direct) | WhatsApp (ManyChat) |
|----------|----------|----------------------|---------------------|
| Requiere aprobación Meta | No | Sí | Sí (account ManyChat) |
| Ventana de 24h | No | Sí | Sí |
| Ya implementado en Sales Agent | Sí | Sí | Parcial |
| Multi-tenant webhook | Sí | Sí | No directo |
| Ideal para probar | ✅ | ❌ | Intermedio |

El Sales Agent ya tiene Telegram implementado completamente (multi-tenant webhook, adapter, service). El OutboundOrchestrator puede enviar por Telegram sin cambios adicionales.

**Ruta de madurez de canales:**

```
MVP 0: Telegram (tests internos, sin aprobaciones)
MVP 1: ManyChat bridge para WhatsApp (tenants con ManyChat conectado)
MVP 2: WhatsApp WABA directo (cuando tengamos aprobación Meta)
MVP 3: Instagram DM (cuando tengan IG Business conectado)
MVP 4: TikTok DM via ManyChat (cuando tengan TikTok Business en connections)
```

---

## 7. Progressive MVP Plan — Foundation → Entregable

### Pre-MVP: La Fundación (1-2 semanas)

**Objetivo:** Crear las bases que ningún MVP subsecuente tenga que reescribir.

**Entregables:**
1. `campaigns/` module con domain models, infra, migrations
2. `crm_segments` tabla + SegmentResolver básico (lifecycle_stage + lead_score filters)
3. CustomerProfile: agregar 4 campos missing (source_campaign_id, source_ref, source_ad_id, preferred_channel)
4. Campaign API: CRUD básico (draft → scheduled → active)
5. AgentState: agregar 3 campos opcionales (campaign_id, campaign_instructions, outbound_mode)
6. CAMPAIGN_CONTEXT prompt slot en compose.py
7. OutboundOrchestrator: clase nueva paralela a ChatOrchestrator
8. CampaignExecutionWorker ARQ: procesa CampaignTask PENDING → OutboundOrchestrator

**Criterio de éxito:** Puedo crear una Campaign en la BD, enqueue tasks, y el Sales Agent los ejecuta via Telegram con campaign_instructions aplicadas.

**Tests requeridos (TDD):**
```
tests/modules/campaigns/test_campaign_domain.py
tests/modules/campaigns/test_segment_resolver.py
tests/modules/campaigns/test_campaign_orchestrator.py
tests/modules/sales_agent/test_outbound_orchestrator.py
tests/modules/sales_agent/test_outbound_state_routing.py
tests/modules/sales_agent/test_campaign_context_slot.py
```

### MVP 1: Primera Campaña Funcional (1 semana)

**Tipo:** `AGENT_CONVERSATION`, canal Telegram, segmento manual.

**Flujo end-to-end:**
1. Emprendedor crea Segment ("mis leads MQL sin respuesta hace 5 días")
2. Emprendedor crea Campaign (AGENT_CONVERSATION, agent_instructions="Hola {nombre}, vi que preguntaste sobre {oferta}. ¿Tienes 5 minutos?")
3. Copilot tool `campaign_launch(campaign_id)` → CampaignOrchestrator.launch()
4. Se crean CampaignTasks (uno por contacto en segmento)
5. ARQ Worker procesa tasks → OutboundOrchestrator → Sales Agent → Telegram
6. Si el lead responde → conversación vive en Inbox con campaign_id tag

**No incluye:** Scheduling, steps, email, WhatsApp.

### MVP 2: Scheduling + Multi-canal (2 semanas)

- CampaignSchedulerWorker: activa campañas en `scheduled_at`
- ChannelRouter: Telegram → ManyChat fallback si el lead tiene ambos
- Copilot: puede crear campañas conversacionalmente ("programa una campaña para el lunes a las 10am")
- MARKETING_CAMPAIGN_SUBAGENT registrado

### MVP 3: MailerLite Bridge (1-2 semanas)

- Implementar `sync_contacts` (stub → real)
- EMAIL_DRIP campaign: Campaign Orchestrator → `MailerLiteService.add_to_group(email, group_slug)`
- ManyChat `subscriber.new` → CustomerProfile.traits["manychat_subscriber_id"]
- 7 trigger mappings (MQL reached → add to "leads-calificados" group)

### MVP 4: Event Campaign — Webinar (3 semanas)

- CampaignStep[] con offset_hours
- EVENT_TRIGGER type: `anchor_event_date` como referencia
- CampaignSchedulerWorker: activa steps según offset calculado desde anchor
- Multi-canal por step: Email (MailerLite) + Telegram/WhatsApp (Sales Agent)
- Copilot puede crear desde template: "lanzar webinar template para el 15 de mayo"

### MVP 5: CRM Hub Frontend (2 semanas)

- UI en `/sales/contactos` (stub actual) → CRM Hub real
- Tabla de contactos con filtros por lifecycle_stage, lead_score, source_campaign_id
- Segment builder visual
- Campaign launcher desde CRM Hub

---

## 8. Preguntas abiertas antes de iniciar código

1. **`campaign_instructions` — formato:** ¿Texto libre que el emprendedor escribe, o plantillas con variables (`{nombre}`, `{oferta}`)? Recomiendo variables básicas en MVP 1, texto libre OK.

2. **Segment resolver scope — MVP 1:** ¿Solo filtros por lifecycle_stage + lead_score son suficientes para el primer segmento? ¿O también necesitamos `last_activity_at > N días`?

3. **Outbound reply handling:** Cuando el lead responde a un mensaje de campaña vía Telegram, ¿el ChatOrchestrator (inbound) debe detectar que la conversación viene de una campaña? ¿Cómo? (Propuesta: verificar si hay CampaignTask con status=SENT para ese lead en las últimas 24h)

4. **ManyChat bridge — timing:** ¿Cuántos de los tenants actuales ya tienen ManyChat conectado? Eso determina si ManyChat bridge va en MVP 1 o MVP 2.

5. **Campaign analytics — mínimo:** Para MVP 1, ¿es suficiente mostrar `SENT / RESPONDED / CONVERTED` counts, o necesitamos más?

---

## 9. Lo que NO cambia (invariantes protegidos)

1. **ChatOrchestrator (inbound) no se modifica.** El OutboundOrchestrator es paralelo, no un fork.
2. **El grafo LangGraph del Sales Agent no se modifica.** Solo se agregan campos opcionales al state.
3. **La arquitectura DDD de cada módulo existente no se modifica.** El módulo `campaigns/` es nuevo y limpio.
4. **Los channels adapters existentes no se modifican.** El OutboundOrchestrator los usa tal como están.
5. **El Copilot provider pattern no se modifica.** Solo se agrega un nuevo CopilotProvider desde `campaigns/`.
6. **Los tests existentes no se rompen.** Los nuevos campos del AgentState son opcionales con defaults.

---

## Resumen ejecutivo — La pregunta para Chris

¿Esta arquitectura refleja lo que tienes en mente?

Antes de escribir una línea de código, necesito tu confirmación en:

**A)** ¿Estás de acuerdo en que el "Director Comercial" vive dentro del Sales Agent (via campaign_instructions slot) en lugar de ser un agente separado?

**B)** ¿El MVP 1 (Telegram-only, campaign_id en state, OutboundOrchestrator) es el punto de partida correcto?

**C)** ¿El módulo `campaigns/` como módulo independiente (no extendiendo crm/ ni sales_agent/) es la decisión correcta?

Con esas 3 confirmaciones, arrancamos con TDD y nunca miramos atrás.
