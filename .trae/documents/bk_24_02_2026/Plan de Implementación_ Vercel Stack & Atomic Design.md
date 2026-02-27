# Plan de Modernización del Frontend (Vercel Stack)

Vamos a transformar tu frontend actual en una aplicación profesional, escalable y mantenible implementando el "Vercel Stack" y Atomic Design, tal como se recomendó.

## 1. Inicialización de Shadcn/UI & Dependencias Core
Prepararemos el terreno instalando las librerías base para componentes y gestión de estado.
*   **Instalar dependencias de utilidad**: `clsx`, `tailwind-merge`, `class-variance-authority`, `lucide-react`.
*   **Inicializar Shadcn**: Ejecutar el comando `init` para configurar `components.json` y los estilos base (CSS Variables).
*   **Instalar TanStack Query**: Para el manejo robusto de datos asíncronos (`@tanstack/react-query`).

## 2. Reestructuración de Carpetas (Atomic Design)
Organizaremos el código para evitar el "espagueti", separando responsabilidades claramente dentro de `src/` (o la raíz si no usas src).
*   Crear `components/ui/` (Átomos: botones, inputs, cards).
*   Crear `components/common/` (Moléculas: barras de búsqueda, navbars).
*   Crear `components/dashboard/` (Organismos: gráficos, tablas de negocio).
*   Crear `lib/` (Utilidades y clientes de API).
*   Crear `hooks/` (Custom hooks).

## 3. Instalación de Componentes Base (Átomos)
Traeremos los componentes esenciales de Shadcn que necesitamos para empezar.
*   **Instalar**: `button`, `card`, `input`, `avatar`, `dropdown-menu`, `skeleton`.

## 4. Implementación del Dashboard (Caso de Uso Real)
Reemplazaremos la página actual (`page.tsx`) por un dashboard estructurado usando los nuevos componentes.
*   **Crear `StatsCard` (Molécula)**: Componente reutilizable para mostrar métricas.
*   **Refactorizar `page.tsx` (Organismo)**:
    *   Usar `StatsCard` para mostrar los datos reales.
    *   Integrar `React Query` para obtener los datos (`/api/v1/knowledge/stats`) con manejo de carga (Skeletons) y error.
*   **Integrar Gráficos**: Instalar `recharts` y crear un componente de ejemplo `RevenueChart` (o similar, adaptado a tus datos de vectores).

## 5. Verificación
*   Reconstruir el contenedor Docker para asegurar que todas las nuevas dependencias se instalen correctamente.
*   Verificar que el dashboard cargue, muestre datos reales y tenga la estética profesional de Shadcn.
