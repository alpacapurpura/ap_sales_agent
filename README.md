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

## Despliegue

### Desarrollo (Development)

Expone los puertos de todos los servicios (API: 8000, Redis: 6379, Qdrant: 6333).

```bash
docker compose --profile development up --build
```

Acceso: `http://localhost:8000/docs`

### Producción (Production)

Diseñado para correr detrás de un Traefik existente en la red `web_gateway`.

1.  Asegúrate de que la red externa existe:
    ```bash
    docker network create web_gateway || true
    ```
2.  Lanzar servicios:
    ```bash
    docker compose --profile production up -d --build
    ```

El servicio estará disponible en `https://salesagent.alpacapurpura.lat` (configurado vía etiquetas Traefik en `docker-compose.yml`).
