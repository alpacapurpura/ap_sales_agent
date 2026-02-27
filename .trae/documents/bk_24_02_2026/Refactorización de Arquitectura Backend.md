# Refactorización de Arquitectura Backend: Chat Orchestrator

## Objetivo
Extraer la lógica de negocio compleja ("Fat Controller") de `src/api/routes.py` hacia una capa de servicios dedicada, mejorando la testabilidad, mantenibilidad y adhesión a principios SOLID.

## Pasos de Implementación

### 1. Crear `src/services/chat_orchestrator.py`
Clase `ChatOrchestrator` que encapsulará:
- `handle_incoming_webhook`: Normalización y encolado en buffer.
- `smart_debounce_task`: Lógica de concurrencia y espera dinámica.
- `process_chat_flow` (antes `_execute_agent_flow`): Orquestación de DB, Historial, Agente y Respuesta.
- **Mejora**: Implementará el patrón Singleton o inyección para reutilizar adaptadores (Telegram/WhatsApp).

### 2. Limpiar `src/api/routes.py`
- Eliminar funciones `_execute_agent_flow` y `smart_debounce_task`.
- Inyectar/Instanciar `ChatOrchestrator`.
- Los endpoints solo delegarán la ejecución: `orchestrator.handle_webhook(...)`.

### 3. Renombrar Servicio de Semántica
- Renombrar `src/services/router_service.py` -> `src/services/semantic_router.py` para evitar confusión con routers HTTP.
- Actualizar todas las importaciones afectadas.

## Verificación
- Verificar que los webhooks de Telegram y WhatsApp sigan respondiendo `200 OK`.
- Verificar que el flujo de conversación (Buffer -> Agente) siga funcionando idéntico (refactorización segura).
