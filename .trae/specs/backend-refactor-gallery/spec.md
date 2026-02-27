# Gallery Module Refactoring Spec

## Why
El módulo Gallery gestiona los activos visuales (imágenes) asociados a Ofertas. Actualmente, los modelos de dominio e infraestructura están mezclados o dispersos. Se necesita estandarizar la entidad `Asset` (o `GalleryImage`) y su persistencia.

## What Changes
-   **Domain**:
    -   `GalleryImage`: Entidad pura (Pydantic) heredando de `BaseEntity`.
    -   Campos: `id`, `offer_id`, `filename`, `public_url`, `ai_metadata`.
-   **Infrastructure**:
    -   `OfferGalleryImageModel` (SQLAlchemy): Mover a `infrastructure/models/gallery_model.py`.
    -   `GalleryRepository`: CRUD.
-   **Application**:
    -   `GalleryService`: Lógica de subida, procesamiento y eliminación.
-   **API**:
    -   `router.py`: Actualizar para usar `GalleryService`.

## Impact
-   **Affected Code**: `src/modules/gallery/*`.
-   **Breaking Changes**: Rutas de importación.

## ADDED Requirements

### Requirement: Gallery Domain
-   `GalleryImage`: Entidad de dominio.

### Requirement: Gallery Infrastructure
-   `OfferGalleryImageModel`: Tabla `offer_gallery_images`.
-   FK a `Tenant` y `Product` (Offer).

### Requirement: Gallery Application
-   `GalleryService.upload_image(...) -> GalleryImage`
-   `GalleryService.list_by_offer(offer_id) -> List[GalleryImage]`
