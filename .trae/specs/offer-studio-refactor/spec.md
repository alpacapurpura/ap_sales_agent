# Offer Studio Refactor Spec

## Why
El "Offer Studio" actual es un formulario monolítico que dificulta la visualización del progreso y la gestión de secciones complejas. El usuario desea migrar a una experiencia "Brand Studio" (Sidebar retráctil + Live Preview + Edit Sheets), pero **preservando estrictamente** la arquitectura modular basada en "Atomic Design" y el patrón "Builder" actual.

## What Changes
- **Arquitectura de Configuración**: Se extiende `SECTION_REGISTRY` en `offer-builder-config.ts` para soportar metadatos de UI (iconos), componentes de previsualización (`previewComponent`) y componentes de formulario independientes (`formComponent`).
- **Layout Dinámico**: Implementar `OfferStudioLayout` que genera el sidebar y el contenido principal leyendo dinámicamente `OFFER_BUILDER_CONFIG[offerType]`.
- **Sidebar Retráctil**: `OfferNavRail` se genera iterando la configuración, mostrando el progreso de cada sección atómica.
- **Vista de Resumen (Live Preview)**: `OfferLivePreview` itera la configuración y renderiza los `previewComponent` de cada sección.
- **Edición Independiente (Atomic Forms)**: `OfferEditSheetManager` carga el `formComponent` correspondiente a la sección activa.
- **Reutilización de Componentes**: Los componentes existentes en `sections/` (ej. `StrategySection`) se reutilizarán envolviéndolos en un contexto de formulario aislado (`WrapperForm`) para mantener la lógica de campos pero permitir guardado independiente.

## Impact
- **Affected Specs**: Offer Management, UI Architecture.
- **Affected Code**:
    - `frontend/src/features/offer-studio/config/offer-builder-config.ts` (Extensión de tipos y registro).
    - `frontend/src/features/offer-studio/components/editor/OfferEditor.tsx` (Se reemplaza por el nuevo sistema dinámico).
    - `frontend/src/features/offer-studio/components/editor/sections/*` (Se mantienen como UI components, se crean wrappers).
- **New Components**:
    - `OfferNavRail`: Sidebar dinámico basado en config.
    - `OfferLivePreview`: Renderizador dinámico de previews.
    - `OfferEditSheetManager`: Orquestador de formularios.
    - `OfferSectionWrapper`: HOC o componente contenedor para aislar el contexto de `react-hook-form` de cada sección.

## ADDED Requirements
### Requirement: Dynamic Configuration Extension
El archivo `offer-builder-config.ts` DEBE ser la única fuente de verdad.
- Se debe extender la interfaz `OfferBuilderSectionConfig` para incluir:
  - `icon`: Icono Lucide para el sidebar.
  - `previewComponent`: Componente React para la vista de lectura.
  - `formComponent`: Componente React (Wrapper) para la edición.

### Requirement: Atomic Form Wrappers
Para reutilizar los componentes actuales (que esperan `form` prop):
- Se crearán componentes "Container" (ej. `StrategyFormContainer`) que:
  - Inicializan `useForm` con el esquema parcial correspondiente (ej. `StrategySchema`).
  - Renderizan el componente UI existente (ej. `<StrategySection form={form} />`).
  - Manejan `onSubmit` enviando solo ese fragmento de datos (`PATCH /offers/{id}`).

### Requirement: Dynamic Rendering
El sistema DEBE renderizar la UI iterando `OFFER_BUILDER_CONFIG[currentType]`:
- **Sidebar**: Muestra items solo para las secciones configuradas.
- **Preview**: Muestra tarjetas solo para las secciones configuradas.
- **Sheet**: Abre el formulario correspondiente al ID de la sección.

## MODIFIED Requirements
### Requirement: Offer Editor Architecture
**Antes**: Monolito.
**Ahora**: Orquestador Modular.
- El `OfferEditor` pasa a ser un componente que simplemente instancia el `OfferStudioLayout` y le pasa la configuración y los datos.

## REMOVED Requirements
### Requirement: Sequential Form Flow
**Reason**: Reemplazado por acceso aleatorio y edición en contexto (Sheet).
