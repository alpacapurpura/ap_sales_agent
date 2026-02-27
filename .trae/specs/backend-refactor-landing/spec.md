# Landing Module Refactoring Spec

## Why
El módulo Landing gestiona la generación y publicación de landing pages. Actualmente, los esquemas de contenido están en `domain/landing_page/content_schemas.py` y no hay modelos de infraestructura claros. Se necesita persistir las landings generadas por IA y sus configuraciones.

## What Changes
-   **Domain**:
    -   `LandingPage`: Entidad raíz. Contiene `LandingPageConfig` (Value Object con polimorfismo).
    -   `Component`: Entidad para bloques reutilizables (opcional, si se usa Puck).
    -   `Enums`: `LandingPageArchetype`, `LandingPageFont`.
-   **Infrastructure**:
    -   `LandingPageModel` (SQLAlchemy): Tabla `landing_pages`.
    -   `LandingRepository`: CRUD.
-   **Application**:
    -   `LandingService`: CRUD y publicación.
    -   `LandingGenerator`: Servicio de IA (existente, refactorizar si es necesario).
-   **API**:
    -   `landing.py`: Router actualizado.

## Impact
-   **Affected Code**: `src/modules/landing/*`.
-   **Breaking Changes**: Rutas de importación.

## ADDED Requirements

### Requirement: Landing Domain
-   `LandingPage`: ID, Slug, Config (JSON), Status.
-   Polimorfismo en `Config.content` según arquetipo.

### Requirement: Landing Infrastructure
-   `LandingPageModel`: Campos JSONB para `config`.
-   FK a `Tenant` y `Product` (Offer).

### Requirement: Landing Application
-   `LandingService.create_from_offer(offer_id) -> LandingPage`
-   `LandingService.publish(id) -> str (url)`
