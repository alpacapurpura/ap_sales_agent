# Plan de Implementación de Testing (Validado para Docker)

He revisado la configuración de `docker-compose.yml`. **No es necesario crear nuevos volúmenes**.

El volumen actual `- ./frontend:/app` permitirá que Vitest detecte automáticamente los nuevos archivos de configuración y tests que creemos en el host. El volumen anónimo de `node_modules` se actualizará correctamente mediante el paso de reconstrucción (`--build`) incluido en el plan.

## Pasos de Implementación

1.  **Instalación de Dependencias**
    *   Instalar `vitest`, `jsdom`, `@vitejs/plugin-react` y `@testing-library/*` en `frontend`.

2.  **Configuración de Vitest**
    *   Crear `vitest.config.ts`: Configuración compatible con Next.js (alias `@/`) y entorno `jsdom`.
    *   Crear `src/test/setup.ts`: Configuración global de matchers.
    *   Actualizar `package.json`: Añadir scripts de test.

3.  **Creación de Test (Smoke Test)**
    *   Crear `src/components/ui/label.test.tsx` para validar la integración.

4.  **Actualización de Contenedor**
    *   Ejecutar `docker compose up -d --build client_dashboard`. Esto es crucial para propagar las nuevas dependencias al volumen aislado `/app/node_modules`.

5.  **Verificación**
    *   Ejecutar `docker exec -t visionarias_client npm test` para confirmar que el entorno dockerizado ejecuta las pruebas correctamente.