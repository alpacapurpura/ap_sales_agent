---
alwaysApply: true
---
# Stack Tecnológico

## Core
* Lenguaje: Python 3.11+ (Tipado Estricto).
* API: `FastAPI`. Modelos Pydantic v2 para validación I/O.
* Orquestación: `LangGraph`. Máquinas de estado complejas.
* LLM: Multi-Provider Factory (`OpenAI` GPT-4 / `Gemini` 1.5). Configurable por entorno.

## Infraestructura de Datos
* Vectorial: `Qdrant`. Payload Filtering obligatorio.
* Embeddings Locales: Caché PERSISTENTE obligatorio en volumen Docker (e.g., `/app/model_cache`). Prohibido descargar en runtime a `/tmp`.
* Estado: `Redis`. Persistencia de sesión y `AgentState`.
* Logs: `PostgreSQL`. Auditoría y Telemetría.
* ORM: `SQLAlchemy`.
* Templating: `Jinja2` para prompts (.j2).

## Despliegue & Dev
* Docker: Perfiles `development` y `production`.
* Tunneling: `Cloudflare Tunnel` para exponer entorno local (Webhooks).
* Gateway: `Traefik` para enrutamiento en producción.
* Config: `pydantic-settings` (.env).

## Reglas de Dependencias
* Versiones: Pinneadas en `requirements.txt`.
* Migraciones: Scripts SQL o Alembic (si aplica) para cambios de esquema.
