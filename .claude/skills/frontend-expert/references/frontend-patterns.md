---
name: frontend-patterns
description: Patrones de diseño frontend autorizados para Next.js (App Router), React y FSD.
origin: Frontend Expert Skill
---

# Patrones de Diseño Frontend (Guía Autorizada)

Este documento define los patrones de arquitectura y diseño frontend obligatorios para el desarrollo en Visionarias Brain. Estos patrones están optimizados para **Next.js 14+ (App Router)**, **React 18/19** y **Feature-Sliced Design (FSD)**.

## 1. Arquitectura de Componentes (App Router)

### 1.1. Server Components por Defecto ("Server-First")
**Principio:** Todo componente es un Server Component (RSC) a menos que requiera interactividad específica.
**Beneficio:** Reducción drástica del bundle size (código de librerías no viaja al cliente), acceso directo a backend/BD, seguridad mejorada.

**Anti-patrón:**
```tsx
// ❌ MAL: Convertir todo a 'use client' por hábito
'use client'
import { db } from '@/shared/lib/db' // Error: No se puede importar backend en cliente
```

**Patrón Correcto:**
```tsx
// ✅ BIEN: Separación de responsabilidades
// entities/user/ui/user-card.tsx (Server Component)
import { formatDate } from '@/shared/lib/date'

export async function UserCard({ userId }: { userId: string }) {
  const user = await fetchUser(userId) // Fetch directo o vía API interna
  return (
    <div className="card">
      <h1>{user.name}</h1>
      <p>Joined: {formatDate(user.createdAt)}</p>
      {/* Slot para interactividad */}
      <FollowButton userId={userId} />
    </div>
  )
}
```

### 1.2. Patrón de Composición ("The Hole Pattern")
**Problema:** Importar un Server Component dentro de un archivo marcado con `'use client'` lo convierte implícitamente en un Client Module (o lanza error si tiene código de servidor).
**Solución:** Pasar los Server Components como `children` o `props` (slots) al Client Component.

```tsx
// ✅ BIEN: Client Wrapper
// features/theme/ui/theme-provider.tsx (Client Component)
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
          {children}     {/* Server Component renderizado en servidor */}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

## 2. Gestión de Estado (State Management)

### 2.1. URL como Fuente de Verdad (URL State)
**Contexto:** Filtros, paginación, búsquedas, modales compartibles.
**Regla:** Si el estado debe sobrevivir a un refresh o ser compartible, **DEBE** estar en la URL.
**Herramienta:** `nuqs` (recomendado) o `useSearchParams`.

```tsx
// ✅ BIEN: Búsqueda vía URL
// features/search/ui/search-bar.tsx
'use client'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { useDebouncedCallback } from 'use-debounce'

export function SearchBar() {
  const searchParams = useSearchParams()
  const pathname = usePathname()
  const { replace } = useRouter()

  const handleSearch = useDebouncedCallback((term: string) => {
    const params = new URLSearchParams(searchParams)
    if (term) params.set('q', term)
    else params.delete('q')
    replace(`${pathname}?${params.toString()}`)
  }, 300)

  return <input defaultValue={searchParams.get('q')?.toString()} onChange={(e) => handleSearch(e.target.value)} />
}
```

### 2.2. Server State (React Query) vs useEffect
**Regla:** **PROHIBIDO** usar `useEffect` para hacer fetch de datos en el cliente.
**Solución:**
1. **Preferido:** Fetch en Server Component y pasar datos como prop inicial.
2. **Cliente (Polling/Mutaciones):** Usar TanStack Query.

```tsx
// ✅ BIEN: Hydration Boundary
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
**Librería:** `zustand`.

## 3. Patrones de Componentes Reutilizables

### 3.1. Componentes Polimórficos (asChild)
**Contexto:** Construcción de UI Kits (botones que son enlaces, etc.).
**Solución:** Usar `Slot` de Radix UI (patrón `asChild`).

