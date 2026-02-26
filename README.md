# Visionarias Brain - AI Sales Agent

Sistema de agente de ventas basado en Inteligencia Artificial, diseñado con una arquitectura "Code-First" utilizando Python, FastAPI y LangGraph.

## Características

*   **Arquitectura Pura Python**: Eliminación de dependencias Low-Code (n8n) para mayor control y latencia reducida.
*   **LangGraph State Machine**: Control determinista del flujo de conversación (S1 -> S6).
*   **Dockerized**: Perfiles de despliegue para Desarrollo y Producción.
*   **RAG Híbrido**: Integración con Qdrant para recuperación de contexto.
*   **Telemetría**: Logging estructurado en PostgreSQL.

## Estructura del Proyecto

```
.
├── docker-compose.yml      # Orquestación de servicios
├── src/
│   ├── api/                # Endpoints (Webhook WhatsApp)
│   ├── core/               # Lógica del Agente (LangGraph)
│   ├── services/           # Integraciones (Redis, DB, WA)
│   └── main.py             # Entrypoint
```

## Configuración

1.  Copiar el archivo de ejemplo:
    ```bash
    cp .env.example .env
    ```
2.  Editar `.env` con tus credenciales de Meta (WhatsApp API) y OpenAI.

## Comandos Rápidos (Makefile)

Este proyecto incluye un `Makefile` para simplificar la gestión de Docker y permisos.

| Comando | Descripción |
| :--- | :--- |
| `make setup` | **Ejecutar primero.** Crea carpetas de datos/logs con permisos correctos. |
| `make dev` | Inicia el entorno de **Desarrollo** (Hot-reload, puertos expuestos). |
| `make prod` | Inicia el entorno de **Producción** (Optimizado, usa `.env.prod`). |
| `make stop` | Detiene todos los contenedores. |
| `make fix-permissions` | Repara problemas de propiedad (candados) en archivos generados por Docker. |
| `make install-front p=lib` | Instala librerías npm en Host y Docker simultáneamente. |

## Despliegue

### Desarrollo (Development)

```bash
make setup
make dev
```

Acceso: `http://localhost:8000/docs`

### Producción (Production)

Diseñado para correr detrás de un Traefik existente.

1.  Asegúrate de que la red externa existe:
    ```bash
    docker network create web_gateway || true
    ```
2.  Lanzar servicios:
    ```bash
    make prod
    ```

El servicio estará disponible en `https://salesagent.alpacapurpura.lat`.
