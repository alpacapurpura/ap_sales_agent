# Fix Brand Settings Load Spec

## Why

El usuario reporta un error "Error al cargar configuración" al acceder al Brand Studio (`/brand-settings`).
El análisis sugiere que el endpoint `/api/v1/settings/brand` puede estar fallando (500 Internal Server Error) si el campo `brand_settings` en `Tenant.config_json` es `null` o está corrupto, lo que hace que el frontend falle silenciosamente y muestre un mensaje genérico.
Además, el frontend no expone la causa real del error, dificultando el diagnóstico.

## What Changes

### Backend (`backend/src/modules/brand/api/router.py`)

* Modificar `get_brand_settings` para manejar explícitamente el caso donde `config.get("brand_settings")` devuelve `None`.

* Asegurar que siempre se devuelva una instancia válida de `BrandSettings` (con valores por defecto) incluso si la configuración está vacía o corrupta.

* Agregar logging detallado en caso de error de validación Pydantic.

### Frontend (`frontend/src/features/brand/hooks/useBrandSettings.ts`)

* Exponer el objeto `error` de `useQuery` en el hook `useBrandSettings`.

### Frontend (`frontend/src/app/(main)/[tenantId]/(dashboard)/brand-settings/page.tsx`)

* Actualizar la UI para mostrar el mensaje de error específico si `useBrandSettings` falla, en lugar de solo "Error al cargar configuración".

* Agregar un botón de "Reintentar" o "Restablecer Configuración" (opcional, pero útil) si el error persiste.

## Impact

* **Affected specs**: Brand Studio.

* **Affected code**: `backend/src/modules/brand/api/router.py`, `frontend/src/features/brand/hooks/useBrandSettings.ts`, `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-settings/page.tsx`.

## ADDED Requirements

### Requirement: Robust Configuration Loading

The system SHALL return a default `BrandSettings` object if the stored configuration is `null` or missing, instead of raising an internal error.

#### Scenario: Null Brand Settings

* **WHEN** user requests brand settings AND `brand_settings` is `null` in DB

* **THEN** system returns default empty settings (200 OK)

### Requirement: Frontend Error Feedback

The system SHALL display the specific error message from the API if loading fails.

#### Scenario: API Error

* **WHEN** API returns 500 or 400

* **THEN** UI displays "Error al cargar configuración: \[Detalle del error]"

## Verification Plan (Test Plan)

Para asegurar que el Brand Studio quede completamente funcional, se ejecutarán las siguientes pruebas:

1. **Prueba de Reproducción (Script Python)**:

   * Simular un `Tenant` con `config_json={"brand_settings": null}`.

   * Llamar a `get_brand_settings` y verificar que falla (antes del fix) y pasa (después del fix).
2. **Prueba de Validación de Esquema**:

   * Verificar que `BrandSettings(**{})` y `BrandSettings(**None)` (con el fix) no lancen excepciones.
3. **Prueba End-to-End Manual**:

   * Acceder a la URL reportada con el usuario afectado.

   * Verificar que la página carga correctamente (incluso si está vacía).

