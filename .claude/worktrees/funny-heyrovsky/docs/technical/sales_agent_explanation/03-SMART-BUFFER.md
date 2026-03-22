# 03 — Smart Buffer (Debounce Inteligente)

## Vision General

El Smart Buffer resuelve un problema critico del chat en tiempo real: **los usuarios envian multiples mensajes seguidos antes de completar su pensamiento**. Sin buffer, cada mensaje dispara un procesamiento LLM separado, generando respuestas fragmentadas e incoherentes.

```
Usuario envia:                 Sin Buffer:              Con Smart Buffer:
  "Hola"         (t=0s)       → Respuesta 1            ┐
  "quiero"       (t=0.3s)     → Respuesta 2            ├── Acumula todo
  "saber el"     (t=0.8s)     → Respuesta 3            │
  "precio"       (t=1.2s)     → Respuesta 4            ┘
                                                        → 1 sola respuesta coherente
```

---

## 1. SmartBufferService (Redis)

**Archivo:** `backend/src/modules/sales_agent/infrastructure/external/buffer_service.py` (L9-101)

### Estructura de Redis
```
chat:buffer:{tenant_id:user_id}  →  List[str]    (mensajes acumulados)
chat:meta:{tenant_id:user_id}    →  Hash          (last_ts, channel_type, metadata_json)
chat:lock:{tenant_id:user_id}    →  String "locked" (NX, ex=30s)
```

### Metodos Clave

#### add_message (L26-42)
```python
def add_message(self, user_id: str, text: str, channel_type: str, metadata: dict = None):
    self.redis.rpush(self._key_buffer(user_id), text)     # Append al final de la lista
    self.redis.expire(self._key_buffer(user_id), 3600)    # TTL 1 hora (limpieza)
    meta = {"last_ts": time.time(), "channel_type": channel_type, "metadata_json": json.dumps(metadata or {})}
    self.redis.hset(self._key_meta(user_id), mapping=meta)
```
- **RPUSH:** Cada mensaje se agrega al final de la lista Redis. El orden se preserva.
- **TTL 1 hora:** Buffers abandonados se limpian automaticamente.
- **last_ts:** Timestamp de Unix. Es la pieza clave del mecanismo de debounce.

#### get_and_clear_buffer (L61-69)
```python
def get_and_clear_buffer(self, user_id: str) -> List[str]:
    pipe = self.redis.pipeline()
    pipe.lrange(self._key_buffer(user_id), 0, -1)  # Leer todo
    pipe.delete(self._key_buffer(user_id))           # Borrar atomicamente
    results = pipe.execute()
    return results[0]
```
- **Pipeline atomico:** Evita race conditions entre leer y borrar.

#### acquire_lock / release_lock (L77-84)
```python
def acquire_lock(self, user_id: str, expire: int = 30) -> bool:
    return bool(self.redis.set(self._key_lock(user_id), "locked", ex=expire, nx=True))
```
- **NX (Not Exists):** Solo adquiere si no existe. Previene procesamiento duplicado.
- **Expire 30s:** Safety net — si el proceso muere, el lock se libera automaticamente.

---

## 2. El Flujo de Debounce Completo

**Archivo:** `backend/src/modules/sales_agent/application/orchestrator/chat.py`

### Paso 0: Entrada del Webhook (_handle_incoming_webhook, L80-103)

```python
async def _handle_incoming_webhook(self, channel_adapter, payload, background_tasks, tenant_id=None):
    incoming = channel_adapter.normalize_payload(payload)
    if not incoming:
        return

    # Composite key: "tenant_id:user_id"
    buffer_key = incoming.user_id
    if tenant_id:
        buffer_key = f"{tenant_id}:{incoming.user_id}"
        incoming.metadata["tenant_id"] = str(tenant_id)
        incoming.metadata["real_user_id"] = incoming.user_id

    self.buffer_service.add_message(buffer_key, incoming.text, incoming.channel_type, incoming.metadata)
    background_tasks.add_task(self.smart_debounce_task, buffer_key, channel_adapter)
```

**Decisiones de diseno:**
- **Composite key `tenant_id:user_id`:** Previene colisiones entre tenants. Sin esto, dos tenants con un usuario que tenga el mismo Telegram ID se mezclarian.
- **Metadata injection:** `real_user_id` se guarda porque el `buffer_key` ya no es el user_id puro.
- **Background task por mensaje:** Cada mensaje lanza su propio debounce task. El mecanismo de "reset check" asegura que solo el ultimo sobrevive.

### Paso 1-7: smart_debounce_task (L105-201)

```
Mensaje 1 llega → background_task 1 inicia
  │
  ├─ [Step 1] sleep(0.5s) ← Buffer inicial
  │
  ├─ [Step 2] Reset Check: ¿last_ts es reciente?
  │     SI → return (abort: otro task se encarga)
  │     NO → continuar
  │
  ├─ [Step 3] set_typing_status() ← Feedback visual al usuario
  │
  ├─ [Step 3.5] Fetch tenant object (para LLM service resolution)
  │
  ├─ [Step 4] Semantic Check (LLM):
  │     peek_buffer() → join all texts
  │     check_is_complete(full_text) → "COMPLETO" o "INCOMPLETO"
  │
  ├─ [Step 5] Dynamic Wait:
  │     COMPLETO   → sleep(4.0s) ← Total ~4.5s
  │     INCOMPLETO → sleep(6.0s) ← Total ~6.5s
  │
  ├─ [Step 6] Final Reset Check + Lock:
  │     ¿Llego mensaje nuevo durante la espera?
  │       SI → return (abort)
  │       NO → acquire_lock()
  │             ¿Lock adquirido?
  │               NO → return (ya se esta procesando)
  │               SI → continuar
  │
  └─ [Step 7] Process:
        get_and_clear_buffer() → join all messages
        → process_chat_flow(channel_adapter, incoming, tenant_id)
        release_lock()
```

