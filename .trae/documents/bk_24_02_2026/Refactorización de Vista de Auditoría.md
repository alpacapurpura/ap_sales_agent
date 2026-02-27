# Refactorización de `src/admin/app.py` para Mejorar Legibilidad

El objetivo es modularizar la función `render_audit_view` para reducir su complejidad ciclomática y facilitar la lectura, extrayendo la lógica de renderizado de la línea de tiempo a funciones auxiliares.

## Cambios Propuestos

1.  **Crear `_render_timeline_trace(t)`**:
    *   Extraer la lógica que visualiza un `AgentTrace` (actualmente líneas 390-442).
    *   Manejará el cálculo de diferencias de estado (`get_state_diff`), visualización de logs de LLM (el prompt) y actualizaciones de perfil.

2.  **Crear `_render_timeline_message(m)`**:
    *   Extraer la lógica simple de visualización de mensajes de chat (actualmente líneas 374-376).

3.  **Simplificar `render_audit_view`**:
    *   La función principal solo se encargará de obtener datos, construir la lista cronológica y llamar a las nuevas funciones auxiliares dentro del bucle.

## Beneficios
*   **Claridad**: Será obvio dónde se renderiza el prompt (`_render_timeline_trace`) sin navegar por cientos de líneas.
*   **Mantenibilidad**: Si quieres cambiar cómo se ve el chat, solo tocas `_render_timeline_message`.
