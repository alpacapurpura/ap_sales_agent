# Refactor OAuth to Multitenant (BYOA) Spec

## Why
El usuario ha detectado que las implementaciones de OAuth (Google, Meta, YouTube) dependen de variables de entorno globales, lo cual impide que cada organización utilice su propia aplicación (Client ID/Secret propios). Se requiere refactorizar estos servicios para seguir el modelo "Bring Your Own App" (BYOA), alineándolos con Shopify, MailerLite y ManyChat que ya son multitenant al requerir credenciales por tenant.

## What Changes
- **Backend**:
  - **Google Analytics, Meta, YouTube**:
    - Nuevos endpoints `PUT /config` para guardar `client_id` y `client_secret` por tenant.
    - Actualización de `GET /auth-url` y `POST /callback` para usar las credenciales almacenadas del tenant en lugar de `settings`.
  - **Shopify, MailerLite, ManyChat**:
    - **Revisión**: Se confirma que ya operan en modo multitenant (input directo de Token/API Key por el usuario). No requieren cambios estructurales, solo verificación.

- **Frontend**:
  - **Google Analytics, Meta, YouTube Views**:
    - Implementación de un "Modo Configuración" (inputs para App ID/Secret) que debe completarse antes de mostrar el botón de "Conectar".
    - Indicadores visuales de si el servicio tiene credenciales configuradas.

## Impact
- **Affected specs**: Módulo de Conexiones.
- **Affected code**: `api/google_analytics.py`, `api/meta.py`, `api/youtube.py`, y sus vistas frontend.

## ADDED Requirements
### Requirement: BYOA Configuration Flow
Para servicios OAuth, el usuario debe poder ingresar sus credenciales de aplicación antes de iniciar la conexión.
- **Scenario: Initial Setup**
  - **WHEN** el usuario entra a la pestaña de Google Analytics por primera vez.
  - **THEN** ve un formulario para ingresar "Client ID" y "Client Secret".
  - **WHEN** guarda el formulario.
  - **THEN** aparece el botón "Conectar con Google".

### Requirement: Tenant-Scoped OAuth
El flujo de OAuth debe ejecutarse utilizando estrictamente las credenciales configuradas por el tenant.
- **Scenario: Auth Flow**
  - **WHEN** el usuario hace clic en "Conectar".
  - **THEN** la URL de redirección de Google/Meta contiene el `client_id` propio del tenant.

## MODIFIED Requirements
### Requirement: Env Var Removal
Se elimina el uso de `settings.GOOGLE_CLIENT_ID`, `settings.META_APP_ID`, etc., en la lógica de conexión.