### Detalle del Reset Check (L113-117)
```python
last_ts = self.buffer_service.get_last_timestamp(buffer_key)
if time.time() - last_ts < 0.4:  # Tolerancia
    return  # Nuevo mensaje llego recientemente, abortar
```
- **Logica:** Si otro mensaje llego en los ultimos 0.4s, este task es "viejo" — el nuevo task se encargara.
- **Efecto cascada:** Cada nuevo mensaje crea un nuevo task que "mata" al anterior. Solo el task del ultimo mensaje sobrevive lo suficiente para procesar.

### Detalle del Semantic Check (L140-159)
```python
messages = self.buffer_service.peek_buffer(buffer_key)
full_text = " ".join(messages)

if len(full_text) > 5:
    is_complete = await check_is_complete(full_text, tenant=tenant_obj)

if is_complete:
    wait_time = 4.0   # Pensamiento completo → espera corta
else:
    wait_time = 6.0   # Pensamiento incompleto → espera larga
```
- **peek_buffer:** Lee SIN borrar — el buffer sigue acumulando.
- **Umbral de 5 chars:** Mensajes muy cortos ("ok", "si") no pasan por el LLM — se asume incompleto.
- **wait_time adaptativo:** Si el LLM dice "COMPLETO" (ej: "Hola, quiero saber el precio del curso"), espera menos. Si dice "INCOMPLETO" (ej: "Hola, quiero"), espera mas para que el usuario termine.

---

## 3. Semantic Completeness Check (LLM)

**Archivo:** `backend/src/modules/sales_agent/infrastructure/prompts/semantic.py` (L8-41)

```python
async def check_is_complete(text: str, tenant=None) -> bool:
    if not text or len(text.strip()) < 3:
        return False

    llm_service = LLMFactory.get_service_for_tenant(tenant) if tenant else LLMFactory.get_service()
    llm = llm_service.fast_chat_model

    sys_prompt = prompt_loader.render("message_completeness")

    response = await llm.ainvoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=f"Mensaje: {text}")
    ])

    content = response.content.strip().upper()
    return content == "COMPLETO"
```

### Template: message_completeness.j2
```
Eres un clasificador binario de intencion de escritura.
Determina si el mensaje del usuario esta 'COMPLETO' (tiene sentido semantico completo,
es una pregunta cerrada o una afirmacion final) o 'INCOMPLETO' (parece que el usuario
va a anadir mas detalles en un siguiente mensaje inmediatamente).
Responde SOLO con una palabra: 'COMPLETO' o 'INCOMPLETO'.
```

### Decisiones de Diseno
- **fast_chat_model:** Usa el modelo mas rapido (ej: GPT-4o-mini, Claude Haiku) para minimizar latencia.
- **Fail-safe a False:** Si el LLM falla, retorna `False` (incompleto) — mejor esperar de mas que responder a medias.
- **Tenant-aware LLM:** Si el tenant tiene un LLM service propio (ej: su propia API key), lo usa. Esto es parte de la estrategia multi-proveedor.

---

## 4. Tiempos del Pipeline Completo

```
t=0.0s   Mensaje llega
t=0.5s   Buffer check (si hay mensaje reciente, abort)
t=0.5s   Typing indicator
t=0.5-1s Semantic check (LLM call, ~500ms)
t=1.0s   Dynamic wait starts
t=5.0s   COMPLETO: Ready to process (0.5 + 4.0 + check time)
t=7.0s   INCOMPLETO: Ready to process (0.5 + 6.0 + check time)
t=7-15s  Agent processing (LLM calls)
t=15-20s Response sent (with typing simulation)
```

### Por que 4-6 segundos de espera?
- **Demasiado corto (< 2s):** Usuarios rapidos que escriben en multiples mensajes serian interrumpidos.
- **Demasiado largo (> 10s):** El usuario siente que el bot no funciona.
- **4-6s es el sweet spot:** Suficiente para que la mayoria de usuarios terminen de escribir, pero no tanto como para que se aburran.

---

## Casuisticas

### Que pasa si llegan 5 mensajes en 2 segundos?
1. Mensaje 1 → Task 1 inicia, sleep(0.5s)
2. Mensaje 2 → Task 2 inicia, sleep(0.5s). Msg 1 buffer updated.
3. Mensaje 3 → Task 3 inicia. Task 1 se da cuenta que `last_ts` es reciente → abort.
4. Mensaje 4 → Task 4 inicia. Task 2 abort.
5. Mensaje 5 → Task 5 inicia. Task 3 abort.
6. Solo Task 5 sobrevive y procesa los 5 mensajes juntos.

### Que pasa si Redis esta caido?
`SmartBufferService` lanzara una excepcion en `add_message()`. El error se propaga hasta el webhook handler, que retorna 500. Los canales externos (Meta, Telegram) re-intentaran.

### Que pasa si el LLM del semantic check falla?
`check_is_complete()` retorna `False` (fail-safe). Se aplica el wait largo (6s). El flujo continua normalmente.

### Que pasa si dos tasks adquieren el lock al mismo tiempo?
Imposible. `redis.set(key, value, nx=True)` es atomico. Solo uno obtiene True.

### El buffer per-tenant previene data leaks?
Si. El `buffer_key` es `"{tenant_id}:{user_id}"`. Incluso si dos tenants tienen un usuario con el mismo Telegram ID (improbable pero posible), sus buffers son completamente separados.
