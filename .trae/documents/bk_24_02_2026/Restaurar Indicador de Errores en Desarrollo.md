# Plan de Solución: Restauración de Herramientas de Desarrollo

Tras investigar a fondo y confirmar que la "N flotante" era el **Indicador de Desarrollo Nativo de Next.js** (que muestra actividad de compilación y, en versiones recientes, estado de rutas o errores minimizados), he diseñado una solución para asegurarnos de que tengas visibilidad total de errores en tu entorno de desarrollo.

El indicador nativo a veces se oculta si no hay actividad o si la configuración por defecto cambia entre versiones. Además, para cumplir con tu requerimiento de "ver errores al hacer click", la mejor herramienta profesional para tu stack (que usa React Query) es **React Query Devtools**.

### Pasos de Implementación

1.  **Restaurar Configuración Nativa (Next.js)**:
    - Modificaré `frontend/next.config.js` para asegurar que los `devIndicators` estén explícitamente habilitados y posicionados en la esquina inferior izquierda (como recordabas).
    - *Configuración*: `devIndicators: { buildActivity: true, buildActivityPosition: 'bottom-left' }`.

2.  **Potenciar la Depuración (React Query Devtools)**:
    - Dado que el indicador nativo a veces es limitado, instalaré `@tanstack/react-query-devtools`.
    - Esta herramienta añade un botón flotante (escudo/flor) que te permite inspeccionar en tiempo real:
        - Errores de API y consultas fallidas (lo que buscabas).
        - Estado de la caché y datos.
    - Se configurará para **solo** aparecer en entorno de desarrollo (`process.env.NODE_ENV === 'development'`).

3.  **Integración Segura**:
    - Instalar paquete: `npm install @tanstack/react-query-devtools --save-dev`.
    - Crear componente `DevelopmentTools` para encapsular la lógica condicional.
    - Integrarlo en `frontend/src/app/providers.tsx`.

### Resultado Esperado
Al finalizar, tendrás:
1.  El indicador nativo de Next.js (si hay actividad de build).
2.  El botón de React Query Devtools (siempre disponible en dev) para ver errores detallados.
Ambos desaparecerán automáticamente en producción.