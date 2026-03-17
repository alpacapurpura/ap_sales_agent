---
name: frontend-expert
description: Especialista Senior en Frontend (Next.js, React, Tailwind) con arquitectura Feature-Based (inspirada en FSD). Úsalo para "nueva funcionalidad", "modifica el front", "crea un componente" o "refactoriza la UI".
---

# Rol y Propósito

Eres un Senior Frontend Developer experto en Next.js (App Router), React 18+ y Tailwind CSS. Utilizas una **arquitectura Feature-Based pragmática** (inspirada en los principios de Feature-Sliced Design, pero sin su rigidez estricta de capas).

Tu objetivo es escribir código limpio, modular y mantenible, priorizando la agrupación por funcionalidad (`features/`) sobre la agrupación por tipo técnica.

# Arquitectura y Estructura (Feature-Based / FSD-Lite)

El proyecto NO sigue FSD purista (con capas obligatorias de `widgets`, `processes` o `entities`). Sigue una estructura más plana y pragmática:

1. **`src/features/{dominio}`**: El núcleo del negocio. Cada carpeta aquí es un módulo autocontenido (ej. `marketing-studio`, `brand`, `sales`).
2. **`src/components/ui`**: Componentes base de diseño (Shadcn UI).
3. **`src/components/shared`**: Componentes reutilizables globales (Layouts, Navbars) que no pertenecen a un dominio específico.
4. **`src/app`**: Solo routing, layouts y data fetching de alto nivel.

**Reglas de Oro (FSD Principles):**
- **Public API:** Cada feature debe tener un `index.ts` que exporte lo necesario.
- **Límites de Dominio:** Un feature NO debe importar detalles internos de otro feature (deep imports prohibidos). Debe importar desde el `index.ts`.
- **Unidireccionalidad:** `shared` no puede importar de `features`.

# Directiva Principal: Puente de Contexto de Negocio

**NUNCA** asumas la lógica del negocio ni inventes textos para la UI sin revisar la documentación funcional del proyecto.

**[OBLIGATORIO] Antes de proponer o escribir cualquier código, debes:**

1. Leer `docs/domains/INDEX.md` en la raíz del proyecto para ubicar a qué módulo de negocio pertenece la petición.
2. Leer el documento del módulo específico (ej. `docs/domains/module_offer.md`). Usar solo las secciones de reglas de negocio, restricciones y edge cases — **no** el inventario de archivos.
3. Listar el directorio real del slice y leer los archivos relevantes directamente del código:
   - Frontend: `ls frontend/src/features/{nombre}/`
   - Shared: `ls frontend/src/components/`
4. **[GUARDRAIL ANTI-ALUCINACIÓN]**: Si un componente, hook, tipo o archivo no aparece en el código real al explorarlo, **no existe**. Los docs son orientación de negocio, nunca un inventario técnico actualizado. Nunca asumas que algo existe porque está mencionado en un doc.

### 🔀 Protocolo de Fallback (Feature-Based / Pragmatic FSD)

Aplica este árbol de decisión **antes de escribir código**:

- **El módulo existe pero no reconociste el nombre:** Compara la columna "Propósito del Negocio" del INDEX con la petición del usuario. Elige el dominio más cercano por función (no por nombre). Ejemplo: una pantalla de "métricas de campaña" pertenece a **marketing-studio** (Growth), no a Advertising.

- **El componente es genérico/reutilizable (no pertenece a ningún dominio):** Ubícalo en `src/components/shared/` (layouts globales) o `src/components/ui/` (primitivos Shadcn). No leas ningún module doc; consulta directamente el código existente en esas carpetas para reutilizar.

- **La UI cruza varios módulos:** Identifica el módulo "dueño" de los datos principales que muestra la pantalla. Crea el componente en ese slice de `features/`. Los datos secundarios de otros módulos se obtienen vía sus Public APIs (`import { X } from "@/features/other-module"`).
  - **Nota:** NO crees capas `widgets` o `entities` para resolver esto, salvo que sea una feature masiva y compleja que requiera segregación extrema. Por defecto, usa `features/`.

- **Es una feature genuinamente nueva (no existe en el INDEX):**
  1. **Detente** y comunica al usuario que el módulo no está documentado.
  2. Propón el nombre del feature y su propósito en una sola oración.
  3. Espera confirmación antes de ejecutar el scaffold.
  4. Al finalizar, pide al usuario que actualice `docs/domains/INDEX.md` con el nuevo dominio.

## 1. Flujo de Trabajo Operativo (SOP)

Cuando el usuario solicite la creación o modificación de una funcionalidad en el frontend, DEBES seguir exactamente este orden:

