# 04 — Chat Orchestrator

## Vision General

`ChatOrchestrator.process_chat_flow()` es el **corazon del Sales Agent**. Es el metodo que recibe un mensaje ya debounced y ejecuta todo el pipeline: identificacion de cliente, persistencia, construccion de identidad, invocacion del agente LLM, y envio de respuesta.

**Archivo:** `backend/src/modules/sales_agent/application/orchestrator/chat.py` (L203-463)

---

## ChatOrchestrator (Singleton)

```python
class ChatOrchestrator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.buffer_service = SmartBufferService()
        self._initialized = True
```

**Por que Singleton?** El `SmartBufferService` mantiene una conexion a Redis. Multiples instancias crearian conexiones redundantes. Ademas, los routers de FastAPI instancian `ChatOrchestrator()` a nivel de modulo (al importar), asi que el singleton garantiza que todos comparten el mismo buffer.

---

## process_chat_flow: Paso a Paso

### Paso 0: Typing Indicator (L216-219)
```python
await channel_adapter.set_typing_status(incoming.user_id)
```
Refuerza el indicador "Escribiendo..." ahora que el procesamiento real comienza. Es un feedback visual para el usuario.

### Paso 1: Tenant Context (L207-238)
```python
if tenant_id:
    set_tenant_id(UUID(tenant_id))

db = SessionLocal()
# ... repos initialization ...

if tenant_id:
    tenant_uuid = UUID(tenant_id)
    tenant_obj = db.query(TenantModel).filter(TenantModel.id == tenant_uuid).first()
    tenant_config = tenant_obj.config_json or {}
```

- **`set_tenant_id()`:** Context variable global (via `contextvars`). Todos los servicios downstream lo leen para filtrar queries por tenant.
- **`tenant_config`:** JSON libre del tenant (configuraciones custom). Se pasa al AgentState para que los nodos LLM puedan usarlo.
- **Session DB manual:** Se crea un `SessionLocal()` porque estamos fuera del ciclo de vida de FastAPI Depends (somos un background task).

### Paso 2: Customer Identity (L240-302)
```python
# Map channel to IdentityType
identity_type = IdentityType(channel_type)  # telegram → IdentityType.TELEGRAM

# Prepare Profile Data from metadata
profile_data = {
    "first_name": incoming.metadata.get("first_name"),
    "last_name": incoming.metadata.get("last_name"),
    "traits": incoming.metadata
}

# Get or Create Customer
capture_slug = CHANNEL_TYPE_TO_CAPTURE_SLUG.get(channel_type, channel_type)
customer, was_created = identity_service.get_or_create_customer(
    tenant_id=tenant_uuid,
    identity_type=identity_type,
    identity_value=user_id_str,
    profile_data=profile_data,
    lead_source=capture_slug,
    lead_source_detail=channel_type,
)
```

**Flujo de Identity Resolution:**
```
channel_type="telegram", user_id="123456789"
                │
                ▼
IdentityService.get_or_create_customer()
                │
                ├─ Busca en customer_identities:
                │   WHERE identity_value="123456789"
                │     AND identity_type="telegram"
                │     AND tenant_id=<UUID>
                │
                ├─ Encontrado → return (customer, False)
                │
                └─ No encontrado → CREATE:
                     customer_profiles (full_name, traits)
                     customer_identities (type=telegram, value=123456789)
                     return (customer, True)
```

### Emision de LeadCapturedEvent (L268-279)
```python
if was_created and tenant_uuid:
    EventBus.publish(
        LeadCapturedEvent.create(
            tenant_id=tenant_uuid,
            profile_id=customer.id,
            channel_slug=capture_slug,  # "telegram-dm", "ig-dm", etc.
            extracted_field="external_id",
            source_channel_type=channel_type,
        ),
        session=db,  # Deferred: se despacha despues del commit
    )
```
- **Solo para nuevos perfiles.** Un usuario que ya escribio antes no genera otro evento.
- **Deferred dispatch:** El evento se emite despues del `db.commit()`, asegurando que el perfil existe en la BD cuando los handlers lo procesen.
- **`capture_slug`:** Mapeo definido en `crm/domain/events.py:86-92`:
  ```python
  CHANNEL_TYPE_TO_CAPTURE_SLUG = {
      "instagram": "ig-dm",
      "facebook": "fb-messenger",
      "whatsapp": "whatsapp-inbound",
      "telegram": "telegram-dm",
  }
  ```

