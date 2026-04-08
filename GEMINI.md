# GEMINI.md

## Proyecto: Visionarias Brain (AI Sales Agent)

Sistema de agente de ventas basado en IA, con arquitectura "Code-First" que utiliza Python, FastAPI y LangGraph, diseñado para eliminar dependencias externas (Low-Code/n8n) y optimizar la latencia.

## Arquitectura
*   **Core:** Python, FastAPI, LangGraph (Máquina de estados determinista).
*   **RAG:** Integración con Qdrant para recuperación de contexto.
*   **Telemetría:** Logs estructurados en PostgreSQL.
*   **Infraestructura:** Dockerizado con perfiles de desarrollo y producción; pensado para ejecutarse detrás de un gateway (Traefik).

## Comandos Principales
Gestionados a través de `Makefile`:

- `make setup`: Preparación inicial (creación de carpetas de datos/logs con permisos correctos).
- `make dev`: Entorno de desarrollo (Hot-reload, puertos expuestos).
- `make prod`: Entorno de producción (Usa `docker-compose.prod.yml`).
- `make stop`: Detener servicios.
- `make fix-permissions`: Reparar problemas de propiedad en archivos generados por Docker.

### Gestión de Shopify (Carriles de Configuración)
El proyecto utiliza configuraciones diferenciadas para desarrollo y producción:

- `make shopify-config-dev`: Activa configuración de desarrollo.
- `make shopify-config-prod`: Activa configuración de producción.
- `make shopify-config-status`: Muestra la configuración activa (nombre, URL, client_id).

*Nota:* Antes de realizar cualquier cambio, verifica siempre el carril activo.

## Convenciones y Flujos de Trabajo
- **Seguridad en Shopify:** Sigue rigurosamente los Runbooks definidos en `README.md` para evitar impactos en la distribución de la app.
- **Desarrollo:** Siempre trabajar en el carril `dev`.
- **Despliegue:** Seguir el "Gate de release" definido en la documentación antes de promover al carril `prod`.

## Estructura de Directorios
- `backend/`: Código fuente principal (FastAPI, servicios, tests).
- `frontend/`: Aplicación frontend (Next.js, Playwright).
- `shopify_app/`: Configuración y lógica específica para la integración con Shopify.
- `workers/`: Funciones serverless para tareas como notificaciones de Sentry a Slack.
- `.claude/`: Configuración específica para agentes y herramientas de desarrollo.
