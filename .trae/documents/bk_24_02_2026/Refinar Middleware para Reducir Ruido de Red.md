## 1. Optimizar Middleware
- Editar `frontend/src/middleware.ts`:
  - Refinar el `matcher` para excluir explícitamente archivos estáticos comunes y rutas internas de Next.js (`_next`).
  - Esto reduce la carga del middleware y evita intercepciones innecesarias que pueden causar los abortos de red.

## 2. Verificar Estado de Clerk
- Confirmar que `src/app/sign-in/[[...sign-in]]/page.tsx` y `src/app/sign-up/[[...sign-up]]/page.tsx` mantienen la configuración `routing="path"`.

## 3. Limpieza Final
- Los errores actuales son de "cliente" (navegador cancelando peticiones). No requieren cambios en el backend ni en Docker.
- Instruir al usuario para probar el flujo completo de inicio de sesión ignorando los errores de telemetría.