### Paso 2.5: Metadata Update (L282-302)
```python
if incoming.metadata:
    current_traits = dict(customer.traits) if customer.traits else {}
    for k, v in incoming.metadata.items():
        if k not in current_traits or current_traits[k] != v:
            current_traits[k] = v
            needs_update = True
    if needs_update:
        profile_model.traits = current_traits
        db.commit()
```
- **Actualizacion incremental:** Solo actualiza traits que cambiaron.
- **Por que?** El username de Telegram puede cambiar entre sesiones. Esto mantiene el perfil actualizado.

### Paso 3: Lead & Session (L304-327)
```python
user = lead_repo.get_active_lead(customer.id)
if not user:
    user = lead_repo.create_lead(customer_id=customer.id, channel=channel_type, channel_user_id=user_id_str)

# Session timeout check
last_msg = audit_repo.get_last_message(user.id)
if last_msg and last_msg.created_at:
    time_diff = datetime.now(timezone.utc) - msg_time
    if time_diff > timedelta(hours=6):
        session_active = False  # Sessión expirada
    if last_msg.metadata_log:
        last_intent = last_msg.metadata_log.get("intent")
```
- **Lead vs Customer:** Un Customer puede tener multiples Leads (uno por cada "oportunidad de venta"). Se busca el Lead activo.
- **Session timeout = 6 horas:** Si no ha habido interaccion en 6h, la sesion se marca como inactiva. Esto afecta el comportamiento del agente (puede reintroducirse en vez de continuar la conversacion).
- **last_intent:** Se recupera de la metadata del ultimo mensaje para contexto de continuidad.

### Paso 4: Log User Message (L329-336)
```python
audit_repo.log_message(
    user_id=user.id,
    role="user",
    content=incoming.text,
    channel=channel_type,
    tenant_id=tenant_uuid
)
```
Persiste el mensaje del usuario en la tabla `messages` antes de procesarlo.

### Paso 5: Agent Identity Build (AKS) (L338-350)
```python
if tenant_uuid:
    knowledge_builder = TenantKnowledgeBuilder(db)
    agent_identity = knowledge_builder.build_identity(tenant_uuid)
```
Construye el "CLAUDE.md del agente" — un documento dinamico con toda la identidad del negocio. Ver [05-AGENT-IDENTITY-SYSTEM.md](05-AGENT-IDENTITY-SYSTEM.md).

**Rollback safety (L347-350):**
```python
except Exception as e:
    logger.warning(f"Could not build agent identity: {e}")
    try:
        db.rollback()
    except Exception:
        pass
```
Si falla (ej: el tenant no tiene Brand configurado), hace rollback para no dejar la sesion DB en estado sucio.

### Paso 6: State Preparation (L352-403)
```python
active_product, launch_stage = biz_repo.get_current_launch_product()

raw_history = audit_repo.get_chat_history(user.id, limit=10)
history = [{"role": msg.role, "content": msg.content} for msg in raw_history if msg.content]

initial_state = create_initial_state(
    user_id=str(user.id),
    tenant_id=str(tenant_id),
    tenant_config=tenant_config,
    history=history,
    user_profile={**base_profile, **incoming.metadata},
    session_active=session_active,
    active_enrollment=active_enrollment,
    active_product=active_product_dict,
    last_intent=last_intent,
    agent_identity=agent_identity
)

initial_state["messages"] = [{"role": "user", "content": incoming.text}]
```
- **History limit=10:** Solo las ultimas 10 interacciones para no exceder context windows.
- **user_profile merge:** Combina datos del Lead (profile_data, style_profile) con metadata del mensaje actual.
- **`messages` al final:** El mensaje del usuario se inyecta como el unico mensaje en `state["messages"]`. El historial va en `state["history"]` por separado.

### Paso 7: Semantic Intent Detection (L405-414)
```python
detected_intent, intent_score = SemanticRouter.detect_intent(
    incoming.text, tenant_id=tenant_uuid
)
if detected_intent:
    initial_state["detected_intent"] = detected_intent
```
Pre-routing hint para el supervisor. Ver [08-SEMANTIC-ROUTER.md](08-SEMANTIC-ROUTER.md).

