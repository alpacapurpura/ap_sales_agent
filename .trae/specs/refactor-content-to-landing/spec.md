# Refactor Content Module to Landing Spec

## Why
El módulo `content` actual contiene lógica mezclada de Landing Pages, Ofertas, Galerías y Enlaces Públicos. El objetivo es aislar la lógica de Landing Pages en un módulo dedicado llamado `landing` y mover el resto de funcionalidades a sus módulos correspondientes (`offer` y `communication`) para mejorar la cohesión y seguir la arquitectura modular.

## What Changes
- **Mover** lógica de Ofertas y Galería desde `content` hacia `offer`.
- **Mover** lógica de Enlaces Públicos desde `content` hacia `communication`.
- **Renombrar** la carpeta `src/modules/content` a `src/modules/landing`.
- **Actualizar** todas las importaciones en el proyecto para reflejar estos cambios.

## Impact
- **Affected specs**: Módulos `content`, `offer`, `communication`.
- **Affected code**: Imports en todo el backend que referencien a `src.modules.content`.

## ADDED Requirements
### Requirement: Estructura de Carpetas
- `src/modules/landing` debe contener SOLO lógica relacionada con Landing Pages.
- `src/modules/offer` debe contener lógica de Ofertas, Productos y Galería.
- `src/modules/communication` debe contener lógica de Enlaces Públicos y Reservas.

## MODIFIED Requirements
### Requirement: Imports
- Todo import `from src.modules.content...` debe ser actualizado a su nueva ubicación:
    - `src.modules.landing...` (si es de landing)
    - `src.modules.offer...` (si es de oferta)
    - `src.modules.communication...` (si es de enlaces)

## REMOVED Requirements
### Requirement: Módulo Content
- El módulo `content` deja de existir como tal y pasa a ser `landing`.
