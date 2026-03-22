# 09 — Output & Response

## Vision General

El `OutputManager` simula el comportamiento de un vendedor humano al enviar respuestas: divide la respuesta en chunks, calcula un tiempo de escritura realista, muestra "Escribiendo...", y envia cada chunk con pausas cognitivas entre ellos.

```
Bot text: "¡Hola! Me alegra que te interese.\n\nNuestro programa tiene 3 módulos..."
    │
    ▼
OutputManager.process_response()
    │
    ├── [Chunk 1] "¡Hola! Me alegra que te interese."
    │     ├── set_typing_status()
    │     ├── sleep(1.5s)  ← typing time
    │     ├── send_message()
    │     └── sleep(0.6s)  ← cognitive pause
    │
    └── [Chunk 2] "Nuestro programa tiene 3 módulos..."
          ├── set_typing_status()
          ├── sleep(2.3s)  ← typing time
          └── send_message()
```

---

## 1. OutputManager

**Archivo:** `backend/src/modules/sales_agent/infrastructure/external/output_manager.py` (L11-106)

### Constantes de Simulacion (L17-22)

```python
class OutputManager:
    CPM_SPEED = 320           # Characters per minute (High Ticket: 300-350)
    JITTER_RANGE = (0.8, 1.2) # Variability factor
    MIN_TYPING_TIME = 1.5     # Minimum "typing..." duration
    MAX_TYPING_TIME = 6.0     # Cap to avoid awkward silences
    MICRO_DELAY_RANGE = (0.4, 0.8)  # Pause between chunks
```

**Por que 320 CPM?** Es el estándar de "High Ticket Sales" — ni demasiado rapido (parece bot) ni demasiado lento (parece desinteresado). Es la velocidad promedio de escritura en movil de un profesional.

### process_response (L24-66)

```python
@classmethod
async def process_response(cls, user_id: str, raw_response: str, channel_adapter):
    chunks = cls._parse_response(raw_response)

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue

        # 1. Calculate typing time
        typing_time = cls._calculate_typing_time(chunk)

        # 2. Show typing indicator
        if hasattr(channel_adapter, "set_typing_status"):
            await channel_adapter.set_typing_status(user_id)

        # 3. Wait (simulate typing)
        await asyncio.sleep(typing_time)

        # 4. Send message
        outgoing = OutgoingMessage(user_id=user_id, text=chunk)
        try:
            await channel_adapter.send_message(outgoing)
        except Exception as e:
            logger.error("error_sending_chunk", user_id=user_id, error=str(e))

        # 5. Cognitive pause (between chunks, not after last)
        if i < len(chunks) - 1:
            pause = random.uniform(*cls.MICRO_DELAY_RANGE)
            await asyncio.sleep(pause)
```

### _parse_response (L68-89)

```python
@classmethod
def _parse_response(cls, raw_response: str) -> List[str]:
    cleaned = raw_response.strip()

    # Remove markdown code blocks (LLM artifact)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE)

    # Try JSON array first
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
    except json.JSONDecodeError:
        pass

    # Fallback: single chunk
    return [raw_response]
```

**Dos modos de chunking:**
1. **JSON array:** Si el LLM devuelve `["Chunk 1", "Chunk 2", "Chunk 3"]`, cada elemento es un chunk separado. Esto es el patron "Triad" de High Ticket sales (3 mensajes cortos en vez de 1 largo).
2. **Single chunk:** Si no es JSON, se envia como un solo mensaje.

**Nota:** Actualmente los specialist prompts no instruyen al LLM a devolver JSON arrays, asi que la mayoria de respuestas van como single chunk. El soporte JSON esta preparado para cuando se active.

### _calculate_typing_time (L92-105)

```python
@classmethod
def _calculate_typing_time(cls, text: str) -> float:
    length = len(text)
    base_seconds = (length / cls.CPM_SPEED) * 60   # CPM → seconds
    jitter = random.uniform(*cls.JITTER_RANGE)       # 0.8x to 1.2x
    final_time = base_seconds * jitter
    return max(cls.MIN_TYPING_TIME, min(final_time, cls.MAX_TYPING_TIME))
```

**Ejemplos:**
| Texto | Chars | Base (s) | Con Jitter | Clamped |
|-------|-------|----------|------------|---------|
| "Hola!" | 6 | 1.13 | 0.9-1.35 | **1.5** (min) |
| "Entiendo tu preocupacion..." | 30 | 5.63 | 4.5-6.75 | 4.5-**6.0** (max) |
| "Nuestro programa incluye..." | 120 | 22.5 | 18-27 | **6.0** (max) |

