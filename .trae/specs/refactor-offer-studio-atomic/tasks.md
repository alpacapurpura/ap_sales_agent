# Tasks

- [ ] Task 1: Backend - Definir Esquemas y Endpoints Atómicos
  - [ ] SubTask 1.1: Crear esquemas Pydantic para cada sección (`Identity`, `Strategy`, `Pricing`, `Details`, `Gallery`, `Closing`, etc.) en `backend/src/core/domain/offer/schema.py`.
  - [ ] SubTask 1.2: Implementar endpoints `PATCH /{id}/{section}` en `backend/src/api/routers/products.py` utilizando los nuevos esquemas.
  - [ ] SubTask 1.3: Actualizar `ProductRepository` si es necesario para manejar actualizaciones parciales específicas (o reutilizar el update genérico con el diccionario filtrado).

- [ ] Task 2: Frontend - Reestructuración de Carpetas (Refactor)
  - [ ] SubTask 2.1: Crear la estructura de carpetas `src/features/offer-studio/components/editor/sections/{domain}`.
  - [ ] SubTask 2.2: Mover `IdentityForm` y `IdentityPreview` a `sections/identity/`.
  - [ ] SubTask 2.3: Mover `StrategyForm` y `StrategyPreview` a `sections/strategy/`.
  - [ ] SubTask 2.4: Mover `PricingForm` y `PricingPreview` a `sections/pricing/`.
  - [ ] SubTask 2.5: Mover el resto de componentes (Gallery, Closing, Resources, Instructors, ValueStack, Details) a sus respectivas carpetas de dominio.
  - [ ] SubTask 2.6: Eliminar las carpetas antiguas `forms/` y `preview/` una vez vacías.

- [ ] Task 3: Frontend - Integración con Endpoints Atómicos
  - [ ] SubTask 3.1: Actualizar el servicio de API del frontend (`offer-service.ts` o similar) para incluir métodos como `updateIdentity`, `updatePricing`, etc.
  - [ ] SubTask 3.2: Actualizar cada formulario movido para que use la llamada a la API específica en lugar de la genérica al guardar.
  - [ ] SubTask 3.3: Actualizar `offer-builder-config.ts` para apuntar a las nuevas rutas de los componentes.

# Task Dependencies
- Task 2 y Task 3 dependen parcialmente de Task 1 (para la integración final), pero el movimiento de archivos (Task 2) puede hacerse en paralelo si se mantienen los imports. Se recomienda hacer Task 1 -> Task 2 -> Task 3.
