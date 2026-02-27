# Offer Studio Structure Refactor Spec

## Why
La arquitectura actual de `offer-studio` tiene inconsistencias en los nombres de archivos (mezcla de CamelCase y kebab-case) y en la separación de responsabilidades (algunos componentes mezclan lógica de negocio con UI). Esto contrasta con la arquitectura de `brand`, que sigue un patrón claro de `Manager` (Lógica) -> `Form` (UI) y nombres en `kebab-case`. Esta inconsistencia aumenta la deuda técnica y dificulta el mantenimiento.

## What Changes
- **Standardization**: Todos los archivos en `features/offer-studio/components/editor/sections` serán renombrados a `kebab-case`.
- **Architectural Pattern**: Se adoptará el patrón `Manager-Form-Preview` de `brand` para las secciones complejas de `offer-studio` (como Instructors, Resources, Gallery).
- **Configuration**: Se actualizará `offer-builder-config.ts` para reflejar los nuevos nombres y estructuras.

## Impact
- **Affected Specs**: `offer-studio` feature spec.
- **Affected Code**: 
  - `frontend/src/features/offer-studio/components/editor/sections/**/*`
  - `frontend/src/features/offer-studio/config/offer-builder-config.ts`
  - `frontend/src/features/offer-studio/components/editor/OfferEditSheetManager.tsx`

## ADDED Requirements
### Requirement: Kebab-Case Standardization
El sistema SHALL utilizar `kebab-case` para todos los nombres de archivo en `offer-studio`, eliminando CamelCase.

#### Scenario: File Renaming
- **WHEN** developer adds a new section component
- **THEN** file name MUST be in `kebab-case` (e.g., `my-new-section.tsx`, not `MyNewSection.tsx`)

### Requirement: Manager Pattern for Complex Sections
El sistema SHALL utilizar un componente `Manager` para encapsular la lógica de obtención de datos y manejo de estado en secciones que requieran datos externos (e.g., Instructors, Resources).

#### Scenario: Data Fetching Encapsulation
- **WHEN** a section needs to fetch data (e.g., list of instructors)
- **THEN** a `[section]-manager.tsx` component MUST handle the query and pass data to the presentation component via props.

## MODIFIED Requirements
### Requirement: Offer Builder Configuration
**Modification**: `offer-builder-config.ts` SHALL import components from their new `kebab-case` paths and use the `Manager` components where applicable.

## REMOVED Requirements
### Requirement: CamelCase Files
**Reason**: Inconsistency with project standards.
**Migration**: Rename existing CamelCase files to kebab-case and update imports.
