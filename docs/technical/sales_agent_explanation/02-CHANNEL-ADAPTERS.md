# 02 — Channel Adapters (Patron Strategy)

## Vision General

El sistema usa el **Strategy Pattern** para desacoplar completamente la logica del Sales Agent de los canales de comunicacion. Cualquier canal externo implementa la misma interfaz (`BaseChannel`) y puede conectarse sin modificar el core.

```
                    ┌──────────────────┐
                    │   BaseChannel    │  (ABC)
                    │   base.py:5-31   │
                    ├──────────────────┤
                    │ normalize_payload│  Raw webhook → IncomingMessage
                    │ send_message     │  OutgoingMessage → API externa
                    │ set_typing_status│  "Escribiendo..." → Canal
                    └───────┬──────────┘
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌───────▼──────┐
   │ Telegram    │  │ WhatsApp    │  │ Instagram    │
   │ Channel     │  │ Channel     │  │ Channel      │
   │ (direct)    │  │ (facade)    │  │ (inherits    │
   │             │  │             │  │  MetaAdapter) │
   └─────────────┘  └──────┬──────┘  └──────────────┘
                           │
                    ┌──────▼──────┐
                    │ WhatsApp    │  (Strategy)
                    │ Provider    │
                    │ interface   │
                    ├─────────────┤
                    │  V1 (Evo 1) │
                    │  V2 (Evo 2) │
                    └─────────────┘

   ┌───────────────┐
   │ WebhookAdapter│  (No hereda BaseChannel — duck typing)
   │ (in-memory)   │
   └───────────────┘
```

---

## 1. Interfaz Base: BaseChannel

**Archivo:** `backend/src/shared/infrastructure/channels/base.py` (L5-31)

```python
class BaseChannel(ABC):
    """Abstract base class for channel adapters."""

    @abstractmethod
    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Convert raw webhook payload to unified IncomingMessage.
        Returns None if the payload should be ignored."""
        pass

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """Send unified OutgoingMessage to the specific channel API."""
        pass

    @abstractmethod
    async def set_typing_status(self, user_id: str) -> None:
        """Send 'typing...' status to the channel."""
        pass
```

### Decisiones de Diseno
- **`normalize_payload` retorna `Optional`:** Permite filtrar payloads irrelevantes (status updates, delivery receipts, edited messages) retornando `None`.
- **`send_message` es async:** Todos los envios a APIs externas son I/O-bound.
- **`set_typing_status` separado:** Permite al orchestrator enviar indicadores de "escribiendo" independientemente del envio de mensajes (se usa durante todo el procesamiento del agente).

---

## 2. Mensajes Unificados: IncomingMessage / OutgoingMessage

**Archivo:** `backend/src/shared/domain/messages.py` (L1-14)

```python
class IncomingMessage(BaseEntity):
    user_id: str         # ID del usuario en el canal (chat_id, sender_id, etc.)
    text: str            # Texto del mensaje
    channel_type: str    # "telegram", "whatsapp", "instagram", "api"
    metadata: Dict[str, Any] = {}  # first_name, last_name, username, source, etc.

class OutgoingMessage(BaseEntity):
    user_id: str
    text: str
    channel_type: Optional[str] = None
    metadata: Dict[str, Any] = {}
```

### Por que `user_id` es `str` y no `UUID`?
Porque cada canal tiene su propio formato de ID:
- **Telegram:** Numerico (`"123456789"`)
- **WhatsApp:** JID format (`"5215512345678@s.whatsapp.net"`)
- **Instagram:** Numerico largo (`"17841400000000"`)
- **API:** Arbitrario (lo define el llamador)

El mapeo a UUID interno (Lead ID) se hace en el `ChatOrchestrator`, no en el adapter.

---

## 3. TelegramChannel

**Archivo:** `backend/src/modules/connections/infrastructure/channels/telegram.py` (L10-122)

### Constructor (L16-23)
```python
class TelegramChannel(BaseChannel):
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
```
- **Multitenant:** Si se pasa un token, lo usa. Si no, fallback al token global del `.env`.
- **Inyeccion desde orchestrator:** `chat.py:72` crea `TelegramChannel(token=token)` despues de resolver la conexion del tenant.

### normalize_payload (L25-59)
```python
def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
    message = payload.get("message")
    if not message:
        return None  # Ignora edited_message, channel_post, etc.
    if "text" not in message:
        return None  # Ignora photos, stickers, etc.

    user_data = message.get("from", {})
    metadata = {
        "first_name": user_data.get("first_name", ""),
        "last_name": user_data.get("last_name", ""),
        "username": user_data.get("username", ""),
        "language_code": user_data.get("language_code", ""),
        "source": "telegram"
    }
    return IncomingMessage(user_id=str(user_data.get("id")), text=text, channel_type="telegram", metadata=metadata)
```
- **Metadata rica:** Extrae nombre, username y idioma del objeto `from` de Telegram. Esta metadata se usa para construir el perfil del cliente en el CRM.

### send_message con Markdown fallback (L61-99)
```python
async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
    payload = {"chat_id": message.user_id, "text": message.text, "parse_mode": "Markdown"}
    response = await client.post(url, json=payload, timeout=10.0)
    # Si falla con 400 (Markdown invalido), reintenta como plain text
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            payload.pop("parse_mode")
            retry_response = await client.post(url, json=payload, timeout=10.0)
```
- **Por que el retry?** El LLM a veces genera Markdown invalido para Telegram (ej: `*bold` sin cerrar). En vez de fallar silenciosamente, se reintenta sin formateo.

### set_typing_status (L101-122)
- Envia `sendChatAction` con `action: "typing"` a la API de Telegram.
- **Fire and forget:** Los errores se loguean pero no se propagan.

---

