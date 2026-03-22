---
type: "reference"
domain: "frontend-components"
description: "Reglas estrictas y estandares arquitectonicos para la creacion y modificacion de componentes React en Next.js App Router."
frameworks: ["React 18+", "Next.js App Router", "Tailwind CSS"]
---

# Estandares de Componentes Frontend (Next.js / React)

Este documento contiene las reglas inquebrantables para el desarrollo de componentes. Aplicar estas reglas sistematicamente sin excepciones a menos que el usuario indique explicitamente lo contrario.

## 1. Estrategia de Renderizado (Server Components vs Client Component)

* **Server by Default:** Asumir que TODO componente es un React Server Component (RSC). NO usar la directiva `"use client"` a menos que sea inevitable.
* **Cuando usar `"use client"`:**
  * Si el componente necesita usar Hooks de React (`useState`, `useEffect`, `useReducer`, `useRef`).
  * Si el componente maneja interactividad del navegador (listeners de eventos como `onClick`, `onChange`).
  * Si usa APIs exclusivas del navegador (window, document, localStorage).
* **El patron "Client Boundary":** Si un componente padre grande es un RSC pero un pequeno boton necesita estado, aislar el boton en su propio archivo con `"use client"` e importarlo en el RSC. NO contaminar el archivo padre entero.

## 2. Tipado y Estructura del Componente (TypeScript)
Todo componente debe estar fuertemente tipado.

- **Interfaces explicitas:** Definir siempre una `interface` o `type` para las props, nombrada como `[NombreComponente]Props`.
- **Prohibido el uso de `any` o `unknown`:** Si no se conoce el tipo, usar genericos (`<T>`) o definir la estructura parcial.
- **Funciones de Flecha:** Usar `const ComponentName = ({ prop1 }: ComponentNameProps) => { ... }`.
- **Desestructuracion:** Desestructurar las props directamente en la firma de la funcion.

## 3. Estilos y Clases (Tailwind CSS)
Mantener un sistema de diseno consistente basado en utilidades.

- **Cero Estilos en Linea:** Totalmente prohibido usar el atributo `style={{...}}`. Usar exclusivamente clases de Tailwind.
- **Clases Condicionales y Dinamicas:** Para unir clases o manejar estados dinamicos, usar SIEMPRE la funcion utilitaria `cn()` (clsx + twMerge).
  - *Correcto:* `className={cn("base-class", isActive && "active-class", className)}`
  - *Incorrecto:* `` className={`base-class ${isActive ? 'active-class' : ''} ${className}`} ``
- **Reutilizacion de UI:** Antes de crear un boton, input, modal o tarjeta desde cero con HTML puro, VERIFICAR si ya existe en `src/components/ui/` (Componentes Shadcn).

## 4. Estado y Efectos (Hooks)
La gestion del estado debe ser predecible y evitar re-renderizados innecesarios.

* **Regla Vercel/React 18:** NO usar `useEffect` para sincronizar estado derivado.
* *Incorrecto:*
```tsx
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const [fullName, setFullName] = useState('');
useEffect(() => setFullName(`${firstName} ${lastName}`), [firstName, lastName]);
```
* *Correcto:*
```tsx
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const fullName = `${firstName} ${lastName}`; // Se calcula al momento de renderizar
```

## 5. Manejo de Datos y Asincronia
- **Data Fetching en RSC:** Las peticiones a base de datos o APIs deben hacerse idealmente en Server Components usando `await` directo en el componente.
- **Loading States:** Usar `Suspense` con componentes de Skeleton (`src/components/ui/skeleton.tsx`) para envolver Server Components asincronos en lugar de manejar estados `isLoading` manuales.

## 6. Anti-Patrones Estrictos (GUARDRAILS)

1. **NO** exportar multiples componentes por defecto en el mismo archivo.
2. **NO** definir sub-componentes dentro del cuerpo de otro componente (causa re-montajes completos en cada render). Definirlos fuera o en otro archivo.
3. **NO** ignorar las advertencias de dependencias en `useEffect` o `useMemo` (eslint: `exhaustive-deps`).
4. **NO** usar etiquetas `<a>` nativas para navegacion interna; usar SIEMPRE `import Link from 'next/link'`.
5. **NO** usar `<img>` nativo; usar SIEMPRE `import Image from 'next/image'` con sus respectivos `alt`, `width` y `height` (o `fill`).
