---
alwaysApply: false
description: 
---
# Stack Tecnológico: Visionarias Agent

## Core
*   **Lenguaje**: Python 3.11+ con **Tipado Estricto** obligatorio.
*   **API**: `FastAPI`. Uso de modelos Pydantic para Request/Response bodies.
*   **Orquestación**: `LangGraph` (v0.1+). Preferido sobre cadenas lineales.
*   **Validación**: `Pydantic` v2. Todo input/output del LLM debe validarse contra un esquema.

## Infraestructura de Datos
*   **Vectorial**: `Qdrant` con filtrado por metadatos (Payload Filtering).
*   **Estado**: `Redis` para persistencia de sesión y `AgentState`.
*   **Logs**: `PostgreSQL` para telemetría y auditoría.
*   **Templating**: `Jinja2`. Prompts en archivos `.j2` (no f-strings).

## Despliegue (Docker)
*   **Perfiles**:
    *   `development`: Puertos abiertos (API:8000, DBs).
    *   `production`: Red interna aislada, expuesto vía **Traefik**.
*   **Configuración**: Variables de entorno (`.env`) gestionadas por `pydantic-settings`.
