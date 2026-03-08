# Add Marketing Connections Spec

## Why
El usuario necesita conectar múltiples plataformas de marketing (Shopify, MailerLite, ManyChat, Google Analytics, Meta Business Suite, YouTube) para centralizar la información y alimentar un futuro dashboard de estrategia (Lienzo de la Estrategia). El objetivo actual es establecer estas conexiones de forma segura, verificable y robusta.

## Guidelines & Constraints
- **Expert Execution**:
  - Todo cambio de Frontend DEBE ser implementado utilizando la skill `frontend-expert` (o siguiendo sus principios de diseño y arquitectura).
  - Todo cambio de Backend DEBE ser implementado utilizando la skill `backend-expert` (asegurando patrones DDD, manejo de errores y seguridad).
- **Documentation First**: Antes de implementar cada conexión, se DEBE consultar la documentación oficial vigente (a fecha 02/03/2026) para asegurar compatibilidad de API y métodos de autenticación.
- **Testability**: Cada conexión DEBE incluir un endpoint y botón de UI "Test Connection" que verifique la validez de las credenciales en tiempo real.
- **Observability**: Todos los errores de conexión y sincronización DEBEN ser registrados con logs estructurados (structlog) que incluyan contexto (tenant_id, servicio, tipo de error) para facilitar el debugging.

## What Changes
- **Backend**:
  - Implementación de nuevos routers API en `src/modules/connections/api/` para cada servicio.
  - Implementación de conectores en `src/modules/connections/infrastructure/marketing_connectors/`.
  - Registro de routers en `src/main.py`.
  - Persistencia de credenciales encriptadas.
  - Endpoints obligatorios por servicio: `connect`, `disconnect`, `status`, `test`.

- **Frontend**:
  - Actualización de `src/lib/api/connections.ts`.
  - Componentes de vista en `src/features/connections/components/` con UX clara para conectar y probar la conexión.
  - Integración en dashboard principal.

## Impact
- **Affected specs**: Módulo de Conexiones (Connections).
- **Affected code**: `backend/src/main.py`, `backend/src/modules/connections/`, `frontend/src/features/connections/`.

## ADDED Requirements
### Requirement: Shopify Connection
- **Auth**: OAuth (Public App) o Access Token (Custom App).
- **Test**: Verificar acceso a `shop.json` o similar.
- **Logs**: Registrar intentos fallidos de conexión y errores de API.

### Requirement: MailerLite Connection
- **Auth**: API Key.
- **Test**: Verificar acceso a `/subscribers` o `/account`.
- **Logs**: Registrar errores 401/403.

### Requirement: ManyChat Connection
- **Auth**: API Key.
- **Test**: Verificar acceso a `/page/getInfo`.
- **Logs**: Registrar errores de API.

### Requirement: Google Analytics (GA4) Connection
- **Auth**: OAuth 2.0 (Scope: `analytics.readonly`).
- **Test**: Listar propiedades de GA4 accesibles.
- **Logs**: Registrar errores de token refresh.

### Requirement: Meta Business Suite Connection
- **Auth**: OAuth 2.0 (Facebook Login).
- **Test**: Verificar acceso a `/me/accounts` o `/me/adaccounts`.
- **Logs**: Registrar errores de permisos insuficientes.

### Requirement: YouTube Connection
- **Auth**: OAuth 2.0 (Scope: `youtube.readonly`).
- **Test**: Verificar acceso a `/channels`.
- **Logs**: Registrar errores de API Data V3.

## MODIFIED Requirements
### Requirement: Connections Dashboard
- Interfaz unificada que muestre el estado de todas las nuevas conexiones.
- Botón "Probar Conexión" disponible para cada servicio conectado.
- Visualización de errores amigable al usuario si la prueba falla.