---

## 2. Envio por Canal

### Telegram (`telegram.py:61-99`)
```python
async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": message.user_id, "text": message.text, "parse_mode": "Markdown"}

    response = await client.post(url, json=payload, timeout=10.0)
    # Si 400 → retry sin Markdown
```

### Instagram (`instagram.py:73-98`)
```python
async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
    url = f"{self.BASE_URL}/{self.API_VERSION}/me/messages"
    data = {"recipient": {"id": message.user_id}, "message": {"text": message.text}}
    headers = {"Authorization": f"Bearer {self.access_token}"}

    response = await client.post(url, json=data, headers=headers)
```

### WhatsApp (via Evolution API)
```python
# V1/V2 implementations vary, but the pattern is:
async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
    url = f"{self.base_url}/message/sendText/{self.tenant_id}"
    payload = {"number": message.user_id, "text": message.text}
    response = await client.post(url, json=payload, headers=self.headers)
```

### WebhookAdapter (in-memory, `webhook.py:15-20`)
```python
async def send_message(self, message: OutgoingMessage):
    self.responses.append(message.text)  # Collect for HTTP response
```

---

## 3. Typing Status por Canal

| Canal | Metodo API | Endpoint | Duracion |
|-------|-----------|----------|----------|
| Telegram | `sendChatAction` | `/bot{token}/sendChatAction` | ~5s (auto-expire) |
| Instagram | Sender Action | `/me/messages` con `sender_action: typing_on` | ~20s |
| WhatsApp | Presence update | Evolution API presence endpoint | Variable |
| Webhook/API | No-op | (log only) | N/A |

**Nota:** Los indicadores de typing expiran automaticamente en la mayoria de plataformas. Por eso el orchestrator los reenvia cada 3 segundos durante el procesamiento del agente (`chat.py:417-423`).

---

## 4. Flujo Completo de Output

```
agent_app.ainvoke(state)
        │
        ▼  result["messages"][-1]["content"]
"¡Hola María! 😊 Me encanta que te interese nuestro programa..."
        │
        ▼
audit_repo.log_message(role="assistant")  ← Persistencia
        │
        ▼
OutputManager.process_response(user_id, bot_text, channel_adapter)
        │
        ├─ _parse_response():
        │   Try JSON array → fail → single chunk
        │
        ├─ For chunk "¡Hola María! 😊 Me encanta que te interese...":
        │   ├─ _calculate_typing_time("¡Hola María!...") → 3.2s
        │   ├─ channel_adapter.set_typing_status(user_id)
        │   ├─ asyncio.sleep(3.2)
        │   └─ channel_adapter.send_message(OutgoingMessage(user_id, chunk))
        │
        └─ Done
```

---

## Casuisticas

### Que pasa si el envio de un chunk falla?
Se loguea el error y se **continua** con el siguiente chunk (`output_manager.py:56-60`). La decision es no abortar todo porque podria ser un error transitorio, y es mejor enviar una respuesta parcial que ninguna.

### Que pasa si la respuesta del LLM esta vacia?
`_parse_response("")` retorna `[""]`. El loop en `process_response` skipea chunks vacios (`if not chunk.strip(): continue`). Nada se envia.

### El usuario puede notar que es un bot por la velocidad?
El jitter (0.8x-1.2x) y el clamp (1.5-6.0s) hacen que la velocidad varie naturalmente. Es indistinguible de un humano rapido escribiendo en movil. El micro-delay entre chunks simula la "pausa para pensar" que tiene un humano entre mensajes.

### El WebhookAdapter tambien simula typing delays?
Si. `process_response()` ejecuta `asyncio.sleep()` aunque sea un WebhookAdapter. El `set_typing_status()` es no-op, pero los delays siguen activos. Esto significa que la API sincrona tiene latencia artificial. Un TODO potencial es desactivar delays para `channel_type="api"`.

### Que pasa si el LLM devuelve un JSON array?
```json
["¡Hola María! 😊", "Me alegra que te interese.", "¿Me cuentas un poco sobre ti?"]
```
Se envia como 3 mensajes separados con typing simulation entre cada uno. Esto es el patron "Triad" de ventas High Ticket: mensajes cortos y conversacionales.
