# Refactor Offer Studio UX Spec

## Why
El usuario requiere unificar la experiencia de usuario (UX) y la interfaz (UI) del "Offer Studio" con el "Brand Studio" para mantener consistencia visual y funcional. La disposición actual desperdicia espacio y el estilo de "tarjetas" no es el deseado. Se busca una experiencia más "editorial" y fluida.

## What Changes
- **Layout General**:
  - El **Título del Offer** se moverá a una barra superior fija (Header) que abarca todo el ancho, por encima de la barra lateral y el contenido.
  - La **Barra Lateral (Sidebar)** se ubicará debajo del Header, en el lado izquierdo. Será "pegajosa" (sticky) y colapsable para maximizar el área de visualización.
  - La navegación en la barra lateral hará **scroll** a la sección correspondiente en lugar de abrir el formulario de edición directamente.
- **Estilo de Contenido**:
  - Se eliminará el estilo de "Cards" (Tarjetas) que encierran cada sección.
  - Se adoptará el estilo "Editorial" del Brand Studio:
    - **Estado Vacío**: Mostrará una explicación y un "Call to Action" animando al usuario a completar la información.
    - **Estado Lleno**: Mostrará un resumen del contenido ingresado.
  - La edición se realizará mediante un **Sheet (Panel Lateral)** que se abrirá al hacer clic en "Editar" o en el estado vacío, manteniendo el contexto.

## Impact
- **Archivos Afectados**:
  - `frontend/src/features/offer-studio/components/container/OfferStudioLayout.tsx`: Reestructuración principal.
  - `frontend/src/features/offer-studio/components/navigation/OfferNavRail.tsx`: Ajustes de estilo y comportamiento (sticky, collapse).
  - `frontend/src/features/offer-studio/components/editor/sections/*`: Actualización de la presentación de cada sección.
  - `frontend/src/features/offer-studio/config/offer-builder-config.ts`: Posibles ajustes en la configuración de renderizado.

## ADDED Requirements
### Requirement: Header Fijo
El sistema DEBE mostrar el nombre del Offer y controles principales en una barra superior fija (sticky) que no se desplace con el contenido y ocupe el 100% del ancho.

### Requirement: Sidebar Mejorado
La barra lateral DEBE:
- Estar debajo del Header.
- Ser "sticky" para estar siempre visible.
- Permitir colapsar/expandir.
- Al hacer clic en un ítem, hacer scroll suave a la sección correspondiente en el área principal.

### Requirement: Estilo Editorial
Las secciones del Offer DEBEN:
- Mostrar un estado "Vacío" atractivo que explique el valor de la sección y tenga un botón de acción.
- Mostrar un estado "Resumen" limpio y legible cuando haya datos.
- Abrir el formulario de edición en un panel lateral (Sheet) sin perder la vista de contexto.

## MODIFIED Requirements
### Requirement: Navegación
**Antes**: Click en sidebar abría formulario/modal.
**Ahora**: Click en sidebar hace scroll a la vista previa de la sección.

## REMOVED Requirements
### Requirement: Card Style
**Reason**: El usuario explícitamente rechazó el estilo de "cajas" o "cards" para cada sección.
