# Refactoring & Deuda Tecnica: Modulo de Conexiones

> **ESTADO**: Resuelto (2026-03-09)
> **PRIORIDAD**: ~~Alta (Seguridad) / Media (Estandarizacion)~~ Completado

Este documento detalla las inconsistencias y riesgos de seguridad que fueron encontrados en el modulo de conexiones (`src/modules/connections`), y su resolucion.

## 1. Riesgos de Seguridad Criticos (Security Debt)

### Credenciales en Texto Plano
- **Problema original**: Los tokens de acceso, `client_secret` y API Keys se almacenaban en texto plano en el campo `credentials` (JSONB).
- **Estado**: RESUELTO
- **Solucion implementada**:
  1. Se creo `EncryptedJSON` TypeDecorator en `shared/infrastructure/database/types.py` que cifra/descifra automaticamente con Fernet.
  2. `ChannelConnectionModel.credentials` usa `EncryptedJSON` en vez de `JSONB`.
  3. Los datos se almacenan como `{"_encrypted": "..."}` en la BD, con soporte para datos legacy sin cifrar.
  4. Tests en `tests/modules/connections/test_channel_security.py` verifican cifrado y backward compatibility.

## 2. Inconsistencias de Arquitectura

### Fragmentacion de Interfaces
- **Problema original**: WhatsApp, Meta, Shopify y Calendar seguian patrones disjuntos.
- **Estado**: RESUELTO
- **Solucion implementada**:
  1. `InstagramChannel` hereda de `MetaAdapter` + `BaseChannel` para mensajeria unificada.
  2. `BaseConnector` define la interfaz para integraciones de solo datos (Shopify, Mailerlite, ManyChat).
  3. Todos los canales de mensajeria implementan `BaseChannel` con `normalize_payload()`, `send_message()`, `set_typing_status()`.

### Gestion de Webhooks Dispersa
- **Problema original**: Validacion HMAC dispersa en cada router.
- **Estado**: RESUELTO
- **Solucion implementada**:
  1. `api/dependencies/webhook_security.py` centraliza `verify_shopify_signature` y `verify_meta_signature` como `Depends()`.
  2. Los routers importan estas dependencias en vez de implementar su propia validacion.

### Modelo ORM en Modulo Incorrecto
- **Problema**: `ChannelConnectionModel` estaba en `sales_agent/infrastructure/models/` en vez de `connections/`.
- **Estado**: RESUELTO
- **Solucion implementada**:
  1. Modelo canonico en `connections/infrastructure/models/channel_connection_model.py`.
  2. Re-export en `sales_agent/infrastructure/models/channel_model.py` para backward compatibility.

### Routers con Acceso Directo a DB
- **Problema**: Todos los routers hacian `db.query(ChannelConnectionModel)` directo sin repositorio, duplicando logica de queries.
- **Estado**: RESUELTO
- **Solucion implementada**:
  1. `ChannelConnectionRepository` en `connections/infrastructure/repositories/` con metodos: `get_active()`, `get_by_tenant_and_type()`, `get_all_active_by_type()`, `get_all_by_tenant()`, `upsert()`, `update_config()`, `update_credentials()`, `deactivate()`, `activate()`.
  2. Todos los routers refactorizados para usar el repositorio via `Depends()`.
  3. SQLAlchemy 2.0 syntax (`select()` en vez de `.query()`).

### Bug: whatsapp.py Usando Modelo de Dominio para Queries ORM
- **Problema**: `whatsapp.py` importaba `ChannelConnection` (Pydantic) y lo usaba con `db.query()`.
- **Estado**: RESUELTO
- **Solucion**: Refactorizado para usar `ChannelConnectionRepository`.

### Hard Deletes en Disconnect
- **Problema**: Algunos routers hacian `db.delete(connection)` en vez de soft-delete.
- **Estado**: RESUELTO
- **Solucion**: Todos los disconnect ahora usan `repo.deactivate()` (soft-delete via `is_active = False`).

## 3. Arquitectura Resultante

```
connections/
  domain/
    channel.py          # ChannelConnection (Pydantic entity)
    enums.py            # ChannelType enum
  infrastructure/
    models/
      channel_connection_model.py  # ORM Model (EncryptedJSON credentials)
    repositories/
      channel_connection_repository.py  # SQLAlchemy 2.0 repository
    channels/
      telegram.py, whatsapp/, gmail.py, meta.py, instagram.py,
      google_calendar.py, youtube.py, google_analytics.py, webhook.py
      telegram_service.py  # Business logic for Telegram
    marketing_connectors/
      base.py             # BaseConnector ABC
      shopify.py, manychat.py, mailerlite.py
  api/
    whatsapp.py, telegram.py, meta.py, shopify.py, calendar.py,
    gmail.py, youtube.py, google_analytics.py, manychat.py,
    mailerlite.py, webhook.py, marketing_webhooks.py, shopify_compliance.py
    dependencies/
      webhook_security.py  # Centralized HMAC verification
    dto/
      meta.py, gmail.py, youtube.py, google_analytics.py
```
