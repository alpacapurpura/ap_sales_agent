# Refactor Offer Studio: Atomicidad y Diseño Orientado a Dominios

## Why
Actualmente, el editor del Offer Studio (`frontend/src/features/offer-studio/components/editor`) tiene una estructura monolítica donde todos los formularios están en `forms/` y todas las vistas previas en `preview/`. Esto dificulta la mantenibilidad y la cohesión, ya que la lógica de una sección (ej. "Pricing") está dispersa. Además, el backend utiliza un único endpoint `PATCH` genérico que recibe un objeto `ProductUpdate` masivo, lo que no favorece la atomicidad ni la validación estricta por sección.

El objetivo es aplicar los aprendizajes del Brand Studio (DDD) para reestructurar el código en carpetas por dominio (ej. `pricing/`, `identity/`) y crear endpoints específicos en el backend para asegurar actualizaciones atómicas y validadas por contexto.

## What Changes

### Frontend (Reestructuración y Atomicidad)
- **Reorganización de Carpetas**: Mover componentes de `forms/` y `preview/` a carpetas de dominio dentro de `components/editor/sections/`:
  - `identity/`: `IdentityForm`, `IdentityPreview`
  - `strategy/`: `StrategyForm`, `StrategyPreview`
  - `pricing/`: `PricingForm`, `PricingPreview`
  - `program/`: `ProgramDetailsForm`, `InstructorsForm`, `CurriculumForm` (agrupación lógica)
  - `visuals/`: `GalleryForm`, `GalleryPreview`
  - `closing/`: `ClosingForm`, `ClosingPreview`
  - ... y así sucesivamente para todas las secciones.
- **Refactorización de Formularios**: Actualizar cada formulario para que use un hook o servicio que llame al endpoint específico de su sección, en lugar de un `updateProduct` genérico.

### Backend (Endpoints Atómicos)
- **Nuevos Esquemas Pydantic**: Crear esquemas de actualización específicos para cada sección en `backend/src/core/domain/offer/schema.py` (ej. `OfferIdentityUpdate`, `OfferPricingUpdate`).
- **Nuevos Endpoints**: Crear endpoints dedicados en `backend/src/api/routers/products.py` para actualizaciones parciales explícitas:
  - `PATCH /{product_id}/identity`
  - `PATCH /{product_id}/strategy`
  - `PATCH /{product_id}/pricing`
  - `PATCH /{product_id}/details` (para detalles polimórficos)
  - ...
- **Validación Estricta**: Cada endpoint validará solo los campos permitidos para esa sección.

## Impact
- **Affected Specs**: Offer Studio.
- **Affected Code**:
  - Frontend: `src/features/offer-studio/components/editor/*`, `src/features/offer-studio/config/offer-builder-config.ts`.
  - Backend: `src/api/routers/products.py`, `src/core/domain/offer/schema.py`.

## ADDED Requirements
### Requirement: Atomic Updates
El sistema DEBE permitir actualizar secciones individuales de una oferta sin enviar el objeto completo.
#### Scenario: Update Pricing
- **WHEN** el usuario guarda el formulario de precios.
- **THEN** se envía una petición `PATCH /products/{id}/pricing` con solo los datos de precios.
- **AND** el backend valida que los datos cumplan con `OfferPricingUpdate`.

## MODIFIED Requirements
### Requirement: Estructura de Carpetas
El código fuente del editor DEBE estar organizado por dominios funcionales (Identity, Strategy, Pricing, etc.) y NO por tipo de archivo técnico (Form vs Preview).
