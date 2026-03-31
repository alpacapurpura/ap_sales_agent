# 10 — Data Models

## Vision General

El Sales Agent interactua con 5 tablas principales distribuidas en 3 modulos (DDD bounded contexts). Todas las tablas soportan soft deletes y tenant isolation.

```
┌─────────────────────────────────────────────────────────────┐
│                     sales_agent module                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   messages    │  │ agent_traces │  │   llm_logs   │      │
│  │              │  │              │  │              │      │
│  │ user_id (FK) │  │ user_id      │  │ trace_id(FK) │      │
│  │ tenant_id    │  │ tenant_id    │  │              │      │
│  │ role         │  │ node_name    │  │ model        │      │
│  │ content      │  │ input_state  │  │ prompt_*     │      │
│  │ channel      │  │ output_state │  │ response     │      │
│  └──────┬───────┘  │ exec_time_ms │  │ tokens_*     │      │
│         │          └──────────────┘  └──────────────┘      │
│         │                                                   │
│  ┌──────┼──────────────────────────────────────────┐        │
│  │      │            prompt_versions               │        │
│  │      │  key, version, content, tenant_id        │        │
│  └──────┼──────────────────────────────────────────┘        │
└─────────┼───────────────────────────────────────────────────┘
          │ FK: leads.id
┌─────────▼───────────────────────────────────────────────────┐
│                        crm module                           │
│                                                             │
│  ┌──────────────┐     ┌────────────────┐                    │
│  │    leads      │     │ customer_      │                    │
│  │              │ FK  │ profiles       │                    │
│  │ customer_id ──────►│                │                    │
│  │ profile_data │     │ full_name      │                    │
│  │ fit_score    │     │ traits (JSONB) │                    │
│  │ temperature  │     │ lead_source    │                    │
│  │ style_profile│     └────────┬───────┘                    │
│  └──────────────┘              │                            │
│                         ┌──────▼───────┐                    │
│                         │ customer_    │                    │
│                         │ identities   │                    │
│                         │              │                    │
│                         │ identity_type│                    │
│                         │ identity_val │                    │
│                         │ tenant_id    │                    │
│                         └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     connections module                       │
│                                                             │
│  ┌───────────────────┐                                      │
│  │ channel_connections│                                      │
│  │                   │                                      │
│  │ tenant_id (FK)    │                                      │
│  │ channel_type      │                                      │
│  │ credentials (ENC) │  ← Fernet encrypted at rest          │
│  │ config (JSONB)    │                                      │
│  │ is_active         │                                      │
│  └───────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. MessageModel (messages)

**Archivo:** `backend/src/modules/sales_agent/infrastructure/models/message_model.py` (L8-38)

```python
class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("leads.id"), nullable=True, index=True)
    tenant_id = Column(UUID, nullable=True, index=True)
    role = Column(String, nullable=False)         # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    channel = Column(String, nullable=True)        # "whatsapp" | "telegram" | "instagram" | "api"
    product_context_id = Column(UUID, nullable=True)
    metadata_log = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("LeadModel", back_populates="messages", foreign_keys=[user_id])
```

**Campos clave:**
- **`user_id`:** Apunta a `leads.id` (no al customer directamente). Un lead es una "oportunidad" de venta.
- **`role`:** Sigue la convencion OpenAI — "user" para mensajes del prospecto, "assistant" para respuestas del agente.
- **`metadata_log`:** JSONB libre para guardar intent detectado, scores, etc.
- **`product_context_id`:** Para asociar el mensaje con un producto especifico (ej: cuando se habla de una oferta concreta).

**Backward compatibility aliases (L27-37):**
```python
@property
def lead_id(self):
    return self.user_id  # Old name

@property
def sender_type(self):
    return self.role  # Old name
```

---

## 2. AgentTrace (agent_traces)

**Archivo:** `backend/src/modules/sales_agent/infrastructure/models/agent_trace_model.py` (L8-32)

```python
class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, nullable=True, index=True)       # Lead ID
    tenant_id = Column(UUID, nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)   # "sess_{user_id}_{hour}"
    node_name = Column(String, nullable=False)                # "sales_supervisor", "qualifier", etc.
    input_state = Column(JSONB, default=dict)                 # Snapshot del state al entrar al nodo
    output_state = Column(JSONB, default=dict)                # Snapshot del state al salir
    execution_time_ms = Column(Float, nullable=True)

    # RL / Feedback Loop (future use)
    action = Column(String, nullable=True)
    reward = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    llm_logs = relationship("LLMLog", back_populates="trace", cascade="all, delete-orphan")
