# Tasks

- [x] Task 1: Hardening de Seguridad (Cifrado de Credenciales)
  - [x] SubTask 1.1: Crear tests de integración para verificar el estado actual (texto plano) y asegurar que los endpoints funcionan.
  - [x] SubTask 1.2: Implementar métodos de cifrado/descifrado en `ChannelRepository` usando `src.core.security`.
  - [x] SubTask 1.3: Crear script de migración para cifrar credenciales existentes en la base de datos.
  - [x] SubTask 1.4: Actualizar `ChannelRepository` para cifrar al guardar y descifrar al leer automáticamente.
  - [x] SubTask 1.5: Verificar que los endpoints siguen funcionando y que los datos en BD están cifrados.

- [x] Task 2: Unificación de Mensajería (Instagram Channel)
  - [x] SubTask 2.1: Crear tests para la integración actual de Meta (si existen) o crear nuevos para verificar `MetaAdapter`.
  - [x] SubTask 2.2: Crear clase `InstagramChannel` en `infrastructure/channels/instagram.py` implementando `BaseChannel`.
  - [x] SubTask 2.3: Migrar lógica de `MetaAdapter` a `InstagramChannel`.
  - [x] SubTask 2.4: Registrar `InstagramChannel` en `ChatOrchestrator` para manejar `ChannelType.META` (o `INSTAGRAM`).
  - [x] SubTask 2.5: Actualizar endpoints de Meta para usar `InstagramChannel` si aplica.

- [x] Task 3: Estandarización de Datos y Webhooks
  - [x] SubTask 3.1: Crear dependencia `verify_webhook_signature` para centralizar validación (Shopify, Meta).
  - [x] SubTask 3.2: Refactorizar `ShopifyConnector` para implementar `BaseConnector`.
  - [x] SubTask 3.3: Refactorizar `GoogleCalendarAdapter` para implementar `BaseConnector`.
  - [x] SubTask 3.4: Verificar endpoints de Shopify y Calendar.

- [x] Task 4: Verificación Final
  - [x] SubTask 4.1: Ejecutar suite de pruebas completa de endpoints de conexiones.
  - [x] SubTask 4.2: Validar flujos de integración completos (guardar credenciales, recibir webhook, enviar mensaje).
