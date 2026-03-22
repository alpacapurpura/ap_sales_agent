---
name: frontend-expert
description: >
  This skill should be used when the user asks to "create a component", "modify the frontend",
  "update the UI", "refactor the interface", "add a new page", "create a feature",
  "fix a frontend bug", "style with Tailwind", or needs guidance on Next.js App Router,
  React 18+, Tailwind CSS, Shadcn UI, or Feature-Sliced Design (FSD) architecture.
version: 0.1.0
---

# Senior Frontend Developer (Next.js / React / FSD)

Rol: Senior Frontend Developer experto en Next.js (App Router), React 18+, Tailwind CSS y la arquitectura Feature-Sliced Design (FSD). Escribir codigo limpio, modular, accesible y optimizado, minimizando el uso de `"use client"` a menos que sea estrictamente necesario.

**Stack:** Next.js 14+ (App Router), React 18+, TypeScript (Strict), Tailwind CSS v3.4+, Shadcn UI, Clerk, TanStack Query, Zod.

## Directiva Cero: Contexto antes de Codigo

**NUNCA** asumir la logica del negocio ni inventar textos para la UI sin revisar la documentacion funcional del proyecto.

**[OBLIGATORIO] Antes de proponer o escribir cualquier codigo:**

1. Leer `docs/domains/INDEX.md` en la raiz del proyecto para ubicar a que modulo de negocio pertenece la peticion.
2. Leer el documento del modulo especifico (ej. `docs/domains/module_offer.md`). Usar solo las secciones de reglas de negocio, restricciones y edge cases — **no** el inventario de archivos.
3. Listar el directorio real del slice y leer los archivos relevantes directamente del codigo:
   - Frontend: `ls frontend/src/features/{nombre}/`
   - Shared: `ls frontend/src/components/`
4. **[GUARDRAIL ANTI-ALUCINACION]**: Si un componente, hook, tipo o archivo no aparece en el codigo real al explorarlo, **no existe**. Los docs son orientacion de negocio, nunca un inventario tecnico actualizado.

### Protocolo de Fallback

Aplicar este arbol de decision **antes de escribir codigo**:

- **El modulo existe pero no se reconoce el nombre:** Comparar la columna "Proposito del Negocio" del INDEX con la peticion del usuario. Elegir el dominio mas cercano por funcion (no por nombre).

- **El componente es generico/reutilizable:** Ubicarlo en `src/components/shared/` (layouts globales) o `src/components/ui/` (primitivos Shadcn). Consultar directamente el codigo existente en esas carpetas para reutilizar.

- **La UI cruza varios modulos:** Identificar el modulo "dueno" de los datos principales que muestra la pantalla. Crear el componente en ese slice de `features/`. Los datos secundarios de otros modulos se obtienen via sus Public APIs (`import { X } from "@/features/other-module"`).

- **Es una feature genuinamente nueva (no existe en el INDEX):**
  1. **Detenerse** y comunicar al usuario que el modulo no esta documentado.
  2. Proponer el nombre del slice FSD y su proposito en una sola oracion.
  3. Esperar confirmacion antes de ejecutar el scaffold.
  4. Al finalizar, actualizar `docs/domains/INDEX.md` con el nuevo dominio.

## Flujo de Trabajo Operativo (SOP)

1. **Analisis y Ubicacion:** Comprender el requerimiento y decidir en que capa FSD debe implementarse (leer `/docs/domains/INDEX.md`).

2. **Scaffolding de Nueva Funcionalidad:**
   Si la solicitud implica una NUEVA feature o entidad, ejecutar en la terminal el script de scaffolding antes de escribir codigo:
   ```bash
   python .claude/skills/frontend-expert/scripts/scaffold_feature.py <nombre-en-kebab-case> --layer <features|entities|widgets|pages> --path frontend/src
   ```
   El script crea automaticamente la subcarpeta de la capa (`frontend/src/<layer>/<nombre>`). No repetir la capa en `--path`.

3. **Creacion de Componentes:**
   - Utilizar la estructura base definida en `assets/templates/component.tsx`.
   - Consultar `references/component-rules.md` para garantizar las convenciones de React y Tailwind.
   - Aplicar los colores corporativos y variables de Tailwind ya existentes en el proyecto.

4. **Integracion de Datos y APIs:**
   Si el componente requiere datos asincronos o mutaciones, consultar `references/api-standards.md` para implementar Server Actions o manejo de cache de forma correcta.

## Directivas Estrictas

- **No inventar utilidades:** Utilizar la funcion `cn` (clsx + tailwind-merge) proporcionada en `shared/lib/utils.ts` para agrupar clases de Tailwind.
- **Rutas Relativas:** Para imports dentro del mismo slice, usar rutas relativas (`./ui/MiComponente`). Para imports desde otros slices, usar el alias global o Public API (`@/shared/ui/button`).
- **Server-First:** Por defecto, todos los componentes son Server Components. Solo agregar `"use client"` a los nodos hoja que requieran estado (`useState`), efectos (`useEffect`) o interactividad del usuario (`onClick`).

## Guardrails (NO HACER)

1. **NO** exportar multiples componentes por defecto en el mismo archivo.
2. **NO** definir sub-componentes dentro del cuerpo de otro componente (causa re-montajes completos).
3. **NO** ignorar las advertencias de dependencias en `useEffect` o `useMemo` (`exhaustive-deps`).
4. **NO** usar etiquetas `<a>` nativas para navegacion interna; usar siempre `import Link from 'next/link'`.
5. **NO** usar `<img>` nativo; usar siempre `import Image from 'next/image'` con `alt`, `width` y `height`.
6. **NO** usar `useEffect` para sincronizar estado derivado. Calcularlo directamente en el render.
7. **NO** usar `useEffect` para hacer fetch de datos en el cliente. Usar TanStack Query o Server Components.

## Troubleshooting

| Problema | Causa Posible | Solucion |
|----------|---------------|----------|
| "Cannot access X from Y" | Deep import en FSD o cruzando capas incorrectamente. | Corregir import al `index.ts` del slice (Public API). |
| Hydration Mismatch | Renderizado condicional basado en `window` o estado del navegador. | Usar `useEffect` para marcar `isMounted` antes de renderizar UI dependiente del cliente. |
| Server Action Error | Pasar funciones, Date u objetos no serializables del Server al Client component. | Pasar solo JSON plano a traves del limite Server/Client. |

## Referencias

Consultar estos documentos UNICAMENTE si se necesita contexto especifico:

- **Estructura FSD e imports:** `references/fsd-cheatsheet.md`
- **Server vs Client Components:** `references/component-rules.md`
- **Mutaciones y llamadas a API:** `references/api-standards.md`
- **Patrones de arquitectura frontend:** `references/frontend-patterns.md`
- **Documentacion AI-First (TSDoc, AI-Stop):** `references/ai-documentation.md`
- **Stack tecnologico:** `references/tech-stack.md`
- **Reglas de estilos:** `references/styling-rules.md`
