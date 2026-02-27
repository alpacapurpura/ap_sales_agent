# Admin Panel Restructure Spec

## Why
El panel administrativo actual contiene funcionalidades dispersas y no optimizadas para la gestión operativa de un SaaS Multi-Tenant. El dueño del producto necesita una herramienta centralizada y eficiente para provisionar Tenants, gestionar Usuarios (altas, bajas, contraseñas) y controlar el acceso a recursos costosos (LLM Keys) como parte de su flujo de soporte y ventas.

## What Changes
- **Reescritura total de `backend/src/admin/app.py`**: Se eliminarán módulos antiguos (Lead Audit, RAG Config) para centrarse exclusivamente en la gestión de Tenants y Usuarios.
- **Nuevo Módulo de Gestión de Tenants**:
  - Listado de Tenants existentes.
  - Creación de nuevos Tenants.
  - Edición de configuración crítica: Toggle `can_use_platform_keys` (Permitir uso de llaves de la plataforma).
- **Nuevo Módulo de Gestión de Usuarios**:
  - Selección de Tenant para filtrar usuarios.
  - Creación de Usuarios con Email/Contraseña (Sincronización dual: Clerk + Base de Datos Local).
  - Acciones de Soporte: "Cambiar Contraseña" y "Bloquear/Desbloquear Acceso".
- **Mejoras en Backend (`ClerkService`)**:
  - Implementación de métodos para reseteo de contraseña administrativo.
  - Implementación de métodos para bloqueo (ban) de usuarios en Clerk.

## Impact
- **Affected specs**: Admin Dashboard.
- **Affected code**: 
  - `backend/src/admin/`: Reemplazo completo de la lógica de UI.
  - `backend/src/services/clerk.py`: Nuevos métodos para soporte de usuarios.
  - `backend/src/services/db/models/user.py`: Asegurar consistencia en creación.

## ADDED Requirements

### Requirement: Tenant Management
El sistema SHALL permitir al superadmin gestionar el ciclo de vida de los Tenants.

#### Scenario: Provisioning
- **WHEN** el admin ingresa nombre, slug y configuración de llaves
- **THEN** se crea el Tenant en Postgres
- **AND** se habilita/deshabilita el uso de `platform_keys` según el checkbox seleccionado.

### Requirement: User Provisioning
El sistema SHALL permitir crear usuarios asociados a un Tenant específico con credenciales iniciales.

#### Scenario: Manual Creation
- **WHEN** el admin selecciona un Tenant e ingresa Email, Password y Nombre
- **THEN** el sistema crea el usuario en Clerk (Identity Provider)
- **AND** el sistema crea el usuario en Postgres (Local DB) vinculado al `tenant_id`
- **AND** se asigna el `clerk_id` correcto en la DB local.

### Requirement: User Support Actions
El sistema SHALL ofrecer herramientas de soporte rápido.

#### Scenario: Password Reset
- **WHEN** el admin selecciona un usuario y una nueva contraseña
- **THEN** se actualiza la contraseña en Clerk inmediatamente.

#### Scenario: Access Block
- **WHEN** el admin bloquea a un usuario
- **THEN** el usuario es marcado como `banned` en Clerk (impidiendo login)
- **AND** se actualiza `is_active=False` en la DB local.

## REMOVED Requirements
### Requirement: Legacy Modules
**Reason**: El usuario solicitó eliminar "las demás opciones" para limpiar la interfaz.
**Migration**: Se eliminarán las referencias a Lead Audit y Safety Layer del menú principal.
