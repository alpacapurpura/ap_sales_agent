# Brand Studio Integration Fix Specification

## 1. Contexto
El módulo "Brand Studio" permite gestionar la identidad de la marca, incluyendo configuración global (Settings), extracción automática desde URL y gestión de Avatares (Buyer Personas). Actualmente, la integración falla debido a endpoints inexistentes y discrepancias en el formato de envío de datos.

## 2. Objetivos
1. Habilitar la gestión completa de Avatares (CRUD + Set Default).
2. Corregir la extracción de marca asegurando compatibilidad de `Content-Type`.
3. Validar el flujo de datos de `BrandSettings`.

## 3. Cambios en Backend
### 3.1. Módulo Avatars (`backend/src/modules/brand`)
**Archivo:** `api/avatars.py`
- **Nuevo Endpoint:** `PATCH /{avatar_id}`
  - Input: `AvatarUpdate` (Partial DTO).
  - Lógica: Actualizar campos, actualizar `updated_at`.
- **Nuevo Endpoint:** `DELETE /{avatar_id}`
  - Lógica: Soft delete o hard delete (según política, por ahora hard delete).
- **Nuevo Endpoint:** `POST /{avatar_id}/set-default`
  - Lógica: Marcar este avatar como `is_default=True` y poner `is_default=False` a todos los demás del mismo `tenant_id`.

**Archivo:** `infrastructure/repositories/avatar_repository.py`
- Implementar métodos `update()`, `delete()` y `set_default_for_tenant()`.

### 3.2. Módulo Extraction (`backend/src/modules/brand`)
**Archivo:** `api/extraction.py`
- No se requieren cambios si se corrige el frontend. Mantener `Form(...)` es correcto para permitir subida de archivos mixta.

## 4. Cambios en Frontend
### 4.1. Cliente de API (`frontend/src/features/brand/api/index.ts`)
- **Fix:** En `extractFullBrand`, forzar SIEMPRE la conversión a `FormData`, incluso si no hay archivos. Esto alinea el request con lo que espera FastAPI (`Form(...)`).

### 4.2. Cliente de Avatares (`frontend/src/lib/api/avatar.ts`)
- Verificar que las rutas coincidan exactamente con las nuevas implementaciones del backend.

## 5. Validación
- **Avatares:** Crear 3 avatares, editar uno, borrar otro, y cambiar el principal.
- **Extracción:** Ejecutar extracción solo con URL (sin archivos) y verificar que no dé error 422.
