# 01 — Entry Points (Webhooks y Endpoints)

## Vision General

El Sales Agent recibe mensajes de 4 canales distintos, cada uno con su propio mecanismo de autenticacion y webhook. Todos los webhooks convergen en el `ChatOrchestrator`, que es un **Singleton** (`chat.py:36-42`).

```
  Telegram Bot API ─────► /webhooks/telegram           ─► handle_telegram_webhook()
  Telegram Bot API ─────► /webhooks/telegram/{tenant}   ─► handle_telegram_webhook(tenant_id)
  WhatsApp Evolution ───► /webhooks/whatsapp             ─► handle_whatsapp_webhook()
  WhatsApp Evolution ───► /whatsapp/webhook/{tenant}     ─► _handle_incoming_webhook()
  Meta (IG/FB) ─────────► /connections/meta/webhook      ─► process_chat_flow() (directo)
  API Generica ─────────► /connections/webhook/chat      ─► process_chat_flow() (sincrono)
```

---

## 1. Telegram

**Archivo:** `backend/src/modules/connections/api/telegram.py`
**Montado en:** `/api/v1/connections/telegram` (`main.py:158`)

### Webhook Legacy (L18-25)
```python
@router.post("/webhooks/telegram")
async def telegram_webhook_legacy(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    await orchestrator.handle_telegram_webhook(payload, background_tasks)
    return {"status": "ok"}
```
- **Ruta completa:** `POST /api/v1/connections/telegram/webhooks/telegram`
- **Autenticacion:** Ninguna (la seguridad depende de que Telegram solo envie al URL configurado)
- **Tenant resolution:** Usa `settings.TELEGRAM_BOT_TOKEN` (variable global, un solo bot)

### Webhook Multitenant (L27-39)
```python
@router.post("/webhooks/telegram/{tenant_id}")
async def telegram_webhook_tenant(tenant_id: str, request: Request, ...):
    payload = await request.json()
    await orchestrator.handle_telegram_webhook(payload, background_tasks, tenant_id=tenant_id, db=db)
    return {"status": "ok"}
```
- **Ruta completa:** `POST /api/v1/connections/telegram/webhooks/telegram/{tenant_id}`
- **Tenant resolution:** El `tenant_id` viene en la URL. El orchestrator busca el bot token en `channel_connections` (`chat.py:56-69`).

### Por que dos webhooks?
El legacy existe para compatibilidad con la configuracion inicial (un solo bot). El multitenant permite que cada tenant tenga su propio bot de Telegram con su propio token, almacenado encriptado en la tabla `channel_connections`.

---

## 2. WhatsApp

**Archivo:** `backend/src/modules/connections/api/whatsapp.py`
**Montado en:** `/api/v1/connections/whatsapp` (`main.py:157`)

### Verificacion Meta (L27-35)
```python
@router.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(challenge)
```
- **Proposito:** Meta requiere un GET de verificacion antes de activar un webhook. Se valida contra `WHATSAPP_VERIFY_TOKEN` del `.env`.

### Webhook Global (L38-42)
```python
@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    await orchestrator.handle_whatsapp_webhook(payload, background_tasks)
    return {"status": "received"}
```
- **Nota:** `handle_whatsapp_webhook()` esta marcado como deprecated (`chat.py:75-78`) — solo tiene `pass`.

### Webhook Per-Tenant (L214-230)
```python
@router.post("/whatsapp/webhook/{tenant_id}")
async def handle_whatsapp_webhook(tenant_id: str, payload: dict = Body(...), ...):
    orch = ChatOrchestrator()
    adapter = WhatsAppChannel(tenant_id=tenant_id)
    background_tasks.add_task(orch._handle_incoming_webhook, adapter, payload, None, tenant_id)
    return {"status": "ok"}
```
- **Ruta completa:** `POST /api/v1/connections/whatsapp/whatsapp/webhook/{tenant_id}`
- **Flujo:** Crea un `WhatsAppChannel` con el tenant_id (que resuelve a Evolution API V1 o V2), y delega directamente a `_handle_incoming_webhook` como background task.
- **Por que background task?** Para responder 200 OK inmediatamente a Meta/Evolution y evitar timeouts.

---

## 3. Meta (Instagram / Facebook)

**Archivo:** `backend/src/modules/connections/api/meta.py`
**Montado en:** `/api/v1/connections/meta` (`main.py:167`)

### Verificacion Meta (L42-53)
```python
@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
):
    verify_token = settings.META_VERIFY_TOKEN
    if mode == "subscribe" and token == verify_token:
        return int(challenge)
```
- **Identico** al patron de WhatsApp, requerido por Meta Platform.

### Webhook con Signature Verification (L56-106)
```python
@router.post("/webhook")
async def webhook_event(
    payload: dict = Body(...),
    verified: bool = Depends(verify_meta_signature),  # ← HMAC
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
```
- **Seguridad:** `verify_meta_signature` (`webhook_security.py:40-72`) verifica HMAC-SHA256 con `META_APP_SECRET`.
- **Tenant resolution por asset_id:** Busca en `channel_connections` todas las conexiones activas de tipo `facebook_page`, `instagram_account`, `meta`, o `instagram`, y hace match por `config.asset_id == account_id` del payload (L69-83).
- **Procesamiento directo:** No usa buffer/debounce. Llama directamente a `process_chat_flow()` (L102).
- **Por que directo?** Instagram DM ya viene como mensajes individuales bien formados, y Meta tiene timeout estricto en webhooks. El debounce no aporta valor aqui.

