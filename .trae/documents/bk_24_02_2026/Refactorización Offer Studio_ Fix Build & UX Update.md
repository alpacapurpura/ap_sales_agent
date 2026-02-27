# Solución Completa: Refactorización UX/UI del Offer Studio

He corregido el error de construcción y refactorizado todo el módulo para cumplir con los principios de diseño (FSD) y mejorar la experiencia de usuario tanto en la creación como en la edición.

## 1. Corrección del Error Crítico
El error `Module not found` se debía a una ruta de importación relativa incorrecta en `specific-details-step.tsx`.
*   **Antes**: `import ... from "../types/index"` (Buscaba en `components/types`)
*   **Ahora**: `import ... from "../../types/index"` (Busca correctamente en la raíz del feature)

## 2. Refactorización UX: Creación vs. Edición
Entendiendo que los "Wizards" son para flujos lineales de primera vez y la "Edición" requiere acceso aleatorio:

### A. Flujo de Creación (`/offer-studio/new`)
*   Se mantiene el **OfferWizard** paso a paso.
*   **Mejora**: Ahora envía el payload completo a la API (antes solo enviaba el nombre).

### B. Flujo de Edición (`/offer-studio/offer/[id]`)
*   **Nuevo Componente**: `OfferEditor` (`src/features/offer-studio/components/offer-editor.tsx`).
*   **Diseño**: En lugar de pasos bloqueantes, utiliza **Tabs** (Pestañas) para navegar libremente entre secciones:
    *   *Identidad, Detalles Específicos, Promesa, Value Stack, Economía, Reglas*.
*   **Polimorfismo Real**:
    *   Si editas un **Producto**, la pestaña "Detalles" muestra campos de stock/envío.
    *   Si editas un **Programa**, muestra campos de syllabus/llamadas.
    *   Esto soluciona el problema de "ver lo mismo en todos lados".

## 3. Actualización de Capa de Datos (`lib/api/offer.ts`)
Actualicé la función `getOffer` y `saveOffer` para mapear **todos** los campos nuevos (JSONB, polimórficos) entre el Frontend y el Backend. Antes la API solo devolvía un subconjunto básico, lo que causaba pérdida de datos al editar.

## 4. Archivos Modificados/Creados
*   `features/offer-studio/components/steps/specific-details-step.tsx` (Fix import)
*   `lib/api/offer.ts` (API completa)
*   `features/offer-studio/components/offer-wizard.tsx` (Lógica de submit)
*   `features/offer-studio/components/offer-editor.tsx` (Nuevo editor por pestañas)
*   `app/(dashboard)/offer-studio/offer/[id]/page.tsx` (Conexión al nuevo editor)

Ahora puedes ir a `Offer Studio`, crear una oferta con el Wizard, y al guardarla, serás redirigido al Editor por Pestañas donde verás exactamente los campos correspondientes a lo que creaste.