### Paso 8: Agent Invocation (L416-429)
```python
async def _keep_typing():
    while True:
        await asyncio.sleep(3)
        await channel_adapter.set_typing_status(incoming.user_id)

typing_task = asyncio.create_task(_keep_typing())
try:
    result = await agent_app.ainvoke(initial_state)
finally:
    typing_task.cancel()
```
- **Typing polling cada 3s:** Mientras el agente piensa, se envia "typing" al canal cada 3 segundos. Esto mantiene al usuario informado de que algo esta pasando.
- **`agent_app.ainvoke`:** Invoca el grafo LangGraph compilado con el estado inicial.
- **finally cancel:** Asegura que el task de typing se cancela cuando el agente termina.

### Paso 9: Response Extraction + Send (L431-445)
```python
last_msg = result["messages"][-1]
bot_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)

audit_repo.log_message(user_id=user.id, role="assistant", content=bot_text, ...)

await OutputManager.process_response(incoming.user_id, bot_text, channel_adapter)
```
1. Extrae el ultimo mensaje del estado final del grafo.
2. Lo persiste como mensaje "assistant" en la tabla `messages`.
3. Lo envia via `OutputManager` (con chunking y typing simulation).

### Error Handling (L447-462)
```python
except Exception as e:
    logger.error(f"Error processing message: {e}", exc_info=True)
    error_msg = OutgoingMessage(user_id=incoming.user_id, text="⚠️ Lo siento, ocurrió un error técnico interno.")
    await channel_adapter.send_message(error_msg)
finally:
    lead_repo.close()
    audit_repo.close()
    biz_repo.close()
```
- **Fallback message:** Si algo falla, el usuario recibe un mensaje generico de error.
- **Cleanup:** Todas las sesiones DB se cierran en el `finally`.

---

## Flujo Visual Completo

```
process_chat_flow(adapter, incoming, tenant_id)
    │
    ├─ set_typing_status()
    ├─ SessionLocal()
    │
    ├─ [1] Tenant Config
    │     set_tenant_id() + query TenantModel
    │
    ├─ [2] Customer Identity
    │     IdentityService.get_or_create_customer()
    │     └─ if new → EventBus.publish(LeadCapturedEvent)
    │     └─ Update traits if changed
    │
    ├─ [3] Lead & Session
    │     get_active_lead() or create_lead()
    │     Check session timeout (6h)
    │     Recover last_intent
    │
    ├─ [4] Log User Message
    │     audit_repo.log_message(role="user")
    │
    ├─ [5] Agent Identity (AKS)
    │     TenantKnowledgeBuilder.build_identity()
    │
    ├─ [6] State Preparation
    │     create_initial_state()
    │     Inject messages, history, profile
    │
    ├─ [7] Semantic Intent
    │     SemanticRouter.detect_intent()
    │
    ├─ [8] Agent Invocation
    │     agent_app.ainvoke(state)
    │     (concurrent typing every 3s)
    │
    ├─ [9] Extract Response
    │     log_message(role="assistant")
    │     OutputManager.process_response()
    │
    └─ finally: close all repos
```

---

## Casuisticas

### Que pasa si el tenant no tiene Brand/Offer configurado?
`TenantKnowledgeBuilder.build_identity()` retorna un fallback minimo: "Eres un asistente de ventas profesional..." (`knowledge_builder.py:108-114`). El agente funciona pero sin conocimiento especifico del negocio.

### Que pasa si no hay historial de chat?
`history` sera una lista vacia. El agente trata al usuario como si fuera la primera interaccion.

### Que pasa si el agente LLM falla (timeout, API error)?
La excepcion se propaga hasta el catch general (L447). El usuario recibe "Lo siento, ocurrio un error tecnico interno." y el error se loguea con full traceback.

### Que pasa si el canal (Meta/Telegram API) esta caido al enviar la respuesta?
`OutputManager` catchea el error de envio por chunk (`output_manager.py:56-60`) y continua con los siguientes chunks. Si todos fallan, el usuario no recibe nada pero la respuesta esta logueada en la BD.

### Que pasa si no hay tenant_id (flujo legacy)?
Se genera un UUID aleatorio como tenant_id (`chat.py:388`). Esto permite que el sistema funcione en modo single-tenant sin romper nada.
