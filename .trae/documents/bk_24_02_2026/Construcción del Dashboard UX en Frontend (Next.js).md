# Reestructuración Frontend y Dashboard de Conocimiento

Entendido. He verificado que tu proyecto Frontend (`/frontend`) **SÍ** tiene una implementación funcional de Next.js con Shadcn/UI, pero actualmente la estructura está en la raíz (`app`, `components`, `lib`) en lugar de estar encapsulada en `src/`. Esto no es un error crítico, pero moverlo a `src/` (como solicitaste) mejora la limpieza y organización.

## 🛠️ Plan de Ejecución

### 1. Refactorización Estructural (Standardización)
Moveré las carpetas principales dentro de `frontend/src` para cumplir con las mejores prácticas modernas de Next.js y aislar el código fuente de los archivos de configuración.
*   **Acción:** Mover `app/`, `components/`, `lib/` -> `src/`.
*   **Ajuste:** Actualizar `tsconfig.json` y `tailwind.config.ts` para que apunten a los nuevos paths (`@/*` -> `src/*`).

### 2. Implementación del "Knowledge Hub" (Dashboard UX)
Voy a trabajar sobre la estructura existente en `app/(dashboard)/knowledge/page.tsx` para transformarla en el centro de control que pediste.

**Componentes Nuevos (`src/components/knowledge`):**
1.  **`KnowledgeTabs`:** El contenedor principal que orquesta las vistas.
2.  **`SafetyLayerManager`:** El componente estrella.
    *   **Selector de Ámbito:** "🏢 Nivel Marca" vs "🚀 Nivel Producto".
    *   **Smart Form:** Campos con iconos, descripciones claras ("hints") y validación visual.
    *   **Tabla de Reglas:** Lista interactiva con filtros por ámbito.
3.  **`DocumentsManager`:** (Reutilizando lógica existente si la hay, o placeholder estructurado).

**Integración API (`src/lib/api/knowledge.ts`):**
*   Crearé un cliente tipado para comunicarnos con el Backend FastAPI (endpoints de `SensitiveData`).

### 3. Verificación
*   Me aseguraré de que la navegación lateral (`app-sidebar.tsx`) apunte correctamente a esta nueva sección.
*   Validaré que los estilos de Tailwind se apliquen correctamente tras la mudanza a `src/`.

Este enfoque respeta tu trabajo previo pero lo eleva al nivel de UX de Hostinger/Cloudflare que buscas.
