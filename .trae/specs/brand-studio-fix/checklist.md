# Checklist de Verificación de Integración

## Backend
- [x] El endpoint `PATCH /api/v1/avatars/{id}` actualiza el nombre y descripción.
- [x] El endpoint `DELETE /api/v1/avatars/{id}` elimina el registro.
- [x] El endpoint `POST /api/v1/avatars/{id}/set-default` cambia el flag `is_default` y lo quita del anterior.
- [x] `extract_full_brand` recibe correctamente los datos cuando el frontend envía solo texto/URL.

## Frontend
- [x] `BrandEmptyState` desaparece al guardar la configuración inicial.
- [x] La lista de Avatares muestra correctamente el badge "Principal".
- [x] El botón de "Eliminar Avatar" funciona sin errores de red.
- [x] La herramienta de extracción no lanza error 422 en la consola.