---

## 4. API Generica (Webhook Sincrono)

**Archivo:** `backend/src/modules/connections/api/webhook.py`
**Montado en:** `/api/v1/connections/webhook` (`main.py:159`)

### Autenticacion por X-Webhook-Secret (L16-35)
```python
def get_tenant_by_secret(
    x_webhook_secret: str = Header(..., alias="X-Webhook-Secret"),
    db: Session = Depends(get_db)
) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.webhook_secret == x_webhook_secret).first()
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid Webhook Secret")
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive")
    set_tenant_id(tenant.id)
    return tenant
```
- **Patron:** Cada tenant tiene un `webhook_secret` unico en la tabla `tenants`. El llamador envia ese secret en el header.
- **Tenant context:** Se setea via `set_tenant_id()` antes de procesar.

### Endpoint Chat (L37-99)
```python
@router.post("/chat")
async def webhook_chat(payload: dict = Body(...), tenant: Tenant = Depends(get_tenant_by_secret)):
    incoming = IncomingMessage(user_id=str(user_id), text=str(message_text), channel_type="api", ...)
    adapter = WebhookAdapter()
    await orchestrator.process_chat_flow(adapter, incoming)
    full_response = "\n\n".join(adapter.responses)
    return {"response": full_response, ...}
```
- **Sincrono:** A diferencia de los otros canales, este endpoint **espera** la respuesta completa y la retorna en el HTTP response.
- **WebhookAdapter:** Colecciona las respuestas en memoria (`adapter.responses`) en vez de enviarlas a un canal externo.
- **No usa buffer/debounce:** Es una llamada directa request-response.
- **channel_type = "api":** Se distingue de los otros canales para el tracking.

---

## 5. Verificacion de Seguridad (HMAC)

**Archivo:** `backend/src/modules/connections/api/dependencies/webhook_security.py`

### verify_meta_signature (L40-72)
```python
async def verify_meta_signature(request: Request):
    signature_header = request.headers.get("X-Hub-Signature-256")
    # Formato: sha256=<signature>
    signature = signature_header.split("=")[1]
    body = await request.body()
    digest = hmac.new(settings.META_APP_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")
```
- **Algoritmo:** HMAC-SHA256 usando `META_APP_SECRET` como clave.
- **Timing-safe:** Usa `hmac.compare_digest()` para prevenir timing attacks.

### verify_shopify_signature (L10-38)
- Similar pero usa Base64 encoding y `SHOPIFY_API_SECRET`.
- Usado en webhooks de Shopify (no del sales agent, pero en el mismo modulo de seguridad).

---

## 6. Router Mounting

**Archivo:** `backend/src/main.py` (L154-168)

```python
# 12. Connections
app.include_router(conn_whatsapp.router,  prefix="/api/v1/connections/whatsapp",  tags=["Connections - WhatsApp"])
app.include_router(conn_telegram.router,  prefix="/api/v1/connections/telegram",  tags=["Connections - Telegram"])
app.include_router(conn_webhook.router,   prefix="/api/v1/connections/webhook",   tags=["Connections - Webhook"])
app.include_router(conn_meta.router,      prefix="/api/v1/connections/meta",      tags=["Connections - Meta"])
```

**Nota importante:** Los routers de WhatsApp, Telegram, Webhook y Meta **no tienen** `Depends(get_tenant_context)` a nivel de router. Esto es intencional: los webhooks son llamados por servicios externos que no tienen Clerk auth. La autenticacion se maneja de forma especifica por canal:
- **Telegram:** Sin auth (seguridad por URL secreto)
- **WhatsApp:** Verificacion de token o tenant_id en URL
- **Meta:** HMAC signature verification
- **API Webhook:** X-Webhook-Secret header

---

## Casuisticas

### Que pasa si el payload de Telegram no tiene "message"?
`TelegramChannel.normalize_payload()` retorna `None` (`telegram.py:33-35`). El orchestrator ignora el webhook (`chat.py:81-83`). Esto filtra updates de tipo `edited_message`, `channel_post`, etc.

### Que pasa si la firma HMAC de Meta es invalida?
`verify_meta_signature` lanza `HTTPException(401)` antes de que el payload llegue al handler. El webhook devuelve 401 y Meta re-intentara.

### Que pasa si el X-Webhook-Secret no corresponde a ningun tenant?
`get_tenant_by_secret` lanza `HTTPException(401)`. Si el tenant existe pero esta inactivo, lanza `HTTPException(403)`.

### Que pasa si llega un webhook de WhatsApp para un tenant sin conexion configurada?
El `WhatsAppChannel(tenant_id)` se crea igual pero usara las credenciales del `.env` global como fallback. Si no hay credenciales, el envio de respuesta fallara pero el mensaje se procesa.
