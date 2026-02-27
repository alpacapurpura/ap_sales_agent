# Brand Module Refactoring Spec

## Why
El módulo Brand actual almacena la configuración en un JSON (`config_json['brand_settings']`) dentro del modelo `Tenant`, pero las definiciones de Pydantic están en `src/modules/brand/domain/models.py` mezcladas con lógica de API. Se necesita formalizar la estructura de dominio y desacoplar la lógica de extracción.

## What Changes
-   **Domain**:
    -   Mover `BrandSettings`, `BrandIdentity`, `BrandStrategy`, etc. a `src/modules/brand/domain/`.
    -   Asegurar que sean modelos Pydantic puros heredando de `BaseEntity`.
-   **Infrastructure**:
    -   Implementar `BrandRepository` para encapsular el acceso a `Tenant.config_json`. Esto abstrae la persistencia JSON.
    -   Mover `AvatarModel` a `infrastructure/models/`.
-   **Application**:
    -   Refactorizar `BrandExtractionService` para usar `BrandRepository` en lugar de acceder directamente a `TenantModel`.
    -   Desacoplar la lógica de scraping/LLM en adaptadores si es posible, o mantenerla en application services pero limpia.
-   **API**:
    -   Actualizar routers para usar los nuevos servicios y DTOs.

## Impact
-   **Affected Code**: `src/modules/brand/*`.
-   **Breaking Changes**: La forma de instanciar `BrandSettings` podría cambiar ligeramente al heredar de `BaseEntity`.

## ADDED Requirements

### Requirement: Brand Domain
-   `BrandSettings`: Agregado raíz (Root Aggregate) para la configuración de marca.
-   Sub-entidades: `BrandIdentity`, `BrandStrategy`, `BrandStory`, `BrandVisuals`, `BrandCompetitor`, `BrandTargetAudience`.

### Requirement: Brand Repository
-   `BrandRepository.get_settings(tenant_id) -> BrandSettings`
-   `BrandRepository.save_settings(tenant_id, settings: BrandSettings)`
-   El repositorio maneja la lectura/escritura en `TenantModel.config_json`.

### Requirement: Avatar Domain & Infra
-   `Avatar`: Entidad de dominio.
-   `AvatarModel`: Modelo SQLAlchemy (ya existe, verificar ubicación).
-   `AvatarRepository`: CRUD para Avatares.
