# Reglas de Estilos (Tailwind CSS)

## Principios
- Usar exclusivamente Tailwind CSS utility classes.
- Cero estilos inline (`style={{...}}`).
- Usar la funcion `cn()` de `@/shared/lib/utils` para clases condicionales.
- Reutilizar componentes de `src/components/ui/` (Shadcn) antes de crear primitivos nuevos.

## Colores y Variables
- Usar las variables CSS del tema definidas en `tailwind.config.ts` y `globals.css`.
- Preferir tokens semanticos (`text-primary`, `bg-background`) sobre valores directos (`text-blue-500`).

## Responsive Design
- Enfoque Mobile-First.
- Usar breakpoints de Tailwind: `sm:`, `md:`, `lg:`, `xl:`, `2xl:`.
- Evitar media queries CSS custom.

## Spacing y Layout
- Usar el sistema de spacing de Tailwind consistentemente.
- Preferir `gap-*` sobre `space-x-*` / `space-y-*` para layouts flex/grid.
- Usar `container` con `mx-auto` para centrado de contenido.
