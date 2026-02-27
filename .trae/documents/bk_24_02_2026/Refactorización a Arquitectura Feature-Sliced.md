# Plan de Refactorización Frontend - Arquitectura Feature-Sliced

He analizado tu estructura actual y propongo la siguiente reorganización para cumplir con el objetivo de modularidad y separación de responsabilidades.

## 1. Mapa de Cambios (Estructura de Archivos)

La transformación moverá los componentes dispersos en `src/components/` hacia módulos autocontenidos en `src/features/`.

| Origen Actual (`src/`) | Nuevo Destino (`src/`) | Notas |
| :--- | :--- | :--- |
| `components/brand/*` | `features/brand/components/*` | Feature principal de marca |
| `components/avatars/*` | `features/brand/components/avatars/*` | Integrado en Brand (usado en la misma página) |
| `components/connections/*` | `features/connections/components/*` | Feature de conexiones |
| `components/offer-studio/*` | `features/offer-studio/components/*` | Feature de ofertas |
| `components/sales/*` | `features/sales/components/*` | Feature de ventas |
| `components/knowledge/*` | `features/knowledge/components/*` | Feature de conocimiento |
| `components/audit/*` | `features/audit/components/*` | Feature de auditoría |
| `components/settings/*` | `features/settings/components/*` | Configuración general |
| `components/dashboard/*` | `features/dashboard/components/*` | Widgets del dashboard (StatsCard) |
| `components/layout/*` | `components/shared/layout/*` | Layouts globales |
| `components/development-tools.tsx` | `components/shared/development-tools.tsx` | Utilidad global |
| `components/mode-toggle.tsx` | `components/shared/mode-toggle.tsx` | UI Global |
| `components/theme-provider.tsx` | `components/providers/theme-provider.tsx` | Provider Global |

## 2. Separación de Lógica (Hooks)

Siguiendo tu regla de **Container/Presenter**, refactorizaré las páginas principales que actualmente contienen lógica pesada (fetch, state, handlers).

### Ejemplo Principal: `BrandSettingsPage`
**Estado Actual:** `app/(dashboard)/brand-settings/page.tsx` maneja `settings`, `loading`, `saving`, y todas las llamadas a `brandApi`.
**Refactorización:**
1.  Crear `features/brand/hooks/useBrandSettings.ts`.
2.  Mover toda la lógica de estado y `useEffect` al hook.
3.  El componente `page.tsx` solo llamará al hook: `const { settings, loading, updateIdentity } = useBrandSettings();` y renderizará la UI.

*Aplicaré este mismo patrón a `ConnectionsPage` y `OfferStudioPage` si detecto lógica similar.*

## 3. Barriles (Barrels)
Crearé un archivo `index.ts` en cada carpeta de feature (`features/brand/index.ts`) para exportar públicamente solo lo necesario, manteniendo la estructura interna encapsulada.

## 4. Ejecución
1.  **Crear estructura**: Generar carpetas en `features/` y `components/shared`.
2.  **Mover archivos**: Reubicar componentes físicos.
3.  **Refactorizar Lógica (Brand)**: Extraer `useBrandSettings`.
4.  **Corregir Imports**: Actualizar referencias en `app/` para apuntar a las nuevas ubicaciones.
5.  **Verificar**: Asegurar que `npm run build` (o verificación estática) no reporte rutas rotas.

¿Apruebas este plan de migración?