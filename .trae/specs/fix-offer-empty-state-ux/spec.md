# Fix Offer Empty State UX Spec

## Why
El usuario rechazó la implementación anterior del "Estado Vacío" en Offer Studio por ser demasiado "transaccional" (cajas con bordes discontinuos y botones explícitos). Se requiere replicar la experiencia "Editorial" del Brand Studio, que es más limpia, inspiracional y menos invasiva.

## What Changes
- **Diseño de Estado Vacío**:
  - Eliminar el contenedor con borde discontinuo (`border-dashed`).
  - Usar un diseño **indentado** (`pl-14`) alineado con el título.
  - Mostrar una **frase inspiracional** en cursiva (`italic text-muted-foreground`) en lugar de instrucciones genéricas.
  - El botón de acción ("Definir Estrategia", etc.) debe estar **oculto por defecto** y aparecer solo al hacer **hover** (`opacity-0 group-hover:opacity-100`).
  - Eliminar el botón "Comenzar Edición" visible permanentemente.
- **Contenido**:
  - Definir frases específicas (Quotes) para cada tipo de sección (Identidad, Estrategia, Precios, etc.) que aporten valor educativo/inspiracional.
- **Visualización General**:
  - Eliminar wrappers de fondo innecesarios en `OfferLivePreview` para mantener la limpieza visual.

## Impact
- **Archivos Afectados**:
  - `frontend/src/features/offer-studio/components/editor/OfferSectionWrapper.tsx`: Refactorización completa del renderizado.
  - `frontend/src/features/offer-studio/components/editor/OfferLivePreview.tsx`: Inyección de frases y configuración de metadatos.

## ADDED Requirements
### Requirement: Frases Inspiracionales
Cada sección vacía DEBE mostrar una frase única relacionada con su propósito (ej: "El precio es solo un número; el valor es lo que perciben" para Pricing).

### Requirement: Interacción Sutil
El llamado a la acción DEBE ser sutil: texto coloreado con icono pequeño, visible solo cuando el usuario muestra intención (hover).

## REMOVED Requirements
### Requirement: Dashed Border Box
**Reason**: Considerado "transaccional" y poco elegante por el usuario.
