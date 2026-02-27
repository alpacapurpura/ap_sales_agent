# IAM Module Refactoring Spec

## Why
El módulo IAM actual tiene modelos de dominio mezclados con esquemas de API y dependencias circulares. Se necesita una separación estricta entre Dominio, Infraestructura y API para cumplir con el estándar de Monolito Modular DDD.

## What Changes
Refactorización completa del módulo `src/modules/iam` siguiendo la arquitectura DDD.

-   **Domain**:
    -   Consolidar `user.py` y `user_models.py` en un único `user.py` (Pydantic puro).
    -   Consolidar `tenant.py` y `tenant_models.py` en un único `tenant.py` (Pydantic puro).
    -   Eliminar dependencias de `src.modules.iam.infrastructure` en el dominio.
-   **Infrastructure**:
    -   Asegurar que los modelos SQLAlchemy en `infrastructure/models/` hereden de `src.shared.infrastructure.db.base_model.Base`.
    -   Implementar `UserRepository` y `TenantRepository` que retornen entidades de dominio, no modelos ORM.
-   **Application**:
    -   Refactorizar `AuthService` y `TenantService` para usar Repositorios e interfaces de dominio.
-   **API**:
    -   Actualizar Routers para usar DTOs de entrada/salida mapeados desde entidades de dominio.

## Impact
-   **Affected Code**: `src/modules/iam/*`, `src/modules/iam/api/*`.
-   **Breaking Changes**: Cambiarán las rutas de importación de `User` y `Tenant` en todo el proyecto.

## ADDED Requirements

### Requirement: IAM Domain
-   `User`: Entidad raíz de usuario.
-   `Tenant`: Entidad raíz de tenant.
-   `TenantConfig`: Value object para la configuración JSON del tenant.

### Requirement: IAM Infrastructure
-   `UserModel`: Tabla `users`.
-   `TenantModel`: Tabla `tenants`.
-   `UserTenantModel`: Tabla de asociación `user_tenants` (Many-to-Many).

### Requirement: IAM Repositories
-   `UserRepository.get_by_email(email) -> Optional[User]`
-   `TenantRepository.get_by_id(id) -> Optional[Tenant]`