## 4. WhatsAppChannel (Facade + Strategy)

**Archivo principal:** `backend/src/modules/connections/infrastructure/channels/whatsapp/__init__.py` (L6-45)

### Facade Pattern
```python
class WhatsAppChannel(BaseChannel):
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.provider = get_whatsapp_provider(tenant_id)  # Factory

    def normalize_payload(self, payload):
        return self.provider.normalize_payload(payload)

    async def send_message(self, message):
        return await self.provider.send_message(message)
```

### WhatsAppProvider Interface
**Archivo:** `backend/src/modules/connections/infrastructure/channels/whatsapp/interface.py` (L5-62)

```python
class WhatsAppProvider(ABC):
    def __init__(self, tenant_id: str, base_url: str, api_key: str):
        self.tenant_id = tenant_id
        self.base_url = base_url
        self.headers = {"apikey": api_key, "Content-Type": "application/json"}

    @abstractmethod
    def normalize_payload(self, payload) -> Optional[IncomingMessage]: ...
    @abstractmethod
    async def send_message(self, message) -> Dict[str, Any]: ...
    @abstractmethod
    async def set_typing_status(self, user_id: str) -> None: ...
    # + create_instance, delete_instance, check_status, get_qr, configure_webhook, logout
```

### Por que Facade + Strategy?
WhatsApp usa **Evolution API**, que tiene dos versiones (V1 y V2) con payloads y endpoints diferentes. La `factory.py` decide cual usar basandose en la configuracion del tenant. El facade (`WhatsAppChannel`) oculta esta complejidad del resto del sistema.

### Implementaciones Concretas
- **V1:** `whatsapp/v1.py` — Evolution API v1 (payload con `data[0].key.remoteJid`)
- **V2:** `whatsapp/v2.py` — Evolution API v2 (payload diferente)

---

## 5. InstagramChannel

**Archivo:** `backend/src/modules/connections/infrastructure/channels/instagram.py` (L11-124)

### Herencia Multiple
```python
class InstagramChannel(MetaAdapter, BaseChannel):
    def __init__(self, client_config: Dict, credentials_data: Optional[Dict] = None):
        access_token = credentials_data.get("access_token") if credentials_data else None
        super().__init__(access_token=access_token)
```
- **MetaAdapter:** Hereda el manejo de OAuth/token de la clase base de Meta.
- **BaseChannel:** Cumple la interfaz unificada.

### normalize_payload (L28-71)
```python
def normalize_payload(self, payload):
    entries = payload.get("entry", [])
    entry = entries[0]
    messaging = entry.get("messaging", [])[0]
    sender_id = messaging.get("sender", {}).get("id")
    text = messaging.get("message", {}).get("text")

    return IncomingMessage(
        user_id=sender_id, text=text, channel_type="instagram",
        metadata={"message_id": ..., "recipient_id": ..., "is_echo": ...}
    )
```
- **Filtra non-text:** Si no hay `sender_id` o `text`, retorna `None`. Esto filtra likes, delivery receipts, etc.
- **is_echo:** Meta envia de vuelta los mensajes que tu enviaste (`is_echo: true`). Se guarda en metadata para referencia pero no se filtra aqui.

### send_message (L73-98)
- Usa la Graph API de Meta: `POST /{API_VERSION}/me/messages`
- **Bearer token:** Usa el `access_token` del page/asset (almacenado encriptado en `channel_connections.credentials`).

---

## 6. WebhookAdapter (In-Memory)

**Archivo:** `backend/src/modules/connections/infrastructure/channels/webhook.py` (L7-33)

```python
class WebhookAdapter:
    def __init__(self):
        self.responses: List[str] = []

    async def send_message(self, message: OutgoingMessage):
        self.responses.append(message.text)

    async def set_typing_status(self, user_id: str):
        logger.debug("webhook_adapter_typing", user_id=user_id)  # No-op

    def normalize_payload(self, payload: Any):
        pass  # No se usa (el mensaje se construye manualmente)
```

### Por que no hereda BaseChannel?
Porque se usa en el flujo sincrono de `webhook.py:37`, donde el mensaje se construye manualmente. No necesita `normalize_payload`. Funciona por **duck typing**: el `ChatOrchestrator` y `OutputManager` solo llaman `send_message()` y `set_typing_status()`, que estan implementados.

### Como funciona en el flujo sincrono
1. `webhook.py:75` crea `adapter = WebhookAdapter()`
2. `process_chat_flow()` genera respuesta y la pasa a `OutputManager`
3. `OutputManager` llama `adapter.send_message()` que acumula en `self.responses`
4. `webhook.py:87` hace `"\n\n".join(adapter.responses)` y lo retorna como HTTP response

---

## Casuisticas

### Que pasa si WhatsApp Evolution API esta caida?
`send_message()` lanza excepcion. El `OutputManager` la catchea, la loguea, y continua con los chunks restantes (`output_manager.py:56-60`).

### Que pasa si el token de Telegram es invalido?
`send_message()` falla con `httpx.HTTPStatusError`. Se loguea el error. El usuario no recibe respuesta, pero el mensaje se proceso y guardo en la BD.

### Que pasa si llega un sticker o foto por Telegram?
`normalize_payload()` retorna `None` porque `"text" not in message`. El orchestrator ignora el webhook completo.

### Se pueden agregar nuevos canales facilmente?
Si. Solo se necesita:
1. Crear una clase que implemente `BaseChannel` (o al menos `send_message`, `set_typing_status`, `normalize_payload`)
2. Crear un router FastAPI que reciba el webhook
3. Llamar `orchestrator._handle_incoming_webhook(adapter, payload, ...)` o `orchestrator.process_chat_flow(adapter, incoming, ...)`

No se modifica nada del core del sales agent.
