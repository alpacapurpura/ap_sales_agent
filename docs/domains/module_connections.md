# Módulo de Conexiones (Connections & Integrations) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este módulo es la **Bóveda de Credenciales** y el **Gateway de Comunicaciones** del sistema. Centraliza la autenticación y el intercambio de datos con *cualquier* plataforma externa (Mensajería, CRM, E-commerce, Calendarios). Su misión es abstraer la complejidad de APIs de terceros (OAuth2, Webhooks, Firmas) y exponer una interfaz unificada al resto del sistema.

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos que pueden estar desactualizados.

- **Backend**: `backend/src/modules/connections/`
  - Dominio (entidad unificada para todas las integraciones, enums de tipo): `domain/`
  - Adaptadores de mensajería (WhatsApp, Meta, etc.): `infrastructure/channels/`
  - Conectores de datos (Shopify, MailerLite, etc.): `infrastructure/marketing_connectors/`
  - Interfaces base (contratos): `backend/src/shared/infrastructure/channels/`
  - Endpoints segregados por proveedor: `api/`
- **Frontend**: `frontend/src/features/growth-studio/`
  - Vista hub de integraciones y tarjetas de conexión: `components/`

## 2. Lógica de Negocio (The "Why" & "How")

### Patrón Adapter/Strategy (Estándar de Oro)
Para evitar "spaghetti code" con `if type == 'whatsapp'`, el sistema usa polimorfismo estricto.
- **Mensajería (`BaseChannel`)**: Todo canal de chat debe implementar:
  - `send_message(payload)`: Transformar mensaje interno -> API Externa.
  - `normalize_payload(webhook_data)`: Webhook Externo -> `IncomingMessage` interno.
- **Datos (`BaseConnector`)**: Todo conector de datos debe implementar:
  - `sync_contacts()`: Traer usuarios externos a `Lead`.
  - `verify_credentials()`: Validar tokens antes de guardar.

### Autenticación y Seguridad
El módulo maneja dos tipos de auth:
1.  **OAuth2 (Meta, Google)**:
    - El usuario es redirigido al proveedor.
    - El callback recibe `code`, canjea por `access_token` y `refresh_token`.
    - El sistema se encarga de refrescar tokens automáticamente (TODO: Implementar worker de refresh).
2.  **API Key / Token (Shopify, Evolution)**:
    - El usuario pega credenciales o escanea QR.
    - Se validan inmediatamente contra la API externa (`verify_credentials`).

**Regla de Seguridad**: Las credenciales se guardan en el campo `credentials` (JSONB).
*   **DEUDA TÉCNICA**: Actualmente en texto plano. Se requiere migrar a cifrado Fernet (`core/security.py`) para `access_token` y `client_secret`.

### Flujos Específicos
- **WhatsApp (Evolution)**: Complejo. Requiere crear instancia -> obtener QR -> configurar webhook. Tiene "Auto-Healing" para sesiones zombis.
- **Shopify**: Simple. Valida URL de tienda + Access Token de Admin API. Sincroniza productos y clientes.
- **Google Calendar**: Usa Service Account o OAuth2 para leer disponibilidad (Free/Busy) y crear eventos de Google Meet.

## 3. Casos Borde y Gotchas (Edge Cases)

- **Desconexión Silenciosa (OAuth2)**: El usuario puede revocar permisos en la configuración de Google/Facebook. El sistema solo se entera al fallar una petición.
  - *Solución*: Capturar errores 401/403 y marcar `is_active=False` en DB automáticamente.
- **Webhooks Concurrentes**: Plataformas como Shopify o Meta envían múltiples eventos simultáneos (ej. `product.update`). El endpoint debe ser idempotente y responder 200 OK rápido (background tasks).
- **Rate Limits**: Las APIs de Meta y Shopify tienen límites estrictos. Los adaptadores deben manejar `429 Too Many Requests` con *Exponential Backoff*.

## 4. Snippets para Agentes (Common Tasks)

### Cómo implementar una nueva conexión (Ej. Slack)
1.  Crear `infrastructure/channels/slack.py` heredando de `BaseChannel`.
2.  Implementar `send_message` (usando `slack_sdk`).
3.  Implementar `normalize_payload` (para eventos de Slack Events API).
4.  Registrar en `ChannelType` (enums.py) y en el `ChannelFactory`.

### Cómo verificar credenciales antes de usar
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# channel_service.py pattern
async def get_valid_connection(tenant_id: str, type: ChannelType):
    conn = await repo.get_connection(tenant_id, type)
    if not conn or not conn.is_active:
        raise InactiveConnectionError()
    
    # Para OAuth2, verificar expiración y refrescar si es necesario
    if type in [ChannelType.META, ChannelType.GOOGLE]:
        if conn.credentials.get('expires_at') < now():
            conn = await auth_service.refresh_token(conn)
            
    return conn
```
