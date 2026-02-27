# Respuesta y Plan de Actualización de Comportamiento

## Respuesta a tu pregunta

**No defines el "qué decir" en `nodes.py`, sino en el Prompt del Sistema.**

El archivo `nodes.py` actúa como el **Director de Escena**: decide en qué escenario estamos (Rapport, Discovery, Pitch) usando el `node_state_manager`.
El archivo `sales_system.j2` actúa como el **Guion**: contiene las instrucciones específicas de cómo actuar en cada escenario.

*   **`nodes.py` (Línea 336)**: Carga el prompt `sales_system.j2` e inyecta el `current_state`.
*   **`sales_system.j2` (Líneas 36-57)**: Tiene bloques `{% if current_state == '...' %}` que definen el comportamiento.

## Plan de Mejora

Actualmente, tu `sales_system.j2` está desactualizado respecto al nuevo `UserProfile` que acabamos de crear y le faltan etapas. Voy a sincronizarlo.

### 1. Actualizar `src/core/prompts/templates/sales_system.j2`

*   **Sincronizar Variables**: Cambiar `revenue_tier` por `financial_tier`, `pain_point` por `main_pain_point`.
*   **Completar Etapas**:
    *   **S2_Discovery**: Añadir lógica para preguntar por `missing_fields` (si faltan datos obligatorios).
    *   **S3_Gap**: Instruir para reflejar el dolor (`main_pain_point`) y crear la brecha.
    *   **S4_Pitch**: Presentar la solución conectada al `main_goal`.
    *   **S6_Closing**: Instrucciones para pedir el cierre o agendar.
*   **Estrategia Dinámica**: Usar el campo `active_strategy` (que ya seteamos en el Manager) para modular el tono (ej. si es "Risk_Reversal", enfatizar garantía).

Esta separación mantiene tu código Python limpio (`nodes.py` solo mueve datos) y tu lógica de negocio flexible (todo el comportamiento está en el J2).
