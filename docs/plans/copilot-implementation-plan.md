# Copilot UI - Resumen de Aprendizaje y Plan de Implementación

Este documento sintetiza las decisiones de arquitectura de interfaz de usuario y flujo de datos para la implementación del **Copilot Permanente Multi-Contexto** en Visionarias, con enfoque inicial en el *Brand Studio*.

## 1. Resumen de Decisiones (UX/UI)

Tras iterar sobre diferentes prototipos interactivos, se han definido los siguientes pilares para la experiencia del usuario:

### 1.1. Arquitectura de Layout: "Panel Desplegable que Empuja" (Alternativa 2)
*   **Persistencia Global:** El Copilot no pertenece a una página específica, vive en el `RootLayout` (o un layout envolvente que cubra todas las rutas internas del Dashboard).
*   **Estado Colapsado:** Por defecto, reside en el borde derecho como un rail sutil de iconos (60px).
*   **Estado Expandido:** Al abrirse, ocupa ~350px/400px y **empuja** el contenido principal (Main Content y Formularios) hacia la izquierda ajustando sus márgenes. No es un overlay que oscurece o tapa información.
*   **Armonía con Formularios (Sheets):** Los formularios de edición mantienen su naturaleza de Sidebars (Shadcn `Sheet`). Cuando un formulario se abre, se ancla *adyacente* al Copilot (si está abierto), permitiendo al usuario ver el Live Document, el Formulario y el Chat simultáneamente.

### 1.2. Interacción "Hover & Chat" (Multi-Contexto)
*   **Micro-Interacción:** Cada input, textarea o sección editable está envuelto en un componente (ej. `<WithCopilot>`) que revela un botón flotante ("✨ + a Copilot") al hacer hover o focus.
*   **Selección Granular:** El usuario puede agregar uno o **múltiples** campos al contexto de la conversación.
*   **Context Chips:** Los campos seleccionados se visualizan como "chips" (etiquetas) en la parte superior del input del chat de la IA.
*   **Awareness Automático:** Incluso si el usuario no selecciona un campo específico, el Copilot **sabe en qué página y en qué formulario exacto (ej. "Edición de Posicionamiento") se encuentra el usuario en ese momento.**

### 1.3. Server-Driven UI (Ida y Vuelta)
*   **Mutación Directa:** La IA no solo da sugerencias en texto. Si el usuario pide modificar campos, el backend responde con los nuevos valores y el frontend actualiza los inputs en tiempo real.
*   **Feedback Visual:** Cuando la IA actualiza un campo del formulario, este realiza una sutil animación (highlight morado) para que el usuario localice rápidamente el cambio.
*   **Navegación Asistida:** El chat puede renderizar botones funcionales (ej. "Ir al Producto A") devolviendo componentes UI desde el backend.

---

## 2. Plan de Implementación Técnica

La implementación abarcará 3 capas principales: Frontend State (Zustand), Frontend UI (Next.js) y Backend/IA (FastAPI + LangGraph).

### Fase 1: Arquitectura de Estado Global (Frontend)

El corazón del sistema es un Store de Zustand que persista entre navegaciones y rastree el contexto exacto.

1.  **Crear `useCopilotStore`:**
    *   `isOpen`: Estado de expansión del panel.
    *   `currentRoute`: URL actual (sincronizada vía `usePathname`).
    *   `activeForm`: ID o nombre del formulario abierto actualmente (ej. `brand_positioning_sheet`).
    *   `selectedFields`: Map o Array de objetos `{ fieldId, label, currentValue }`.
    *   `messages`: Historial del chat de la sesión.
    *   **Acciones:** `toggle()`, `addContext()`, `removeContext()`, `setActiveForm()`, `clearContext()`.

2.  **Rastreador de Contexto (Context Tracker):**
    *   Implementar un hook o componente en el RootLayout que escuche los cambios de ruta y actualice el store automáticamente.

### Fase 2: Implementación de UI (Next.js + Shadcn)

1.  **Refactor del Root Layout:**
    *   Ajustar el layout principal para soportar el contenedor derecho dinámico (`padding-right` transicional).
    *   Crear el componente `<CopilotSidebar />` global.

2.  **Adaptación de Shadcn `Sheet`:**
    *   Modificar la configuración o estilos de los `Sheets` actuales (como `EditSheetManager` en Brand Studio) para que su posición `right` o transformación sea relativa al ancho del Copilot, evitando que el Copilot quede tapado.

3.  **Componente Wrapper `<WithCopilot>`:**
    *   Crear un High-Order Component (o wrapper estándar) que reciba: `fieldId`, `label`, `value`.
    *   Implementar la lógica de hover y el botón "✨ + a Copilot".
    *   Al hacer clic, disparar `addContext` en Zustand y expandir el Copilot.
    *   Implementar el hook que escucha si este `fieldId` fue actualizado por la IA para disparar la animación CSS de `highlight`.

### Fase 3: Integración Backend y LangGraph (FastAPI)

1.  **Enriquecer el Payload de Entrada:**
    *   Actualizar el endpoint de chat (ej. `/api/v1/copilot/chat`) para recibir el contexto rico:
        ```json
        {
          "message": "Hazlo más agresivo",
          "context": {
            "url": "/brand-studio",
            "active_form": "positioning",
            "targeted_fields": [
              {"id": "uvp_text", "label": "Propuesta de Valor", "value": "..."}
            ]
          }
        }
        ```

2.  **System Prompt Dinámico (LangGraph):**
    *   Actualizar el nodo inicial del orquestador para inyectar este contexto en el System Prompt.
    *   *Prompt logic:* "El usuario está en la página X, viendo el formulario Y. Ha seleccionado los campos Z. Si te pide cambios, DEBES usar la herramienta de actualización para esos campos específicos."

3.  **Tool Calling (Herramientas de Mutación):**
    *   Crear una tool `@tool def update_ui_fields(fields: List[Dict[str, str]])` en LangGraph.
    *   Esta tool no necesariamente guarda en DB inmediatamente (ya que el usuario debe darle a "Guardar" en el formulario del frontend), sino que emite una respuesta estructurada.

4.  **Respuesta Estructurada (Server-Driven):**
    *   Asegurar que la respuesta de FastAPI devuelva el texto del asistente y un array de mutaciones:
        ```json
        {
          "reply": "He actualizado la propuesta de valor.",
          "mutations": [
            {"fieldId": "uvp_text", "newValue": "Nueva propuesta..."}
          ]
        }
        ```

### Fase 4: Sincronización de Ida y Vuelta (El "Bucle")

1.  **Procesamiento de Mutaciones en Frontend:**
    *   Al recibir la respuesta de FastAPI, el componente de Chat analiza si hay `mutations`.
    *   Si las hay, actualiza el valor de los inputs en el DOM o mediante el estado de **React Hook Form** (ej. usando `setValue('uvp_text', 'Nueva propuesta...')`).
    *   El Wrapper `<WithCopilot>` detecta el cambio programático y dispara el resplandor visual.

2.  **Testing y Refinamiento:**
    *   Probar el flujo completo en la sección de "Origen" y "Posicionamiento" del Brand Studio.
    *   Asegurar que al cambiar de ruta, el contexto del chat se actualice pero el historial no se pierda.

---

### Siguientes pasos
Para iniciar la implementación en la próxima conversación, te sugiero que el primer prompt sea:
*"Iniciemos el Plan Copilot Fase 1 y 2: Crea el Zustand Store global y ajustemos el Root Layout para acomodar el panel derecho colapsable."*