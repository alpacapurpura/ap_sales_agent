# Refactor Tailwind Best Practices Spec

## Why
El análisis del código frontend ha revelado deuda técnica en el manejo de estilos con Tailwind CSS. Específicamente, se utiliza concatenación manual de cadenas para clases condicionales, lo cual es propenso a errores de especificidad y conflictos de estilos. Además, existen bloques de estilos repetitivos (como en las burbujas de chat) que violan el principio DRY y dificultan el mantenimiento. La adopción de utilidades de combinación de clases (`cn`) y patrones de componentes (`cva`) alineará el proyecto con las mejores prácticas modernas.

## What Changes
- **Estandarización de `cn()`**: Reemplazo sistemático de interpolación de strings (`className={\`...\${cond ? 'a' : 'b'}\`}`) por la utilidad `cn()` (clsx + tailwind-merge) para garantizar la correcta fusión de clases y resolución de conflictos.
- **Abstracción de Layouts**: Introducción de clases de utilidad semánticas para layout (`v-stack`, `h-stack`, `center`) en la configuración de Tailwind o CSS global, siguiendo las recomendaciones de la skill `frontend-tailwind-best-practices`.
- **Refactorización de Componentes Repetitivos**:
    - Extracción de estilos de burbujas de chat en `sales-inbox-sheet.tsx` usando `cva` (Class Variance Authority).
    - Limpieza de lógica condicional en `team-list.tsx` y `PipelineView.tsx`.
- **Eliminación de Antipatrones**: Corrección de usos de `truncate` y `absolute` que dependen de concatenación manual.

## Impact
- **Affected specs**: No afecta funcionalidad de negocio, es un refactor puramente técnico y visual.
- **Affected code**:
    - `frontend/src/lib/utils.ts` (Verificación de utilidad `cn`)
    - `frontend/src/app/globals.css` (Adición de utilidades de layout)
    - `frontend/src/features/sales/components/overlay/sales-inbox-sheet.tsx`
    - `frontend/src/features/brand/components/team/team-list.tsx`
    - `frontend/src/features/marketing-studio/components/PipelineView.tsx`
    - Otros componentes dispersos que usen concatenación manual.

## ADDED Requirements
### Requirement: Layout Utilities
El sistema DEBE proveer las siguientes clases de utilidad para layout:
- `.v-stack`: Flex column con soporte de gap.
- `.h-stack`: Flex row con soporte de gap y alineación centrada verticalmente por defecto.
- `.center`: Flex con items-center y justify-center.
- `.spacer`: Flex-grow para ocupar espacio disponible.

### Requirement: Component Variants
Los componentes con múltiples estados visuales (como mensajes de chat) DEBEN usar `cva` para definir sus variantes en lugar de lógica ternaria en línea.

## MODIFIED Requirements
### Requirement: Class Name Construction
**Antes**: `className={\`base ${cond ? 'active' : ''}\`}`
**Después**: `className={cn("base", cond && "active")}`
**Razón**: Evitar conflictos de especificidad y mejorar legibilidad.
