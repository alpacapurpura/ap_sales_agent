# Plan de Implementación: Activación de "Nueva Oferta" con UX Mejorada

El usuario reporta que "no sucede nada" al hacer clic en "Nueva Oferta". Esto puede deberse a que el componente no está manejando correctamente el estado de carga o la redirección. Además, para mejorar la UX y reutilizar código, implementaré un diálogo inicial que solicite el nombre de la oferta antes de crearla, evitando crear ofertas genéricas como "Nueva Oferta" automáticamente.

## Propuesta UX
En lugar de crear una oferta inmediatamente con un nombre genérico:
1.  **Diálogo Modal:** Al hacer clic en "Nueva Oferta", se abrirá un `Dialog` (componente de Shadcn UI).
2.  **Input de Nombre:** El usuario ingresará el nombre de la oferta (ej. "High Ticket Mentorship Q1").
3.  **Confirmación:** Al confirmar, se llamará a la API, se creará la oferta y *entonces* se redirigirá al editor.

## Plan Técnico

### 1. Refactorizar `OfferDashboard` (`frontend/src/components/offer-studio/offer-dashboard.tsx`)
*   Integrar el componente `Dialog` de Shadcn UI (ya instalado en el proyecto según `package.json`).
*   Añadir un estado local para controlar la visibilidad del diálogo (`isCreateDialogOpen`).
*   Añadir un estado para el nombre de la nueva oferta (`newOfferName`).
*   Modificar `handleCreateOffer` para que:
    1.  Valide que el nombre no esté vacío.
    2.  Llame a `offerApi.createOffer(newOfferName)`.
    3.  Redirija a `/offer-studio/offer/{id}`.

### 2. Verificar `OfferWizard` (`frontend/src/components/offer-studio/offer-wizard.tsx`)
*   Este componente existe pero es un prototipo "monolítico" que no se está usando actualmente.
*   **Decisión:** Por ahora, no lo integraremos como el flujo principal de *creación* rápida, ya que el usuario parece querer entrar al editor ("Resumen de la Oferta") que acabamos de arreglar. El Wizard es útil para un flujo paso a paso, pero el Dashboard actual sugiere una gestión más directa.
*   Sin embargo, tomaremos inspiración de su estructura si el usuario decide expandir el flujo más adelante.

### 3. Backend (Verificación)
*   El endpoint `POST /products/` ya espera un `ProductCreate(name=str)`. Esto es compatible con nuestra mejora de UX (enviar el nombre real desde el principio).

## Pasos de Ejecución
1.  Modificar `offer-dashboard.tsx` para importar `Dialog`, `DialogContent`, etc.
2.  Implementar el formulario dentro del diálogo.
3.  Conectar la lógica de creación al nuevo formulario.
