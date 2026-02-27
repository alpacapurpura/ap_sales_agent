# Tareas

- [x] Tarea 1: Refactorizar Capa de Infraestructura y Dominio
  - [x] SubTarea 1.1: Renombrar `OfferGalleryRepository` a `GalleryRepository` en `infrastructure/repositories`.
  - [x] SubTarea 1.2: Asegurar que los métodos del repositorio acepten filtros genéricos (tenant_id) y no dependan estrictamente de `offer_id` (hacerlo opcional si es columna de DB, o manejarlo como metadato).
  - [x] SubTarea 1.3: Crear migración de base de datos para agregar columna `offer_id` a tabla `gallery_images`.

- [x] Tarea 2: Refactorizar Capa de Aplicación
  - [x] SubTarea 2.1: Crear/Renombrar `GalleryService` (desde `OfferGalleryService`).
  - [x] SubTarea 2.2: Implementar método `upload_image` genérico (tenant_id, file, metadata).
  - [x] SubTarea 2.3: Implementar método `list_images` genérico (tenant_id, filtros opcionales).

- [x] Tarea 3: Actualizar API de Offer
  - [x] SubTarea 3.1: Actualizar `api/offer_gallery.py` para instanciar y usar `GalleryService`.
  - [x] SubTarea 3.2: Verificar que los endpoints de Offer sigan funcionando correctamente (Backward Compatibility).

- [x] Tarea 4: Limpieza
  - [x] SubTarea 4.1: Eliminar código muerto o referencias a "Offer" dentro de la lógica pura de Galería.
