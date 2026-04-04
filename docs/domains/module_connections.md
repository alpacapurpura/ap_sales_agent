---
module: Connections
status: active
---

# Connections

Boveda de credenciales y gateway de comunicaciones. Abstrae la autenticacion y el intercambio de datos con plataformas externas (mensajeria, e-commerce, analytics, calendario).

## Domain Concepts

- **ChannelConnection**: Entidad unificada — almacena `credentials` (JSONB) y `config` (JSONB) para cualquier tipo de canal.
- **ChannelType**: Enum con 17 tipos actualmente: Telegram, WhatsApp (Evolution), WhatsApp Cloud, ManyChat, Shopify, MailerLite, Google Analytics, Meta (master), Facebook Page, Instagram Account, Meta Ads Account, Meta Pixel, WhatsApp Business Account, YouTube, YouTube Analytics, Google Calendar, Gmail.

## Architecture Decisions

- **Adapter/Strategy**: `BaseChannel` (interfaz en `shared/`) fuerza polimorfismo para evitar `if type == 'whatsapp'`. Implementaciones en `infrastructure/channels/` (~13 adaptadores). Marketing connectors (`infrastructure/marketing_connectors/`) siguen patron similar con `BaseConnector`.
- **BaseChannel tiene 3 metodos abstractos**: `normalize_payload(webhook_data)` -> `IncomingMessage`, `send_message(OutgoingMessage)`, `set_typing_status(user_id)`.

## Business Rules

- Webhooks de plataformas externas (Shopify, Meta) deben ser idempotentes y responder 200 OK rapido (delegar a background tasks).
- Para OAuth2, capturar errores 401/403 y marcar `is_active=False` automaticamente (desconexion silenciosa).
- Rate limits de Meta y Shopify requieren Exponential Backoff en los adaptadores.

## Edge Cases

- **WhatsApp Evolution**: Flujo complejo (crear instancia -> QR -> configurar webhook). Tiene auto-healing para sesiones zombis.
- **Desconexion silenciosa OAuth2**: El usuario puede revocar permisos en Google/Facebook sin notificar al sistema — solo se detecta al fallar una peticion.
- **Token refresh**: Existe como TODO — no hay worker automatico de refresh de OAuth tokens aun.

## CRITICAL — Do Not Violate

- **Credentials en texto plano**: Deuda tecnica activa. El campo `credentials` JSONB NO esta cifrado. No exponer en responses sin response_model explicito.
- Al agregar un nuevo canal: crear adaptador en `infrastructure/channels/`, agregar valor en `ChannelType` enum, registrar en `ChannelFactory`.
