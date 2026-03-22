---
type: "reference"
domain: "frontend-components"
description: "Reglas estrictas y estándares arquitectónicos para la creación y modificación de componentes React en Next.js App Router."
frameworks: ["React 18+", "Next.js App Router", "Tailwind CSS"]
---

# 📜 Estándares de Componentes Frontend (Next.js / React)
Este documento contiene las reglas inquebrantables para el desarrollo de componentes. **[INSTRUCCIÓN IA]:** Aplica estas reglas sistemáticamente sin excepciones a menos que el usuario indique explícitamente lo contrario.

## 1. Estrategia de Renderizado (Server Components vs Client Component)

* **Server by Default:** Asume que TODO componente es un React Server Component (RSC). NO uses la directiva `"use client"` a menos que sea inevitable.  
* **¿Cuándo usar `"use client"`?:**  
  * Si el componente necesita usar Hooks de React (`useState`, `useEffect`, `useReducer`, `useRef`).  
  * Si el componente maneja interactividad del navegador (listeners de eventos como `onClick`, `onChange`).  
  * Si usa APIs exclusivas del navegador (window, document, localStorage).  
* **El patrón "Client Boundary":** Si un componente padre grande es un RSC pero un pequeño botón necesita estado, aísla el botón en su propio archivo con `"use client"` e impórtalo en el RSC. NO contamines el archivo padre entero.


## 2. Tipado y Estructura del Componente (TypeScript)
Todo componente debe estar fuertemente tipado.

- **Interfaces explícitas:** Define siempre una `interface` o `type` para las props, nombrada como `[NombreComponente]Props`.
- **Prohibido el uso de `any` o `unknown`:** Si no conoces el tipo, usa genéricos (`<T>`) o define la estructura parcial.
- **Funciones de Flecha:** Usa `const ComponentName = ({ prop1 }: ComponentNameProps) => { ... }`.
- **Desestructuración:** Desestructura las props directamente en la firma de la función.

## 3. Estilos y Clases (Tailwind CSS)
Mantenemos un sistema de diseño consistente basado en utilidades.

- **Cero Estilos en Línea:** Totalmente prohibido usar el atributo `style={{...}}`. Usa exclusivamente clases de Tailwind.
- **Clases Condicionales y Dinámicas:** Para unir clases o manejar estados dinámicos, usa SIEMPRE la función utilitaria `cn()` (clsx + twMerge).
  - *Correcto:* `className={cn("base-class", isActive && "active-class", className)}`
  - *Incorrecto:* ``className={`base-class ${isActive ? 'active-class' : ''} ${className}`}``
- **Reutilización de UI:** Antes de crear un botón, input, modal o tarjeta desde cero con HTML puro, VERIFICA si ya existe en `src/components/ui/` (Componentes Shadcn).

## 4. Estado y Efectos (Hooks)
La gestión del estado debe ser predecible y evitar re-renderizados innecesarios.

* **Regla Vercel/React 18:** NO uses `useEffect` para sincronizar estado derivado.  
* *Incorrecto:*
```
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const [fullName, setFullName] = useState('');
useEffect(() => setFullName(`${firstName} ${lastName}`), [firstName, lastName]);
```
*  *Correcto:*
```
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const fullName = `${firstName} ${lastName}`; // Se calcula al momento de renderizar
```

## 5. Manejo de Datos y Asincronía
- **Data Fetching en RSC:** Las peticiones a base de datos o APIs deben hacerse idealmente en Server Components usando `await` directo en el componente.
- **Loading States:** Usa `Suspense` con componentes de Skeleton (`src/components/ui/skeleton.tsx`) para envolver Server Components asíncronos en lugar de manejar estados `isLoading` manuales.

## 🚫 6. Anti-Patrones Estrictos (GUARDRAILS)
**[INSTRUCCIÓN IA]: Bajo ninguna circunstancia debes cometer estos errores en el código generado:**

1. **NO** exportar múltiples componentes por defecto en el mismo archivo.
2. **NO** definir sub-componentes dentro del cuerpo de otro componente (causa re-montajes completos en cada render). Defínelos fuera o en otro archivo.
3. **NO** ignorar las advertencias de dependencias en `useEffect` o `useMemo` (eslint: `exhaustive-deps`).
4. **NO** usar etiquetas `<a>` nativas para navegación interna; usa SIEMPRE `import Link from 'next/link'`.
5. **NO** usar `<img>` nativo; usa SIEMPRE `import Image from 'next/image'` con sus respectivos `alt`, `width` y `height` (o `fill`).