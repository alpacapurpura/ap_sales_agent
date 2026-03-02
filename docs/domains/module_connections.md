---
module: "Integration & Channels"
status: "active"
core_files:

api_routes:
  - "GET /api/v1/whatsapp/status"
  - "POST /api/v1/whatsapp/session"
  - "GET /api/v1/whatsapp/qr"
  - "POST /api/v1/webhooks/whatsapp"
---

## 1. Propósito del Negocio (El "Por Qué")
Actuar como la bóveda central (Credential Vault) para todas las conexiones con el mundo exterior (WhatsApp, Telegram, Shopify, Google Calendar, Meta). Este módulo actúa como el **Gateway de Comunicaciones** del sistema, centralizando la conexión con proveedores externos (WhatsApp Evolution/Meta, Telegram, Gmail). Su objetivo principal es abstraer la complejidad técnica de cada API de terceros, proporcionando una interfaz unificada para el envío y recepción de mensajes. Gestiona el ciclo de vida de las conexiones (autenticación QR, renovación de tokens), la normalización de payloads entrantes (webhooks) y la "auto-curación" de estados inconsistentes entre la base de datos local y el proveedor externo.

## 2. Reglas de Negocio Estrictas (Business Rules)
- Agnóstico de Negocio: No sabe qué es un "Lead" ni qué es una "Cita". Solo sabe manejar OAuth2, Webhooks puros, refrescar tokens vencidos y devolver credenciales.
- Seguridad Absoluta: Las API Keys y Access Tokens DEBEN estar obligatoriamente encriptadas en la base de datos (usando Fernet u otro cifrado fuerte).
- El Llavero del Sistema: Los demás dominios (sales_agent, scheduling, social_media) deben consultar a este módulo para obtener los tokens desencriptados en tiempo de ejecución.

### Gestión de Conexiones (WhatsApp)
- **Unicidad por Tenant:** Cada instancia de conexión (WhatsApp Session) pertenece estrictamente a un único `tenant_id`. No se comparten sesiones entre clientes.
- **Prioridad de Proveedor:** El sistema soporta simultáneamente "Evolution API" (QR) y "Meta Cloud API", pero la UI advierte explícitamente contra tener ambos activos para evitar respuestas duplicadas.
- **Limpieza de Zombis (Zombie Cleanup):** Antes de crear una nueva sesión de WhatsApp, el sistema verifica obligatoriamente si ya existe una instancia en el proveedor. Si existe, la elimina y espera 5 segundos antes de crear la nueva, evitando conflictos de puertos o sesiones colgadas.
- **Configuración Automática de Webhook:** Al crear una sesión exitosa en Evolution API, el sistema configura *automáticamente* el webhook de retorno (`/api/v1/whatsapp/webhook/{tenant_id}`) en el proveedor.

### Sincronización de Estado (Auto-Healing)
- **Recuperación de Metadatos:** Si la base de datos local marca una conexión como activa pero sin metadatos (nombre, foto, número), y el proveedor confirma que la sesión está "open", el endpoint de estado (`/status`) actualiza automáticamente la base de datos local con la información del perfil obtenida del proveedor.
- **Persistencia de Configuración:** Las credenciales y metadatos se almacenan en el campo JSONB `config` del modelo `ChannelConnection`.

### Seguridad
- **Verificación de Webhooks:**
    - **Meta:** Requiere validación estricta de `hub.verify_token` y `hub.challenge`.
    - **Evolution:** La seguridad se basa en la URL única por Tenant y la gestión interna del API Key del servicio.

## 3. Mapa de Código (The "Where")

- Backend: backend/src/modules/connections/
- Frontend: frontend/src/features/connections/ (Pantalla de "Conexiones" del usuario).


## 4. Casos Borde Conocidos (Edge Cases)

- **Instancia "Crashed" en QR:** El frontend detecta explícitamente el estado `crashed` durante la generación del QR y detiene el polling, notificando al usuario en lugar de intentar infinitamente.
- **Falso Positivo de Desconexión:** Si la base de datos local dice "desconectado" pero el proveedor dice "conectado" (ej. tras un reinicio de DB), el sistema se "auto-cura" al consultar el estado, reactivando la conexión localmente sin requerir nuevo escaneo QR.
- **Formato de QR Variable:** El adaptador maneja inconsistencias en la respuesta de Evolution API, extrayendo el base64 ya sea de `data.code`, `data.base64` o estructuras anidadas `data.qrcode.base64`.
- **Race Condition en Polling:** El hook `useWhatsApp` implementa referencias (`useRef`) para cancelar el polling inmediatamente si se detecta conexión exitosa, evitando llamadas redundantes al backend.
