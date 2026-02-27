# Plan Refinado: Visualización Realista de Tokens y Proveedor LLM

## Diagnóstico

El usuario requiere que la cantidad de tokens (input/output) mostrada en la auditoría sea la **real** devuelta por la API del proveedor, y que se visualice correctamente el proveedor (OpenAI/Gemini).

He revisado el código y detectado el problema:

* En `src/core/llm/providers/openai.py`, la llamada al repositorio `repo.create_llm_log` está enviando `tokens_input=0` y `tokens_output=0` (hardcoded).

* La razón documentada en el código es: `# Usage metadata requires accessing .response_metadata from LangChain result`.

* LangChain devuelve esta metadata en el objeto `AIMessage` resultante de `invoke()`, pero el código actual solo extrae `.content`.

## Solución Técnica

### 1. Captura de Tokens Reales (Backend)

Modificaré `src/core/llm/providers/openai.py` (y `gemini.py` si aplica) para extraer correctamente los metadatos de uso de la respuesta de LangChain.

* **OpenAI**: El objeto `response` de `chat_model.invoke()` contiene `response.response_metadata['token_usage']`.

  * `prompt_tokens` -> `tokens_input`

  * `completion_tokens` -> `tokens_output`

* **Gemini**: LangChain para Gemini también estandariza esto en `response_metadata` o `usage_metadata`.

### 2. Actualización del Logger

Actualizaré la llamada a `repo.create_llm_log` dentro de los providers para pasar estos valores reales en lugar de `0`.

### 3. Visualización en Admin (Frontend)

Implementaré el diseño solicitado en `src/admin/app.py`:

* Detectar proveedor basado en el nombre del modelo (ej. `gpt-` -> OpenAI, `gemini-` -> Google).

* Mostrar métricas reales de tokens ahora que la base de datos tendrá datos verídicos.

## Pasos de Implementación

1. **Modificar** **`src/core/llm/providers/openai.py`**:

   * Cambiar `response.content` por `response` completo temporalmente.

   * Extraer `token_usage` de `response.response_metadata`.

   * Pasar valores a `repo.create_llm_log`.
2. **Modificar** **`src/core/llm/providers/gemini.py`**:

   * Aplicar lógica similar para capturar uso de tokens.

   * Añadir el logging a base de datos (actualmente parece faltar en Gemini según la búsqueda).
3. **Actualizar** **`src/admin/app.py`**:

   * Mejorar la tarjeta de traza para mostrar Provider (Icono), Modelo y Tokens Reales.

## Verificación

* Ejecutaré una prueba manual (o simulación) para verificar que los logs nuevos en DB tengan `tokens_input > 0`.

* El frontend mostrará estos datos.

> **Nota**: Los logs antiguos seguirán mostrando 0 tokens, el cambio aplicará a partir de las nuevas ejecuciones.

