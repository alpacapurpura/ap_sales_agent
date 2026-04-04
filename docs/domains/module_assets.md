---
module: Assets
status: active
---

# Assets

Centraliza almacenamiento, validacion y enriquecimiento IA de archivos (imagenes, documentos, audio, video). Otros modulos guardan solo `asset_id` o `public_url` como referencia.

## Architecture Decisions

- **Storage hibrido**: `LOCAL` (dev) y `R2` (Cloudflare R2 via S3-compatible API, produccion). Controlado por `settings.STORAGE_PROVIDER`. No se usa S3 de AWS.
- **Procesamiento asincrono**: Upload retorna `Asset` con `status=PROCESSING`. Un background task enriquece con IA (`ai_metadata`: descripcion, colores, OCR) y pasa a `COMPLETED` o `FAILED`.
- **`public_url` es la URL final**. El frontend nunca debe construir URLs manualmente concatenando paths.

## Business Rules

- Validacion de MIME por magic number del archivo, no solo por extension. Renombrar `.exe` a `.jpg` falla.
- Consumidores deben tolerar `ai_metadata` vacio (latencia de IA, o fallo del procesador).
- Preferir guardar `asset_id` (no solo URL) en otros modulos para mantener integridad referencial y acceso a metadata.

## Edge Cases

- **Borrado en cascada**: Si se borra un asset, modulos que guardan solo la URL quedan con enlace roto. Usar `asset_id` permite validar antes de borrar.
- `GalleryImage` es un alias deprecated de `Asset` (backward compatibility).

## CRITICAL -- Do Not Violate

- Todo archivo pasa por `AssetsService`. Nunca subir directamente al storage desde otro modulo.
- Toda query filtra por `tenant_id`.
