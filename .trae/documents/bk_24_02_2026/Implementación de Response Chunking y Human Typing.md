# Implementación de Response Chunking y Simulador de Escritura Humana

Este plan aborda la solicitud de implementar "Response Chunking" (fragmentación de respuestas) y simulación de escritura humana para mejorar la experiencia de usuario y la autoridad de ventas ("High Ticket").

## 1. Modificación del System Prompt (Core)

Actualizaremos la plantilla del prompt del sistema para instruir al LLM a estructurar sus respuestas como un Array JSON en lugar de un bloque de texto único.

* **Archivo Objetivo**: `backend/src/core/prompts/templates/sales_system.j2`

* **Cambios**:

  * Añadir instrucción explícita: "Tu salida DEBE ser un Array JSON de strings: `["Mensaje 1", "Mensaje 2", "Mensaje 3"]`."

  * Definir la "Tríada de Ventas":

    1. **Acknowledgment**: Empatía/Validación corta.
    2. **Value**: Explicación técnica o de valor (máximo 3-4 líneas).
    3. **Ping-Pong**: Pregunta o CTA final aislada.

  * Asegurar que el formato sea estrictamente JSON válido.

## 2. Creación del Servicio `OutputManager`

Crearemos un nuevo servicio encargado de orquestar la salida de mensajes, manejando el parsing, los delays y la simulación de escritura.

* **Nuevo Archivo**: `backend/src/services/output_manager.py`

* **Responsabilidades**:

  * **Parsing Robusto**: Intentar parsear la respuesta del LLM como JSON. Si falla (fallback), tratar el texto como un único bloque.

  * **Cálculo de Delays**: Implementar la fórmula de "Velocidad de Tecleo Variable" (CPM + Jitter).

    * `typing_time = length(message) / speed_factor`

  * **Simulación Visual**: Enviar estados de "escribiendo..." (`typing_on`) al canal correspondiente.

  * **Micro-Pausas**: Añadir pausas cognitivas (200ms-600ms) entre el envío de un mensaje y el inicio del siguiente "tecleo".

## 3. Integración en el Flujo de la API

Reemplazaremos la lógica de envío actual en `routes.py` por el nuevo `OutputManager`.

* **Archivo Objetivo**: `backend/src/api/routes.py`

* **Cambios**:

  * En la función `_execute_agent_flow`:

  * Eliminar la lógica actual de "Artificial Delay" simple (líneas 128-133).

  * Eliminar el envío directo único (líneas 136).

  * Invocar `await OutputManager.process_response(user_id, bot_text, channel_adapter)`.

## 4. Verificación

Como no podemos interactuar con webhooks reales (WhatsApp/Telegram), crearemos un test unitario para validar la lógica del `OutputManager`.

* **Validación**:

  * Testear que el parser maneje correctamente JSONs válidos y textos planos (fallback).

  * Verificar que los delays calculados estén dentro de rangos razonables.

