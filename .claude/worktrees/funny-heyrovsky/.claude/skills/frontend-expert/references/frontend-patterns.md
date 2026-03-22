---
name: frontend-patterns
description: Patrones de diseno frontend autorizados para Next.js (App Router), React y FSD.
---

# Patrones de Diseno Frontend (Guia Autorizada)

Este documento define los patrones de arquitectura y diseno frontend obligatorios para el desarrollo en Visionarias Brain. Optimizados para **Next.js 14+ (App Router)**, **React 18/19** y **Feature-Sliced Design (FSD)**.

## 1. Arquitectura de Componentes (App Router)

### 1.1. Server Components por Defecto ("Server-First")
**Principio:** Todo componente es un Server Component (RSC) a menos que requiera interactividad especifica.
**Beneficio:** Reduccion drastica del bundle size, acceso directo a backend/BD, seguridad mejorada.

**Patron Correcto:**
```tsx
// entities/user/ui/user-card.tsx (Server Component)
import { formatDate } from '@/shared/lib/date'

export async function UserCard({ userId }: { userId: string }) {
  const user = await fetchUser(userId)
  return (
    <div className="card">
      <h1>{user.name}</h1>
      <p>Joined: {formatDate(user.createdAt)}</p>
      <FollowButton userId={userId} /> {/* Slot para interactividad */}
    </div>
  )
}
```

### 1.2. Patron de Composicion ("The Hole Pattern")
**Problema:** Importar un Server Component dentro de un archivo marcado con `'use client'` lo convierte implicitamente en un Client Module.
**Solucion:** Pasar los Server Components como `children` o `props` (slots) al Client Component.

```tsx
// Client Wrapper
'use client'
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return <Context.Provider>{children}</Context.Provider>
}

// app/layout.tsx (Server Component)
import { ThemeProvider } from '@/features/theme'
import { Navigation } from '@/widgets/navigation'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <ThemeProvider>
          <Navigation /> {/* Server Component renderizado en servidor */}
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

## 2. Gestion de Estado (State Management)

### 2.1. URL como Fuente de Verdad (URL State)
**Contexto:** Filtros, paginacion, busquedas, modales compartibles.
**Regla:** Si el estado debe sobrevivir a un refresh o ser compartible, **DEBE** estar en la URL.
**Herramienta:** `nuqs` (recomendado) o `useSearchParams`.

### 2.2. Server State (React Query) vs useEffect
**Regla:** **PROHIBIDO** usar `useEffect` para hacer fetch de datos en el cliente.
**Solucion:**
1. **Preferido:** Fetch en Server Component y pasar datos como prop inicial.
2. **Cliente (Polling/Mutaciones):** Usar TanStack Query.

```tsx
// Hydration Boundary
// features/offer/ui/offer-list.tsx (Server Component)
import { HydrationBoundary, dehydrate, QueryClient } from '@tanstack/react-query'
import { getOffers } from '../api/get-offers'
import { OfferListClient } from './offer-list-client'

export async function OfferList() {
  const queryClient = new QueryClient()
  await queryClient.prefetchQuery({ queryKey: ['offers'], queryFn: getOffers })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <OfferListClient />
    </HydrationBoundary>
  )
}
```

### 2.3. Estado Global UI (Zustand)
**Uso:** Solo para estado global de UI (Sidebar abierto/cerrado, Toast notifications). No para datos de negocio.

## 3. Patrones de Componentes Reutilizables

### 3.1. Componentes Polimorficos (asChild)
Usar `Slot` de Radix UI (patron `asChild`).

```tsx
import { Slot } from '@radix-ui/react-slot'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
}

export function Button({ asChild, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button"
  return <Comp {...props} />
}
```

### 3.2. Compound Components
Componentes complejos con sub-partes que comparten estado implicito.

```tsx
export function Card({ children }: { children: React.ReactNode }) {
  return <div className="card-root">{children}</div>
}

Card.Header = function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="card-header">{children}</div>
}
```

## 4. Patrones de Formularios y Mutaciones

### 4.1. Server Actions + Zod
Las mutaciones deben ser Server Actions validadas con Zod.

```tsx
// features/auth/actions/login.ts
'use server'
import { z } from 'zod'

const schema = z.object({ email: z.string().email() })

export async function loginAction(prevState: any, formData: FormData) {
  const validated = schema.safeParse(Object.fromEntries(formData))
  if (!validated.success) return { errors: validated.error.flatten().fieldErrors }
  // Logica de backend...
}
```

## 5. Optimizacion y Performance

### 5.1. Optimistic UI
Feedback instantaneo al usuario antes de que el servidor responda. Usar `useOptimistic`.

### 5.2. Dynamic Imports (Lazy Loading)
Componentes pesados (Graficos, Mapas, Editores) que no son visibles inicialmente.

```tsx
const HeavyChart = dynamic(() => import('./heavy-chart'), {
  loading: () => <Skeleton className="h-64" />,
  ssr: false
})
```

## 6. Matriz de Decision Tecnica

| Escenario | Solucion Recomendada | Por que? |
|-----------|---------------------|----------|
| **SEO Critico** | Server Component (RSC) | HTML generado en servidor, indexable. |
| **Dashboard Privado** | Client Component + React Query | Interactividad alta, cache de cliente. |
| **Formulario Complejo** | React Hook Form + Zod | Validacion rica en cliente, UX fluida. |
| **Landing Page** | RSC + SSG (Static Generation) | Velocidad maxima (TTFB bajo). |
| **Modal / Dialog** | Parallel Routes (Intercepting Routes) | URL compartible, preserva contexto. |

## 7. Checklist de Calidad

Antes de dar por finalizado un componente o feature:

- [ ] **RSC por defecto:** Es un Server Component? Si tiene `'use client'`, es estrictamente necesario?
- [ ] **Limites de Suspense:** Hay `<Suspense>` envolviendo llamadas de datos lentas?
- [ ] **Gestion de Errores:** Existe un `error.tsx` o `ErrorBoundary` para fallos controlados?
- [ ] **Accesibilidad:** Se puede navegar con teclado? Tiene etiquetas ARIA si no es semantico?
- [ ] **Tipado:** No hay `any`? Las props estan definidas con interfaces claras?
- [ ] **FSD:** Respeta la jerarquia de capas (shared -> entities -> features -> widgets -> pages)?
