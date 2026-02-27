Entendido. El problema es que las trazas no se están vinculando visualmente con los mensajes porque mi heurística de "tiempo" (15 segundos antes) es demasiado estricta o los timestamps no coinciden exactamente.

Además, mostrar solo los nodos *antes* del mensaje del asistente puede ocultar procesos importantes.

### 🔭 Solución Mejorada: "Timeline Integrado" (Estilo WhatsApp + Debug)

En lugar de intentar "adivinar" qué traza pertenece a qué mensaje y ocultarla en un desplegable, voy a renderizar **TODO** en una sola línea de tiempo cronológica.

**Nuevo Diseño Visual:**

1.  **Mensaje Usuario:** 👤 "Hola"
2.  **Traza (Debug):** ⚙️ `[Node: Entry]` → `[Node: Router (Sales Flow)]`
3.  **Traza (Debug):** 🧠 `[Node: Manager]` (Pensamiento: "Usuario saluda...")
4.  **Mensaje Asistente:** 🤖 "¡Hola! ¿En qué te ayudo?"

Esto te dará una visión perfecta de "Causa y Efecto".

### 🛠️ Plan Técnico

1.  **Unificar Datos:**
    *   Obtendré `Messages` y `AgentTraces` en una sola lista.
    *   Los ordenaré todos por `created_at`.

2.  **Renderizado Condicional:**
    *   Iteraré la lista unificada.
    *   Si es `Message`: Muestro la burbuja de chat (`st.chat_message`).
    *   Si es `AgentTrace`: Muestro un bloque de código colapsable (`st.expander`) con un estilo visual distintivo (ej. "⚙️ Paso de Sistema").

3.  **Refinamiento de Datos:**
    *   Dentro del bloque de Traza, mostraré claramente: **Input State**, **LLM Prompt** (si existe), y **Output Decision**.

Esto elimina la necesidad de "adivinar" relaciones y te muestra la realidad cruda de la ejecución secuencial. ¿Procedemos?