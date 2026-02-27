# Frontend Architecture Audit and Refactor Spec

## Why
El usuario requiere una auditoría completa del frontend para asegurar que el código sea mantenible, escalable y extensible. Se busca eliminar duplicidad, asegurar la correcta ubicación de archivos y funciones, y verificar el cumplimiento de buenas prácticas (SOLID, Clean Code).

## What Changes
- **Reorganización de `src/app`**: Mover lógica de negocio a `src/features` y dejar solo rutas y layouts.
- **Estandarización de `src/features`**: Asegurar que cada feature siga la estructura `components`, `hooks`, `types`, `index.ts`.
- **Limpieza de `src/components`**: Verificar que `ui` contenga solo componentes Shadcn sin modificaciones internas no autorizadas, y que `shared` sea realmente reutilizable.
- **Eliminación de Duplicidad**: Identificar y consolidar código repetido en utilidades o hooks compartidos.
- **Mejora de Imports**: Asegurar que los imports sean limpios y sigan las reglas de arquitectura.
- **Verificación de Buenas Prácticas**: Revisar nombres de variables/funciones, tamaño de funciones, y responsabilidades únicas.

## Impact
- **Mantenibilidad**: Código más limpio y fácil de entender.
- **Escalabilidad**: Estructura modular que facilita agregar nuevas features.
- **Extensibilidad**: Código desacoplado y reutilizable.
- **Rendimiento**: Posible mejora al reducir código duplicado y optimizar imports.

## ADDED Requirements
### Requirement: Architecture Compliance
El código DEBE cumplir estrictamente con la estructura definida en `.trae/rules/front-structure.md`.

#### Scenario: Code Location
- **WHEN** se revisa un archivo en `src/app`
- **THEN** debe contener solo definición de rutas y layouts, importando lógica de `src/features`.

#### Scenario: Feature Isolation
- **WHEN** se revisa una feature en `src/features`
- **THEN** debe contener su propia lógica, componentes y tipos, exponiendo solo lo necesario en `index.ts`.

## MODIFIED Requirements
### Requirement: Component Structure
Los componentes en `src/components/ui` NO DEBEN contener lógica de negocio ni modificaciones que rompan la compatibilidad con futuras actualizaciones de Shadcn.

## REMOVED Requirements
### Requirement: Inline Logic in Pages
**Reason**: Dificulta la mantenibilidad y testabilidad.
**Migration**: Mover lógica a custom hooks en `src/features/[feature]/hooks`.
