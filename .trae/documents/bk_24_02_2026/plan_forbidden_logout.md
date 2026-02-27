# Plan de Modificación: Página de Acceso Denegado

Este plan detalla los cambios necesarios para actualizar la página de "Acceso Denegado" (`ForbiddenPage`), cambiando la acción de "Volver al Inicio" por un cierre de sesión explícito ("Intentar con otra cuenta").

## Objetivos
1.  **Cambiar Texto del Botón**: Reemplazar "Volver al Inicio" por "Intentar con otra cuenta".
2.  **Implementar Lógica de Logout**: Al hacer clic, el usuario debe ser deslogueado y redirigido al inicio.

## Archivos Afectados
- `frontend/src/app/(main)/forbidden/page.tsx`: Componente que renderiza la pantalla de bloqueo.

## Pasos de Implementación

### 1. Análisis y Preparación
- Leer el archivo `frontend/src/app/(main)/forbidden/page.tsx` para confirmar la estructura actual.
- Verificar que el componente sea un "Client Component" (debe tener `'use client'` al inicio) para poder usar hooks como `useClerk`. Si no lo es, convertirlo.

### 2. Modificación del Componente
- Importar `useClerk` de `@clerk/nextjs`.
- Obtener la función `signOut` del hook `useClerk`.
- Modificar el botón existente:
    - **Texto**: Cambiar a "Intentar con otra cuenta".
    - **Acción**: Asignar `onClick={() => signOut({ redirectUrl: '/' })}`.
- Asegurar que el componente use la directiva `'use client'`.

### 3. Verificación
- Verificar que no haya errores de linter.
- El usuario deberá verificar manualmente que al hacer clic en el botón, la sesión se cierre y redirija al login/home.

## Estado
- [ ] Leer archivo actual.
- [ ] Aplicar cambios en `ForbiddenPage`.
- [ ] Verificación final.
