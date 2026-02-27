# Tasks

- [x] Task 1: Setup y Utilidades Base
    - [x] SubTask 1.1: Verificar que `frontend/src/lib/utils.ts` exporte correctamente la función `cn`.
    - [x] SubTask 1.2: Añadir utilidades de layout (`.v-stack`, `.h-stack`, `.center`, `.spacer`) en `frontend/src/app/globals.css` usando `@layer utilities` o plugin de Tailwind.

- [x] Task 2: Refactorización de Componentes Críticos (Chat y Listas)
    - [x] SubTask 2.1: Refactorizar `sales-inbox-sheet.tsx`. Implementar `cva` para las burbujas de chat (mensajes enviados/recibidos) y reemplazar concatenación manual por `cn()`.
    - [x] SubTask 2.2: Refactorizar `team-list.tsx`. Reemplazar lógica de strings para `bg-green-500`/`bg-amber-500` por `cn()`.
    - [x] SubTask 2.3: Refactorizar `PipelineView.tsx`. Corregir la asignación de colores de etapa (`${stage.color}`) asegurando que se mezcle correctamente con las clases base usando `cn()`.

- [x] Task 3: Barrido General de Concatenación Manual
    - [x] SubTask 3.1: Buscar en todo `frontend/src` patrones de regex como `className=\{.*?\$\{` y refactorizar a `cn()` donde aplique (priorizando componentes de UI compartidos).
    - [x] SubTask 3.2: Verificar que no queden conflictos de estilos obvios (ej. `p-4 p-2` resueltos por `tailwind-merge`).

# Task Dependencies
- Task 2 y Task 3 dependen de Task 1 (disponibilidad de `cn` y utilidades).
