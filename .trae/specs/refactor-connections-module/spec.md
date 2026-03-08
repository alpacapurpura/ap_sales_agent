# Refactor Connections Module Spec

## Why
El módulo de conexiones actual presenta riesgos de seguridad críticos (credenciales en texto plano) e inconsistencias arquitectónicas (interfaces fragmentadas para canales de mensajería y conectores de datos). Esto dificulta el mantenimiento, la escalabilidad y la integración de nuevos canales como Instagram DM en el orquestador de chat unificado.

## What Changes
- **Seguridad**: Implementación de cifrado (Fernet) para el campo `credentials` en `ChannelConnectionModel`.
- **Arquitectura**:
  - Refactorización de `MetaAdapter` a `InstagramChannel` implementando la interfaz `BaseChannel`.
  - Integración de `InstagramChannel` en `ChatOrchestrator`.
  - Estandarización de `ShopifyConnector` y `GoogleCalendarAdapter` bajo la interfaz `BaseConnector`.
- **Webhooks**: Centralización de la validación de firmas y manejo de eventos.

## Impact
- **Affected specs**: Módulo de Conexiones, Orquestador de Chat.
- **Affected code**:
  - `backend/src/modules/connections/infrastructure/models/channel_model.py` (o Repository)
  - `backend/src/modules/connections/infrastructure/repositories/channel_repository.py`
  - `backend/src/modules/connections/infrastructure/channels/meta.py` -> `instagram.py`
  - `backend/src/modules/sales_agent/application/orchestrator/chat.py`
  - `backend/src/modules/connections/api/` (routers)

## ADDED Requirements
### Requirement: Encryption
El sistema DEBE cifrar el campo `credentials` antes de persistirlo en la base de datos y descifrarlo al leerlo, utilizando `src.core.security`.

#### Scenario: Guardar conexión
- **WHEN** se guarda o actualiza una conexión con credenciales
- **THEN** las credenciales se almacenan cifradas en la base de datos.

### Requirement: Instagram Channel
`InstagramChannel` DEBE implementar la interfaz `BaseChannel` (`send_message`, `normalize_payload`, etc.) para ser compatible con `ChatOrchestrator`.

## MODIFIED Requirements
### Requirement: Channel Connection
Se modifica el acceso a las credenciales para ser transparente al uso del cifrado.

### Requirement: Webhook Validation
La validación de firmas de webhooks (Shopify, Meta) DEBE realizarse mediante dependencias reutilizables de FastAPI.
