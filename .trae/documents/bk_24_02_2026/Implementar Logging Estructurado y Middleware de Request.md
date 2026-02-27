# Implementación de Logging Estructurado con `structlog` (Docker-Ready)

## 1. Instalación de Dependencias
Añadiremos `structlog` al entorno. Dado que estamos en Docker, debemos actualizar `requirements.txt` y reconstruir.

## 2. Configuración (`src/core/logging_config.py`)
Crearemos un módulo para configurar `structlog`.
*   **JSON Renderer**: Para que los logs de Docker sean legibles por máquinas.
*   **Contexto**: `request_id`, `timestamp`.

## 3. Middleware (`src/main.py`)
Interceptaremos todas las peticiones HTTP para:
*   Asignar `request_id`.
*   Loguear entrada (Body crudo) y salida (Status Code).
*   Capturar excepciones globales.

## 4. Instrumentación (`src/api/routes.py`)
Añadiremos logs explícitos al inicio de `process_message` para ver exactamente qué payload llega desde Telegram/WhatsApp, antes de que cualquier lógica de negocio falle.

## Plan de Ejecución
1.  **Actualizar `requirements.txt`**: Añadir `structlog`.
2.  **Crear `src/core/logging_config.py`**.
3.  **Modificar `src/main.py`**: Integrar configuración y middleware.
4.  **Modificar `src/api/routes.py`**: Usar el nuevo logger.
5.  **Reconstruir Docker**: Ejecutar `docker-compose build web` y `up` para aplicar cambios.
