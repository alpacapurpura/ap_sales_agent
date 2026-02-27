# Implementación Completa de Panel de Contexto (Backend + Frontend)

Para garantizar que tengas acceso a **toda** la información (`profile_data` y `AgentState` completo), ejecutaré la siguiente estrategia full-stack:

## 1. Backend: Nuevo Endpoint de Detalle
Modificaré `backend/src/api/routers/admin.py` para añadir una ruta específica `GET /audit/users/{user_id}`.
*   **Objetivo**: Retornar el objeto `User` completo.
*   **Dato Crítico**: Incluirá explícitamente el campo `profile_data` (JSONB) que actualmente no se envía al frontend.

## 2. Frontend: API y Hooks
Actualizaré `frontend/lib/api/audit.ts` para:
*   Definir la interfaz `UserDetails` que incluya `profile_data: any`.
*   Crear el hook `useUserDetails(userId)` para consumir el nuevo endpoint.

## 3. Frontend: Componente `ContextPanel`
Crearé el componente `frontend/components/audit/context-panel.tsx` basado en `Sheet` (Panel Lateral Derecho).
*   **Pestaña "Perfil"**:
    *   Consumirá `useUserDetails`.
    *   Mostrará un visor JSON (`<pre>`) con todo el contenido de `profile_data` y metadatos del usuario.
*   **Pestaña "Estado"**:
    *   Identificará el último evento de tipo `trace` en tu línea de tiempo.
    *   Consumirá `useTraceDetails` para ese ID.
    *   Mostrará el `output_state` completo sin filtros.

## 4. Integración en `ChatTimeline`
*   Añadiré los botones `[👤 Usuario]` y `[🧠 AgentState]` en la cabecera.
*   Estos botones abrirán el `ContextPanel` en la pestaña correspondiente.

Esta solución asegura que **ningún dato quede oculto**, cumpliendo estrictamente con tu solicitud de "absolutamente todos los datos".
