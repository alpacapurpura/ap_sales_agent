---
alwaysApply: true
---
# Arquitectura: Visionarias Agent

## Filosofía
Python 100%. Code-First. Flujo determinista con LangGraph (Máquina de Estados).

## Estructura de Capas
1. Canales: `src/channels`. Adapters I/O (WA/TG).
2. API: `src/api`. Webhooks.
3. Core: `src/core`. Lógica cognitiva, Nodos, Estado.
4. Servicios: `src/services`. DB, Vector Store.

## Mapa de Navegación

| Necesidad | Ruta |
|---|---|
| Ventas & Copy | `src/core/nodes.py`, `src/core/prompts/templates/` |
| Datos Usuario | `src/core/state.py` (Memoria), `src/services/models.py` (DB) |
| Integraciones | `src/channels/`, `src/api/routes.py` |
| IA & RAG | `src/services/router_service.py`, `src/services/vector_store.py` |
| Admin | `src/admin/app.py` |

## Reglas Críticas
* Cero Alucinaciones: LLM NUNCA calcula precios.
* Financial Enforcer: Cálculo determinista obligatorio (usa DB).
* RAG Contextual: Filtra chunks por estado del grafo.
* Agnosticismo: El Core desconoce el canal (WA/TG).
