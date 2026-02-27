# Revisión Sistémica y Plan de Optimización High-Ticket

He realizado una revisión exhaustiva de tu arquitectura (`agent.py`, `nodes.py`) y los prompts asociados. Tu sistema es estructuralmente sólido, pero he detectado áreas críticas de mejora para alcanzar el nivel de "Venta High Ticket" que buscas.

## 1. Análisis de Calidad y Contradicciones

### A. El "Router" vs. "State Manager" (Conflicto de Responsabilidad)
*   **Problema:** `node_router` usa lógica *hardcoded* (palabras clave simples) para detectar objeciones, mientras que `node_state_manager` usa un LLM avanzado para entender el contexto.
*   **Riesgo:** Si una usuaria dice "No sé si tengo tiempo porque trabajo mucho", el router simple podría marcarlo como `obj_time` y disparar una respuesta prefabricada, ignorando que el `State Manager` podría haber detectado que en realidad es una oportunidad para indagar más en `S2_Discovery`.
*   **Solución:** Mover la detección de objeciones sutiles al `State Manager` (fase cognitiva) y dejar el `Router` solo para emergencias técnicas o éticas.

### B. El "HyDE" Indiscriminado (Desperdicio de Tokens y Latencia)
*   **Problema:** Actualmente, `node_response_generation` ejecuta el pipeline HyDE (generar documento hipotético -> buscar vectores) para *casi todos* los mensajes que no son objeciones.
*   **Impacto:** Estás gastando ~300 tokens extra y añadiendo 2-3 segundos de latencia en mensajes triviales como "Hola" o "Sí".
*   **Solución:** Implementar un "Filtro de Densidad" antes de llamar a HyDE. Solo buscar en la base de conocimientos si la pregunta es compleja o específica.

### C. La "Memoria a Corto Plazo" del LLM
*   **Problema:** Aunque inyectamos el historial, el LLM a veces pierde el foco de "qué acabo de preguntar".
*   **Solución:** Reforzar el prompt `sales_system.j2` con una directiva explícita de "Objetivo Inmediato" derivado del `State Manager`.

---

## 2. Plan de Acción (Sin rehacer todo, solo refinar)

### Paso 1: Optimización del `node_router`
*   **Acción:** Simplificar el router. Eliminar la detección de objeciones por palabras clave (precio, tiempo) y dejar que el LLM en `State Manager` o `Response Generation` maneje esto con más matices.
*   **Por qué:** Las ventas High Ticket requieren *escucha activa*, no gatillos automáticos.

### Paso 2: Refinamiento de `node_response_generation` (Smart RAG)
*   **Acción:** Añadir una condición lógica:
    ```python
    if len(last_user_msg.split()) > 4 or "?" in last_user_msg:
        # Ejecutar HyDE + RAG
    else:
        # Respuesta conversacional directa (Ahorro de tokens/tiempo)
    ```

### Paso 3: Pulir `state_transition.j2` (El Cerebro)
*   **Acción:** Asegurar que el prompt entienda la diferencia entre una "excusa" (manejar objeción) y un "dato de perfil" (guardar info).
*   **Mejora:** Añadir ejemplos *few-shot* en el prompt para que distinga mejor.

### Paso 4: Revisión de Prompts (Calidad de Respuesta)
*   **Acción:** Revisar `sales_system.j2`.
*   **Mejora:** Inyectar dinámicamente la "Estrategia Activa" (ej. ROI Reframing) como una instrucción *top-level* para que el modelo no la olvide al generar el texto final.

¿Te parece bien este enfoque de "refinamiento quirúrgico" para elevar la calidad sin romper la estructura actual?