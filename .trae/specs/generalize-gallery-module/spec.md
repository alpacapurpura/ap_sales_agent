# Especificación: Generalización del Módulo Gallery

## Por qué
Actualmente, el módulo `gallery` está acoplado a la lógica de `offer` (e.g., `OfferGalleryService`, `offer_id` obligatorio). Para soportar `brand studio` y futuras funcionalidades como un gestor de "assets" centralizado, `gallery` debe ser un Módulo de Dominio independiente y genérico, no una utilidad compartida en `shared` ni un submódulo de `offer`.

Moverlo a `shared` es **incorrecto arquitecturalmente** porque `gallery` posee lógica de negocio (entidad `GalleryImage`, metadatos AI, estado en DB). `shared` debe reservarse para utilidades sin estado y lógica transversal (Logging, DB Base, etc.).

## Qué Cambios
- **Refactorización de Servicio**: Transformar `OfferGalleryService` en un `GalleryService` genérico.
- **Desacoplamiento**: Eliminar la dependencia fuerte de `offer_id` en la lógica central de carga y listado. Las imágenes pertenecerán al `tenant`, y `offer` (u otros módulos) podrán referenciarlas por ID/URL.
- **API Genérica**: Preparar el terreno para endpoints de galería generales (futuro módulo `assets`).
- **Mantenimiento de Compatibilidad**: Los endpoints existentes de `offer_gallery` seguirán funcionando, pero internamente usarán el servicio genérico.

## Impacto
- **Affected specs**: N/A
- **Affected code**: 
  - `backend/src/modules/gallery/application/offer_gallery_service.py` -> `gallery_service.py`
  - `backend/src/modules/gallery/infrastructure/repositories/offer_gallery_repository.py` -> `gallery_repository.py`
  - `backend/src/modules/gallery/api/offer_gallery.py` (Actualización de llamadas)

## Requisitos AÑADIDOS
### Requisito: Servicio de Galería Genérico
El sistema DEBE proveer un servicio capaz de cargar y listar imágenes basado únicamente en el `tenant_id`, sin requerir un contexto de `offer`.

#### Escenario: Carga Genérica
- **CUANDO** un usuario (o servicio) carga una imagen.
- **ENTONCES** la imagen se guarda asociada al `tenant`.
- **Y** se retorna la información de la imagen (ID, URL, metadatos) para ser usada por cualquier módulo (`brand`, `offer`, etc.).

## Requisitos MODIFICADOS
### Requisito: Endpoints de Offer Gallery
**Motivo**: Desacoplar la lógica de negocio.
**Cambio**: Los endpoints `/offer/{offer_id}/gallery` seguirán existiendo, pero su implementación delegará en `GalleryService` y manejará la asociación (si aplica) o simplemente filtrará por metadatos (si es necesario).
**Nota**: Por ahora, mantenemos la funcionalidad de `offer` tal cual, pero refactorizando el "backend" del módulo.
