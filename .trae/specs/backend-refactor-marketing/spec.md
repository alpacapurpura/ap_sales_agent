# Marketing Module Refactoring Spec

## Why
El módulo Marketing (CDP) gestiona la identidad unificada de los clientes (`CustomerProfile`). Actualmente, los modelos están en `infrastructure/models/customer.py` mezclando definiciones de Enum y ORM. Se requiere una capa de Dominio pura para manejar la lógica de unificación de identidad y segmentación.

## What Changes
-   **Domain**:
    -   `CustomerProfile`: Entidad raíz.
    -   `CustomerIdentity`: Entidad hija.
    -   `JourneyEvent`: Value Object / Entidad inmutable.
    -   `Enums`: `IdentityType`, `LifecycleStage`.
-   **Infrastructure**:
    -   `CustomerProfileModel`, `CustomerIdentityModel`, `JourneyEventModel` (SQLAlchemy) en `infrastructure/models/`.
    -   `CustomerRepository`: CRUD y búsqueda por identidad.
-   **Application**:
    -   `CustomerService`: Lógica de resolución de identidad (Identity Resolution).
    -   `SegmentationService`: Lógica de segmentos (placeholder).
-   **API**:
    -   `cdp.py`: Router actualizado.

## Impact
-   **Affected Code**: `src/modules/marketing/*`.
-   **Breaking Changes**: Rutas de importación.

## ADDED Requirements

### Requirement: Marketing Domain
-   `CustomerProfile`: ID, Email, Phone, Name, Scoring.
-   `CustomerIdentity`: Type, Value, Verification.

### Requirement: Marketing Infrastructure
-   Modelos SQLAlchemy heredando de `Base`.
-   Repositorios manejan la relación Profile <-> Identities.

### Requirement: Marketing Application
-   `CustomerService.identify(traits, tenant_id) -> CustomerProfile` (Identity Resolution logic).