```

**Notas:**
- **Loose coupling:** No usa FK a `leads` ni `tenants`. Solo guarda UUIDs. Esto previene dependencias circulares entre modulos DDD.
- **session_id:** Formato `"sess_{user_id}_{hour_timestamp}"`. Agrupa traces de la misma hora para analisis de sesion.
- **RL fields:** `action`, `reward`, `feedback` estan preparados para un futuro sistema de reinforcement learning (Data Flywheel).

---

## 3. LLMLog (llm_logs)

**Archivo:** `backend/src/modules/sales_agent/infrastructure/models/llm_log_model.py` (L8-26)

```python
class LLMLog(Base):
    __tablename__ = "llm_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    trace_id = Column(UUID, ForeignKey("agent_traces.id"), nullable=True)
    model = Column(String, nullable=False)                # "gpt-4o-mini", "claude-3-haiku", etc.
    prompt_template = Column(String, nullable=True)        # "supervisor_routing", "specialist_qualifier"
    prompt_rendered = Column(Text, nullable=False)         # Full rendered prompt sent to LLM
    response_text = Column(Text, nullable=False)           # LLM response
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    metadata_info = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trace = relationship("AgentTrace", back_populates="llm_logs")
```

**Proposito:** Registro completo de cada llamada LLM. Permite:
- **Debug:** Ver exactamente que prompt se envio y que respondio el LLM.
- **Cost tracking:** Contar tokens para facturacion.
- **Optimization:** Identificar prompts que generan respuestas malas o caras.

---

## 4. PromptVersion (prompt_versions)

**Archivo:** `backend/src/modules/sales_agent/infrastructure/models/prompt_version_model.py` (L7-19)

```python
class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    key = Column(String, index=True, nullable=False)       # "supervisor_routing"
    version = Column(Integer, nullable=False)               # 1, 2, 3...
    content = Column(Text, nullable=False)                  # Jinja2 template content
    is_active = Column(Boolean, default=True)
    change_reason = Column(String, nullable=True)
    author_id = Column(String, nullable=True)               # "system" or user UUID
    metadata_info = Column(JSONB, default=dict)             # target_node, target_model
    tenant_id = Column(UUID, nullable=True)                 # NULL = system, UUID = tenant override
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Ver [07-PROMPT-SYSTEM.md](07-PROMPT-SYSTEM.md) para detalle de uso.

---

## 5. LeadModel (leads)

**Archivo:** `backend/src/modules/crm/infrastructure/models/lead_model.py` (L8-55)

```python
class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customer_profiles.id"), nullable=True)

    # Channel-specific IDs (legacy, pre-CDP)
    telegram_id = Column(String, unique=True, nullable=True)
    whatsapp_id = Column(String, unique=True, nullable=True)
    instagram_id = Column(String, unique=True, nullable=True)
    tiktok_id = Column(String, unique=True, nullable=True)
    api_id = Column(String, unique=True, nullable=True)

    # Profile (full qualification data)
    profile_data = Column(JSONB, default={})

    # Scoring
    fit_score = Column(Integer, default=0)
    intent_score = Column(Integer, default=0)
    temperature = Column(String, default="COLD")          # COLD | WARM | HOT

    is_blacklisted = Column(Boolean, default=False)
    last_interaction_date = Column(DateTime, nullable=True)
    next_scheduled_action = Column(DateTime, nullable=True)

    # Deep Memory
    conversation_summary = Column(Text, nullable=True)
    key_objections_history = Column(JSONB, default=[])
    style_profile = Column(JSONB, default={})
    custom_system_instruction = Column(String, nullable=True)

    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True)
    messages = relationship("MessageModel", back_populates="lead", cascade="all, delete-orphan")
```

**Notas:**
- **Dual identity:** `customer_id` apunta al CDP (Customer Data Platform), pero los `telegram_id`, `whatsapp_id` legacy siguen existiendo para backward compat.
- **`style_profile`:** Output del "Psychologist" — personalidad detectada del lead para adaptar el tono.
- **`custom_system_instruction`:** Output del "Architect" — instruccion custom para el agente al hablar con este lead.

---

## 6. ChannelConnectionModel (channel_connections)

**Archivo:** `backend/src/modules/connections/infrastructure/models/channel_connection_model.py` (L9-25)

```python
class ChannelConnectionModel(Base):
    __tablename__ = "channel_connections"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
    channel_type = Column(String, nullable=False)         # "telegram", "whatsapp", "meta", etc.
    credentials = Column(EncryptedJSON, default={})        # ← Fernet encryption at rest
    config = Column(JSONB, default={})                     # Non-sensitive (metadata, welcome msg)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

**Seguridad critica:**
- **`credentials`:** Usa `EncryptedJSON` — un tipo custom de SQLAlchemy que encripta/desencripta con Fernet (AES-128-CBC). API tokens, bot tokens, y access tokens se guardan encriptados en la BD.
- **`config`:** JSONB sin encriptar — para datos no sensibles como metadata del perfil, welcome messages, asset IDs.

---

## Relaciones entre Tablas

```
tenants
  │
  ├─── channel_connections (tenant_id FK)
  │
  ├─── leads (tenant_id FK)
  │      │
  │      ├─── messages (user_id FK → leads.id)
  │      │
  │      └─── customer_profiles (customer_id FK)
  │             │
  │             └─── customer_identities
  │
  ├─── agent_traces (tenant_id, no FK — loose coupling)
  │      │
  │      └─── llm_logs (trace_id FK)
  │
  └─── prompt_versions (tenant_id, no FK)
```
