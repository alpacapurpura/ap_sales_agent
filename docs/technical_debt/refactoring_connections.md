# Refactoring & Deuda Técnica: Módulo de Conexiones

> **ESTADO**: Propuesta de Mejora Técnica (RFC)
> **PRIORIDAD**: Alta (Seguridad) / Media (Estandarización)

Este documento detalla las inconsistencias y riesgos de seguridad encontrados en el módulo de conexiones (`src/modules/connections`), proponiendo una ruta de refactorización para unificar todas las integraciones bajo un estándar robusto.

## 1. Riesgos de Seguridad Críticos (Security Debt)

### Credenciales en Texto Plano
- **Problema**: Actualmente, los tokens de acceso, `client_secret` y API Keys se almacenan tal cual en el campo `credentials` (JSONB) de la tabla `channel_connections`. Si la base de datos es comprometida, todas las integraciones de los clientes quedan expuestas.
- **Evidencia**: Revisión de `channel_repository.py` no muestra uso de utilidades de encriptación al guardar.
- **Solución Propuesta**:
  1.  Integrar `backend/src/core/security.py` (Fernet) en el Repositorio.
  2.  Crear un script de migración para cifrar credenciales existentes.
  3.  Implementar getters/setters en el modelo `ChannelConnection` que descifren/cifren automáticamente al acceder a propiedades sensibles.

## 2. Inconsistencias de Arquitectura

### Fragmentación de Interfaces
- **Problema**:
  - WhatsApp implementa una interfaz rica (`WhatsAppProvider`) con manejo de estados y webhooks complejos.
  - Meta (Facebook/Instagram) usa una implementación ad-hoc (`MetaAdapter`) que no hereda de `BaseChannel` completamente, dificultando su uso en el orquestador de chat.
  - Shopify y Calendar siguen patrones disjuntos.
- **Solución Propuesta**:
  1.  Imponer el uso estricto de `BaseChannel` para **todo** canal que implique mensajería (incluyendo DM de Instagram/Messenger).
  2.  Imponer `BaseConnector` para integraciones de solo datos.
  3.  Refactorizar `MetaAdapter` para cumplir con `BaseChannel`, permitiendo que el Agente de Ventas responda DMs de Instagram igual que WhatsApp.

### Gestión de Webhooks Dispersa
- **Problema**: La lógica de validación de firmas (HMAC) y procesamiento de eventos está dispersa en cada router (`api/whatsapp.py`, `api/shopify.py`).
- **Solución Propuesta**:
  - Centralizar la validación de firmas en decoradores o dependencias de FastAPI (ej. `Depends(verify_shopify_signature)`).
  - Unificar el endpoint de entrada si es posible, o estandarizar la respuesta de los controladores.

## 3. Plan de Acción (Roadmap)

### Fase 1: Hardening de Seguridad (Inmediato)
- [ ] Implementar cifrado en `ChannelConnection.credentials`.
- [ ] Rotar claves de cifrado y re-cifrar datos.

### Fase 2: Unificación de Mensajería (Corto Plazo)
- [ ] Refactorizar `MetaAdapter` -> `InstagramChannel` (heredando de `BaseChannel`).
- [ ] Unificar el `ChatOrchestrator` para que acepte `ChannelType.META` de forma transparente.

### Fase 3: Estandarización de Datos (Medio Plazo)
- [ ] Mover `ShopifyConnector` y `GoogleCalendarAdapter` bajo la interfaz `BaseConnector`.
- [ ] Implementar `sync_frequency` configurable por tenant.

## 4. Referencias de Código para Refactor
- Cifrado: [`backend/src/core/security.py`](file:///home/chris/AISALESHT/backend/src/core/security.py)
- Interfaz Chat: [`backend/src/shared/infrastructure/channels/base.py`](file:///home/chris/AISALESHT/backend/src/shared/infrastructure/channels/base.py)
