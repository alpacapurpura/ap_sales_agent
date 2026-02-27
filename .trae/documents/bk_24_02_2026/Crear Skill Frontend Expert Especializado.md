Voy a crear el skill `frontend-expert` siguiendo las mejores prácticas y tu stack tecnológico específico.

### Pasos para crear un Skill en Trae (Resumen del Tutorial)
Según la documentación oficial, el proceso consta de 3 pasos clave:
1.  **Definición**: Crear una carpeta `.trae/skills/<nombre-skill>`.
2.  **Instrucción**: Crear un archivo `SKILL.md` dentro con el frontmatter (nombre, descripción) y las instrucciones detalladas.
3.  **Activación**: El skill se carga dinámicamente cuando el usuario lo solicita o cuando el contexto lo requiere (gracias a la descripción en el frontmatter).

### Plan de Implementación
Crearé el archivo `.trae/skills/frontend-expert/SKILL.md` con las siguientes características especializadas para tu proyecto:

1.  **Stack Tecnológico Definido**:
    *   **Core**: Next.js 14 (App Router), TypeScript (Strict), React 18.
    *   **UI**: Tailwind CSS, Shadcn UI (Radix), Lucide Icons.
    *   **Estado/Data**: TanStack Query, Server Actions, Zod.
    *   **Testing**: Vitest, React Testing Library.

2.  **Reglas de Oro (Clean Code & Seguridad)**:
    *   **No-Destrucción**: Instrucción explícita de *leer antes de escribir* y *analizar dependencias*.
    *   **Atomicidad**: Crear componentes pequeños y reutilizables (Atomic Design).
    *   **Server-First**: Priorizar Server Components por defecto.
    *   **Mobile-First**: Clases de Tailwind base para móvil, `md:`/`lg:` para escritorio.

3.  **Estructura del Skill**:
    *   **Frontmatter**: Descripción optimizada para que la IA sepa cuándo invocarlo.
    *   **Sección "Critical Protocol"**: Pasos obligatorios de análisis de código existente para evitar regresiones.
    *   **Guías de Estilo**: Uso de `cn()` (clsx + tailwind-merge), manejo de errores con `try/catch` en Server Actions, etc.

### Archivo a crear
`home/chris/AISALESHT/.trae/skills/frontend-expert/SKILL.md`
