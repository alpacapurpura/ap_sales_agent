---
module: Sales Agent
status: active
---

# Sales Agent

Agente de ventas autonomo multicanal (WhatsApp, Telegram, Instagram DM, ManyChat) que pre-califica leads, maneja objeciones, agenda citas y envia links de pago. Reemplaza a un SDR humano usando LangGraph, memoria dual y conocimiento dinamico del negocio.

## Conceptos de Dominio

- **Agent Knowledge System (AKS):** Documento de identidad renderizado dinamicamente desde Brand Studio + Offer Studio via TenantKnowledgeBuilder. Usa model_dump() para ser schema-resilient — campos nuevos fluyen automaticamente a los templates Jinja2 sin modificar el builder.
- **SemanticRouter:** Clasificador de intenciones por similitud coseno (fastembed, modelo multilingual). Rutas del sistema (security, objections, pains, desires, buying signals) siempre activas + rutas tenant-specific (trigger_phrases de objeciones del Offer) cacheadas por tenant.
- **SmartBufferService:** Debounce en Redis para mensajes rapidos. Acumula mensajes en una lista (RPUSH), guarda timestamp y canal. Usa lock distribuido (SET NX) para evitar procesamiento paralelo del mismo usuario.
- **OutputManager:** Simulacion de tipeo humano. Divide la respuesta en chunks (por parrafos), calcula delays basados en CPM + jitter, y envia con typing indicators. Strips bloques internos ([QUALIFICATION_DATA], [SIGNALS], [TOOL_REQUEST]) antes de enviar al usuario.

## Decisiones de Arquitectura

- **Supervisor -> Subgraph:** El orchestrator principal (graph.py) es un supervisor que delega al subgrafo de ventas (sales/graph.py). Disenado para agregar futuros subgrafos (soporte, onboarding) sin reescribir el flujo principal.
- **Memoria dual:** Qdrant (semantic memory) para busqueda por similitud de conocimiento del negocio + PostgreSQL (episodic memory via AuditRepository) para historial de conversacion. El vector store usa hybrid search (dense + sparse embeddings) con FlashRank reranking.
- **PromptLoader hibrido multitenant:** Resolucion de prompts: DB tenant-specific -> DB system default -> archivo J2 (fallback). Controlado por PROMPT_SOURCE (HYBRID/FILE/DB). Cache en memoria con TTL de 60s. Permite override de prompts por tenant sin deploy.
- **Checkpointing de estado:** AgentStateCheckpointModel persiste buying_signals, objection_history, qualification_answers, turn_count, close_strategy entre turns. Session timeout de 6h — al expirar, se desactiva el checkpoint y se crea uno nuevo.
- **Safety layer de dos fases:** Fase 1 (deterministica): regex configurable desde DB. Fase 2 (contextual): si la regla tiene context_instruction, se verifica con LLM rapido antes de reemplazar. Fail-safe: si el LLM falla, asume que SI es sensible (paranoid mode). Credit cards siempre se redactan por patron hardcoded.

## Reglas de Negocio

- El SemanticRouter DEBE evaluar security_breach primero — si detecta jailbreak (>=0.65 similarity), el agente no procesa el mensaje.
- Todo knowledge search en Qdrant DEBE filtrar por tenant_id en el payload — es la unica barrera de aislamiento en el vector store.
- Los buying_signals se acumulan (detect_and_accumulate) pero no se duplican por tipo en el mismo turn.
- El agente SIEMPRE genera una fallback_identity minima si falla la construccion del AKS — nunca debe quedar sin identidad.

## Casos Borde

- **5 mensajes rapidos:** Sin SmartBufferService, se disparan 5 ejecuciones paralelas del LLM. El lock (acquire_lock, 30s TTL) previene esto, pero si el lock expira antes de que termine el procesamiento, puede haber race condition.
- **Alucinacion de URLs:** El modelo puede inventar URLs de pago. Las herramientas (sales/tools.py) deben proveer URLs reales via tool calling estructurado.
- **Invalidacion de tenant routes:** Cuando se actualizan las ofertas, se debe llamar SemanticRouter.invalidate_tenant() para limpiar el cache de embeddings.
- **Tracing decorator:** trace_node() captura input/output state de cada nodo LangGraph. Si el tracing falla, el nodo sigue ejecutandose — el tracing nunca debe bloquear la conversacion.

## CRITICAL — No Violar

- NUNCA hardcodear prompts en nodos — usar prompt_loader.render() con templates J2. Las 4 violaciones criticas documentadas en el audit deben corregirse.
- NUNCA procesar un mensaje sin pasar por SmartBufferService primero — el debounce es esencial para evitar respuestas duplicadas.
- NUNCA exponer datos de un tenant en el vector store de otro — el filtro tenant_id en Qdrant es la unica proteccion.
- Los campos del checkpoint (buying_signals, objection_history) son JSONB — nunca reemplazarlos completos sin merge con el estado previo.