```tsx
// ✅ BIEN: Botón flexible
import { Slot } from '@radix-ui/react-slot'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
}

export function Button({ asChild, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button"
  return <Comp {...props} />
}

// Uso
<Button asChild>
  <Link href="/login">Login</Link>
</Button>
```

### 3.2. Compound Components (Componentes Compuestos)
**Contexto:** Componentes complejos con sub-partes que comparten estado implícito.

```tsx
// ✅ BIEN: Card Component
export function Card({ children }: { children: React.ReactNode }) {
  return <div className="card-root">{children}</div>
}

Card.Header = function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="card-header">{children}</div>
}

// Uso
<Card>
  <Card.Header>Título</Card.Header>
</Card>
```

## 4. Patrones de Formularios y Mutaciones

### 4.1. Server Actions + Zod
**Regla:** Las mutaciones deben ser Server Actions validadas con Zod.
**Hook:** `useForm` (React Hook Form) para manejo de estado en cliente + integración con Server Action.

```tsx
// features/auth/actions/login.ts
'use server'
import { z } from 'zod'

const schema = z.object({ email: z.string().email() })

export async function loginAction(prevState: any, formData: FormData) {
  const validated = schema.safeParse(Object.fromEntries(formData))
  if (!validated.success) return { errors: validated.error.flatten().fieldErrors }
  // Lógica de backend...
}
```

## 5. Optimización y Performance

### 5.1. Optimistic UI
**Contexto:** Feedback instantáneo al usuario antes de que el servidor responda.
**Hook:** `useOptimistic`.

```tsx
// ✅ BIEN: Feedback inmediato
'use client'
import { useOptimistic } from 'react'

export function LikeButton({ likes, onLike }: { likes: number, onLike: () => void }) {
  const [optimisticLikes, addOptimisticLike] = useOptimistic(
    likes,
    (state, newLike: number) => state + newLike
  )

  return (
    <button onClick={async () => {
      addOptimisticLike(1) // Actualiza UI inmediatamente
      await onLike()       // Llama al server action
    }}>
      Likes: {optimisticLikes}
    </button>
  )
}
```

### 5.2. Dynamic Imports (Lazy Loading)
**Contexto:** Componentes pesados (Gráficos, Mapas, Editores de Texto) que no son visibles inicialmente.

```tsx
const HeavyChart = dynamic(() => import('./heavy-chart'), {
  loading: () => <Skeleton className="h-64" />,
  ssr: false // Si depende de window/browser APIs
})
```

## 6. Matriz de Decisión Técnica

| Escenario | Solución Recomendada | ¿Por qué? |
|-----------|----------------------|-----------|
| **SEO Crítico** | Server Component (RSC) | HTML generado en servidor, indexable. |
| **Dashboard Privado** | Client Component + React Query | Interactividad alta, caché de cliente. |
| **Formulario Complejo** | React Hook Form + Zod | Validación rica en cliente, UX fluida. |
| **Landing Page** | RSC + SSG (Static Generation) | Velocidad máxima (TTFB bajo). |
| **Modal / Dialog** | Parallel Routes (Intercepting Routes) | URL compartible, preserva contexto. |

## 7. Checklist de Calidad (Validación)

Antes de dar por finalizado un componente o feature:

- [ ] **RSC por defecto:** ¿Es un Server Component? Si tiene `'use client'`, ¿es estrictamente necesario?
- [ ] **Límites de Suspense:** ¿Hay `<Suspense>` envolviendo llamadas de datos lentas?
- [ ] **Gestión de Errores:** ¿Existe un `error.tsx` o `ErrorBoundary` para fallos controlados?
- [ ] **Accesibilidad:** ¿Se puede navegar con teclado? ¿Tiene etiquetas ARIA si no es semántico?
- [ ] **Tipado:** ¿No hay `any`? ¿Las props están definidas con interfaces claras?
- [ ] **FSD:** ¿Respeta la jerarquía de capas (shared -> entities -> features -> widgets -> pages)?
