# Plan Final de Ejecución: Arquitectura Multi-Tenant & Documentación

Confirmado el enfoque "SOTA 2026", procederé a la implementación técnica y documental.

## 1. Infraestructura de Datos (Postgres & Qdrant)
- **Tenant Model:** Agregar columna `config_json` en `backend/src/services/db/models/tenant.py` para almacenar la configuración de identidad (branding, tono, reglas).
- **Migration:** Crear script/lógica para asegurar que el tenant "Visionarias" tenga su configuración inicial en este JSON.
- **Vector Store:** Refactorizar `backend/src/services/vector_store.py` para hacer **obligatorio** el `tenant_id` en `search_knowledge_base`, garantizando aislamiento lógico.

## 2. Motor de Prompts y Configuración
- **PromptLoader:** Actualizar `backend/src/core/prompts/base.py` para inyectar `tenant.config_json` en las plantillas Jinja2.
- **Refactorización de Templates:** Modificar `sales_system.j2` reemplazando textos hardcoded ("Visionarias") por variables (`{{ company_name }}`, `{{ agent_name }}`).

## 3. Lógica del Agente (LangGraph)
- **AgentState:** Actualizar el esquema de estado para incluir `tenant_config`.
- **Nodos:** Modificar `backend/src/core/agents/orchestrator/nodes.py` para leer la configuración del estado en lugar de usar constantes, y pasar el `tenant_id` a las herramientas de búsqueda.

## 4. Documentación y Explicabilidad (Nuevo Requisito)
- **Comentarios en Código:** Agregar Docstrings detallados y comentarios explicativos ("Why this pattern?") en las secciones críticas refactorizadas.
- **Documento de Arquitectura:** Crear `docs/architecture/agentic_system_2026.md` que explique:
  - Diseño del Grafo y Nodos.
  - Estrategia de Multi-tenancy (Postgres + Qdrant).
  - Patrones utilizados (Reflexion, Context Injection).
  - Glosario de términos técnicos.

Procederé con la ejecución de estos pasos en orden secuencial.