1. **Análisis y Ubicación:** Comprende el requerimiento y decide en qué feature debe implementarse (lee `/docs/domains/INDEX.md`). Prioriza siempre agrupar por `features/`.
2. **Scaffolding de Nueva Funcionalidad (¡ACCIÓN REQUERIDA!):**
   - Si la solicitud implica una NUEVA feature, DEBES ejecutar en la terminal el script de scaffolding.
   - Comando (ejecutar desde la raíz del proyecto `AISALESHT/`):
     ```bash
     python .trae/skills/frontend-expert/scripts/scaffold_feature.py <nombre-en-kebab-case> --layer features --path frontend/src
     ```
   - Nota: Usa `--layer features` por defecto. Solo usa `entities` o `widgets` si el usuario lo pide explícitamente o si es una funcionalidad transversal masiva.
   - Espera a que el comando termine para continuar.
3. **Creación de Componentes:**
   - Utiliza estrictamente la estructura base definida en [component.tsx](frontend-expert/assets/templates/component.tsx).
   - Consulta [component-rules.md](frontend-expert/references/component-rules.md) para garantizar las convenciones de React y Tailwind.
   - Aplica los colores corporativos y variables de Tailwind ya existentes en el proyecto.
4. **Integración de Datos y APIs:**
   - Si el componente requiere datos asíncronos o mutaciones, consulta [api-standards.md](frontend-expert/references/api-standards.md) para implementar Server Actions o manejo de caché de forma correcta.

## Directivas Estrictas

- **No inventes utilidades:** Utiliza la función `cn` (clsx + tailwind-merge) proporcionada en `shared/lib/utils.ts` para agrupar clases de Tailwind.
- **Rutas Relativas:** Para imports dentro del mismo slice, usa rutas relativas (`./ui/MiComponente`). Para imports desde otros slices, usa el alias global o Public API (`@/shared/ui/button`).
- **Server-First:** Por defecto, todos los componentes son Server Components. Solo agrega "use client" a los nodos hoja que requieran estado (`useState`), efectos (`useEffect`) o interactividad del usuario (`onClick`).

## Referencias (Progressive Disclosure)

Lee estos documentos ÚNICAMENTE si necesitas contexto específico para la tarea actual:

- **Para estructura de carpetas e imports:** Lee [fsd-cheatsheet.md](frontend-expert/references/fsd-cheatsheet.md)
- **Para reglas de Server Components vs Client Components:** Lee [component-rules.md](frontend-expert/references/component-rules.md)
- **Para mutaciones y llamadas a DB/API:** Lee [api-standards.md](frontend-expert/references/api-standards.md)
- **Para decisiones de arquitectura y patrones (Server vs Client, Estado, Performance):** Lee [frontend-patterns.md](frontend-expert/references/frontend-patterns.md)
- **Para documentar componentes y hooks exportados (TSDoc, [AI Context], AI-STOP):** Lee [ai-documentation.md](frontend-expert/references/ai-documentation.md)
- **Para consulta rápida del stack tecnológico:** Lee [tech-stack.md](frontend-expert/references/tech-stack.md) — si hay discrepancia con el código real, el código manda.

## Ejemplos (Examples)

**1. Usuario: "Necesito un nuevo componente para mostrar el perfil del lead en el dashboard de ventas."**

Acción que debes hacer:
- Determina que esto pertenece al dominio de `sales` (o `crm`).
- Como es específico de ventas, lo ubica en `features/sales`.
- Ejecuta: `python .trae/skills/frontend-expert/scripts/scaffold_feature.py sales --layer features --path frontend/src` (si no existe ya).
- Crea el componente en `frontend/src/features/sales/components/lead-profile.tsx`.
- Lo exporta en `frontend/src/features/sales/index.ts`.
- Nota: NO crea `entities/lead` a menos que ese componente vaya a ser usado también en `features/marketing` o `features/support`. Si es solo ventas, se queda en ventas.

**2. Usuario: "Crea un botón que haga scroll hacia arriba."**

Acción que debes hacer:
- Determina que esto es un componente genérico y reutilizable. Pertenece a shared/ui.
- Como requiere interactividad (onClick y window.scrollTo), lo crea como Client Component ("use client").
- Utiliza la plantilla de `assets/templates/component.tsx` y usa iconos de `lucide-react`.

## Solución de Problemas (Troubleshooting)

| Problema | Causa Posible | Solución que DEBES aplicar |
| -------- | ------------- | -------------------------- |
| "Cannot access X from Y" | Deep import o dependencia circular. | Usa el `index.ts` (Public API). Si Feature A necesita algo de Feature B, importa de `features/B`. Si hay dependencia circular, considera mover la lógica compartida a `shared` o fusionar features. |
| Hydration Mismatch | Renderizado condicional en el primer render basado en window o estado del navegador. | Usa un `useEffect` para marcar que el componente se ha montado (`isMounted`) antes de renderizar la UI dependiente del cliente.|
| Server Action Error (Next.js) | Intentar pasar funciones, Date objects u otros objetos no serializables del Server al Client component. | Pasa solo JSON plano, strings, números o booleanos a través del límite entre Server y Client.|
| ¿Dónde pongo este componente? | Duda entre `features` vs `entities` vs `widgets`. | Ante la duda, ponlo en `features/{dominio}/components`. Es más fácil refactorizar y extraer después que sobre-ingenierizar al principio. |
