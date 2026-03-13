# Feature-Sliced Design (FSD) Cheatsheet

Este proyecto usa una version simplificada de FSD adaptada para Next.js App Router.

## 1. Estructura de Directorios

### `src/features/` (The Core)
Todo lo relacionado con un dominio de negocio especifico vive aqui.
**Regla**: Si se elimina `src/features/{domain}`, la funcionalidad del {domain} deberia desaparecer completamente, pero la app deberia seguir compilando (menos las rutas especificas).

Estructura:
```
src/features/{domain}/
+-- components/       # UI Components especificos del dominio
+-- hooks/           # Logica & Estado
+-- types/           # Domain Interfaces & Zod Schemas
+-- index.ts         # PUBLIC API (Barrel File)
```

### `src/components/` (The Shared)
- **`ui/`**: Primitivos Shadcn (Button, Input). **NO MODIFICAR** logica aqui.
- **`shared/`**: Componentes de layout globales (Sidebar, Navbar, Footer) usados en multiples features.

### `src/app/` (The Router)
Logica minima. Responsable solo de:
1. Routing (Folders = URLs)
2. Layouts (`layout.tsx`)
3. Metadata (`page.tsx`)
4. Data Fetching (Server Components) -> Pasar datos a Feature Components.

## 2. La Regla de "Public API"
Imports cross-feature estan restringidos.

**Correcto:**
`import { BrandCard } from "@/features/brand";` (Importando del barrel file)

**Incorrecto:**
`import { BrandCard } from "@/features/brand/components/brand-card";` (Deep import violation)

**Por que?**
Deep imports acoplan el codigo a la estructura interna de otro modulo. El `index.ts` actua como contrato.

## 3. Workflow para Nuevas Features
1. **Crear Directorio**: `src/features/<name>`
2. **Scaffold**: Crear `components`, `hooks`, `types`.
3. **Exportar**: Exponer solo los componentes/hooks necesarios en `index.ts`.
4. **Ruta**: Crear `src/app/(dashboard)/<name>/page.tsx` y usar los componentes exportados.
