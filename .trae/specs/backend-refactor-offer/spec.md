# Offer Module Refactoring Spec

## Why
El módulo Offer tiene una lógica de dominio rica y polimórfica (diferentes tipos de detalles según el tipo de oferta) que actualmente está parcialmente en modelos Pydantic (`schemas.py`) y parcialmente en el modelo SQLAlchemy (`Product` con campos JSONB). Se necesita una separación clara donde el dominio maneje la lógica de validación y polimorfismo, y la infraestructura solo persista los datos.

## What Changes
-   **Domain**:
    -   Consolidar `Offer` como la entidad raíz.
    -   Mantener el polimorfismo de `specific_details` (ProductDetails, ServiceDetails, etc.) usando Pydantic.
    -   Asegurar que todos los modelos hereden de `BaseEntity`.
    -   Renombrar `Product` (infra) a `OfferModel` para consistencia con el dominio `Offer`, o mantener `Product` si es ubicuo, pero preferiblemente alinear. (Decisión: Usar `ProductModel` en infra para evitar colisión con `ProductDetails`, y `Offer` en dominio).
-   **Infrastructure**:
    -   `ProductModel` (SQLAlchemy): Mapear los campos de dominio a columnas y JSONB.
    -   `OfferRepository`: Traducir entre `Offer` (Domain) y `ProductModel` (DB).
-   **Application**:
    -   `OfferGenerator`: Usar Repositorio.
    -   `OfferService`: CRUD y lógica de negocio.
-   **API**:
    -   Actualizar routers para usar DTOs alineados con el dominio.

## Impact
-   **Affected Code**: `src/modules/offer/*`.
-   **Breaking Changes**: Estructura de importaciones y nombres de clases.

## ADDED Requirements

### Requirement: Offer Domain
-   `Offer`: Root Aggregate.
-   Value Objects: `PricingStructure`, `DeliverableItem`.
-   Polymorphic Details: `ProductDetails`, `ServiceDetails`, `ProgramDetails`, `EventDetails`, `SubscriptionDetails`.

### Requirement: Offer Infrastructure
-   `ProductModel`: Tabla `products`.
-   `OfferGalleryImageModel`: Tabla `offer_gallery_images` (si aplica, revisar módulo Gallery).

### Requirement: Offer Repository
-   `OfferRepository.get_by_id(id) -> Optional[Offer]`
-   `OfferRepository.save(offer: Offer) -> Offer`
-   Manejo de campos JSONB para `specific_details`, `pricing`, `deliverables`.
