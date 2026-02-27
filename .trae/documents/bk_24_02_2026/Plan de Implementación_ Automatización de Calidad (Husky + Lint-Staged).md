# Plan de Implementación: Automatización de Calidad (Husky + Lint-Staged)

Implementaré un sistema de "Defensa Automática" ligero y eficiente para prevenir errores básicos antes de cada commit, sin afectar el rendimiento en producción.

## 1. Instalación y Configuración (Development Only)
*   Instalar `husky` y `lint-staged` como `devDependencies` en el proyecto frontend.
*   Configurar Husky para activar los hooks de Git.
*   Crear hook `pre-commit` que ejecute `lint-staged`.
*   Configurar `lint-staged` en `package.json` para ejecutar:
    *   `eslint --fix`: Corrige estilo y detecta errores de lógica (como imports rotos).
    *   `tsc --noEmit`: Verifica tipos de TypeScript (crucial para "Module not found").

## 2. Actualización de Reglas (.trae/rules/front-testing-new.md)
Reescribiré el archivo de reglas para que sea mi "guía de autodisciplina" obligatoria antes de entregarte código.

*   **Objetivo**: Verificar siempre antes de responder.
*   **Formato**: < 1000 caracteres, sin negritas, directo al grano.
*   **Contenido**: Mandato de ejecutar `npm run lint` y `tsc` localmente antes de confirmar cualquier cambio de código, y usar Husky como red de seguridad.

## 3. Verificación
*   Provocaré un error intencional (ej. import roto) y trataré de hacer commit (simulado) para verificar que Husky lo bloquee.
*   Correré los comandos manualmente para asegurar que el proyecto actual está limpio.

Procederé a instalar las herramientas en el contenedor de desarrollo (`client_dashboard_dev`).