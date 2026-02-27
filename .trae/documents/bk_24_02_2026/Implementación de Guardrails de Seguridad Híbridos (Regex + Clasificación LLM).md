Voy a implementar un sistema de seguridad **"Híbrido y Económico"** en `node_guardrails` que combina filtros de costo cero con una clasificación inteligente de bajo consumo, utilizando exactamente tus protocolos.

### Estrategia de Eficiencia (Token-Saving)
En lugar de pedirle al LLM que "genere una respuesta de rechazo" (que consume muchos tokens), usaremos un enfoque de **Clasificación + Script**:
1.  **Filtro Nivel 1 (Regex - Costo $0):** Detecta ataques técnicos obvios ("Ignora instrucciones", "Eres un robot") al instante.
2.  **Filtro Nivel 2 (Clasificador LLM - Bajo Costo):** Un prompt ligero que solo responde con una **ETIQUETA** (ej: `POLITICA`, `DRAMA_PERSONAL`, `SPAM`).
3.  **Respuesta Determinista:** Si se detecta una etiqueta de bloqueo, tu código Python inyecta el **Script Exacto** de tus documentos. Esto garantiza cumplimiento legal 100% y ahorra tokens de generación.

### Pasos de Implementación

#### 1. Crear Prompt Clasificador (`src/core/prompts/templates/safety_check.j2`)
Crearé un template optimizado que clasifique el mensaje del usuario en una de las categorías de tus protocolos:
*   `OFF_TOPIC` (Política, Religión, Recetas - *Protocolo Límites*)
*   `PERSONAL_DRAMA` (Rupturas amorosas - *Protocolo Límites*)
*   `SPAM` (Venta cruzada - *Protocolo Límites*)
*   `SAFE` (Mensaje válido para ventas)

#### 2. Actualizar `src/core/nodes.py` -> `node_guardrails`
Reescribiré la función para seguir este flujo lógico:
1.  **Check Regex:** Bloqueo inmediato de inyecciones de prompt.
2.  **Check LLM:** Invocar al modelo con `safety_check.j2`.
3.  **Mapeo de Scripts:**
    *   Si es `OFF_TOPIC` -> Usar script: *"Me encanta tu curiosidad, Visionaria, pero..."*
    *   Si es `PERSONAL_DRAMA` -> Usar script: *"Siento mucho que estés pasando por eso..."*
    *   Si es `SPAM` -> Usar script: *"Gracias por el interés. Este canal es exclusivo..."*
    *   Si es `SAFE` -> Dejar pasar al nodo `router`.

#### 3. Validación
Verificaré que un mensaje como "¿Qué opinas del presidente?" sea bloqueado con tu script exacto, mientras que "Quiero saber el precio" pase fluidamente al flujo de ventas.

### Beneficios
*   **Ahorro:** El LLM solo genera 1 token (la etiqueta).
*   **Seguridad:** Imposible que el LLM "alucine" una respuesta política, porque usamos tus scripts pre-aprobados.
*   **Velocidad:** Los rechazos son casi instantáneos.