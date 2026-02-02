# Arquitectura de Sistema Agentic Multi-Tenant (SOTA 2026)

Este documento describe la arquitectura técnica y los patrones de diseño implementados para transformar el sistema en una solución SaaS Multi-Tenant robusta, segura y escalable.

## 1. Visión General
El sistema ha evolucionado de un chatbot monolítico a una **Arquitectura Cognitiva Distribuida y Multi-Tenant**. 
Esto permite servir a múltiples clientes (Tenants) desde una única infraestructura, garantizando el aislamiento total de sus datos y personalizando la "Identidad" del agente dinámicamente.

### Principios Clave (2026 Standards)
1.  **Strict State Isolation**: El estado del agente (`AgentState`) es la única fuente de verdad.
2.  **Logical Sharding**: Los datos vectoriales conviven en una sola colección pero están particionados lógicamente por `tenant_id` a nivel de motor (Qdrant).
3.  **Dynamic Persona Injection**: La personalidad no está hardcodeada; se inyecta en tiempo de ejecución desde la configuración del Tenant.
4.  **System 2 Thinking**: Uso de patrones de reflexión (Critic Node) y razonamiento (Chain of Thought) antes de actuar.

---

## 2. Estrategia Multi-Tenant

### A. Aislamiento de Datos (Postgres & Qdrant)
Implementamos un modelo de **Base de Datos Compartida, Esquema Compartido** (Shared Database, Shared Schema) para máxima eficiencia operativa, con aislamiento lógico estricto.

*   **Postgres (`Tenant` Model):**
    *   Cada cliente tiene un registro en la tabla `tenants`.
    *   Columna `config_json`: Almacena la configuración de identidad (Nombre del bot, tono, reglas de negocio).
    *   **Beneficio:** Permite cambiar el comportamiento del agente sin desplegar código (Hot-Swap).

*   **Vector Store (Qdrant):**
    *   **Estrategia:** Single Collection + Payload Partitioning.
    *   **Seguridad:** La función `search_knowledge_base` ahora **exige** un `tenant_id`.
    *   **Implementación:** Se inyecta un filtro `must: [{ key: "tenant_id", match: { value: <ID> } }]` en cada query. Esto hace imposible que el Cliente A recupere documentos del Cliente B.

### B. Inyección de Contexto (Prompt Engineering)
Abandonamos los prompts estáticos ("Eres Visionaria") por plantillas dinámicas Jinja2.

*   **Motor de Prompts (`PromptLoader`):**
    *   Detecta el `tenant_id` del contexto actual.
    *   Carga la configuración del Tenant (`brand_name`, `agent_persona`).
    *   Inyecta estas variables en el template `sales_system.j2`.
    *   **Resultado:** El mismo código sirve para "Visionarias" (Empático/Mujeres) y "TechCorp" (Formal/B2B) simplemente cambiando el JSON de configuración.

---

## 3. Arquitectura del Agente (LangGraph)

El cerebro del sistema es un grafo de estados (`StateGraph`) que orquesta la conversación.

### Nodos Principales
1.  **Router Node:**
    *   Analiza la intención del usuario usando FastEmbed (local, <10ms).
    *   Detecta riesgos de seguridad (Jailbreaks) con Regex.
    *   Decide si ir al flujo de ventas o responder una FAQ.

2.  **Manager Node (Cerebro):**
    *   Ejecuta razonamiento complejo (Chain of Thought).
    *   Decide la transición de estado del embudo (e.g., de `Discovery` a `Pitch`).
    *   Genera resúmenes de memoria episódica.

3.  **Generator Node (La Voz):**
    *   **RAG Pipeline:** Ejecuta HyDE (Hypothetical Document Embeddings) -> Búsqueda Híbrida (Qdrant) -> Reranking (FlashRank).
    *   **Persona Injection:** Lee `state["tenant_config"]` y adopta la personalidad adecuada ("Closer", "Empática", "Estratega").
    *   Genera la respuesta final.

4.  **Critic Node (Reflexion):**
    *   Evalúa la respuesta generada antes de enviarla.
    *   Si detecta alucinaciones o tono incorrecto, rechaza la respuesta y fuerza una revisión.

---

## 4. Flujo de Datos (Request Lifecycle)

1.  **API Request:** Llega un mensaje a `/chat`. Middleware resuelve el `tenant_id` (vía API Key o Header).
2.  **State Init:** Se crea el `AgentState` inicial cargando el perfil del usuario y la `tenant_config` desde Postgres.
3.  **LangGraph Execution:**
    *   El agente navega el grafo.
    *   En cada paso, tiene acceso a `state["tenant_config"]`.
    *   Al consultar Qdrant, pasa el `state["tenant_id"]`.
4.  **Response:** Se envía la respuesta generada y validada.

---

## 5. Guía para Desarrolladores

### Cómo agregar un nuevo Tenant
1.  Ir al Panel de Admin (`/admin`).
2.  Crear un nuevo Tenant.
3.  Configurar el JSON (Nombre, Tono, Precios).
4.  Subir sus documentos PDF en la pestaña "Conocimiento".
5.  ¡Listo! El agente ya funciona con la nueva identidad y datos.

### Cómo modificar la lógica del agente
*   **Lógica de Negocio:** Editar `backend/src/core/agents/orchestrator/nodes.py`.
*   **Prompts:** Editar `backend/src/core/prompts/templates/*.j2`. Recuerda usar variables `{{ variable }}` en lugar de texto fijo.

### Glosario
*   **RAG (Retrieval-Augmented Generation):** Técnica para dar memoria al LLM usando documentos externos.
*   **HyDE:** Generar una respuesta falsa para buscar documentos reales similares semánticamente.
*   **LangGraph:** Framework para construir agentes como grafos cíclicos.
*   **Tenant:** Un cliente o organización que usa el sistema.
