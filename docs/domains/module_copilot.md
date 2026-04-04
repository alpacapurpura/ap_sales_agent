---
module: Copilot
status: active
---

# Copilot

Asistente flotante in-app (estilo Cursor) que acompana al dueno del negocio por toda la interfaz. Autocompleta formularios, analiza estilo de comunicacion, extrae informacion de sitios web, y guia la configuracion del SaaS usando LangGraph con tool calling dinamico.

## Conceptos de Dominio

- **Procedures:** Workflows multi-paso declarativos (first_setup, brand_setup, offer_creation). Cada paso referencia un module_id del MODULE_REGISTRY y una section_id opcional. La completitud se verifica dinamicamente via schema_introspection — nunca se hardcodean campos.
- **MODULE_REGISTRY:** Fuente unica de verdad sobre que modulos puede leer el copilot. Cada ModuleDescriptor declara: model_class (para introspeccion Pydantic), repo_factory, read_fn, keywords. Registra: brand, offer, connections, crm, analytics, sales_agent, commercial_calendar, landing.
- **schema_introspection:** Descubre secciones y campos de cualquier modelo Pydantic via model_fields. Genera CompletionStatus (filled/total/is_configured) sin hardcodear nombres de campos — campos nuevos son auto-descubiertos.
- **Proactive Nudges:** Sugerencias contextuales basadas en completitud de modulos y ruta actual. Reglas: EmptyModuleNudge (modulo vacio), CrossModuleGapNudge (brand listo pero offer no), IncompleteModuleNudge (<30%). Cache in-memory 5 minutos.

## Decisiones de Arquitectura

- **ReAct loop (LangGraph):** Ciclo simple: LLM genera respuesta -> si tiene tool calls, ejecutarlos y volver al LLM -> si no, responder al usuario y END. No hay estado complejo de grafo como en sales_agent.
- **Tool selection por ruta:** ROUTE_TOOL_MAP mapea prefijos de ruta del frontend a grupos de tools. Ejemplo: "growth-studio" activa analytics + crm tools pero no mutation tools. Esto reduce ruido para el LLM y previene acciones no deseadas en contextos incorrectos.
- **12 grupos de tools:** navigation, awareness, mutation, module_data, analytics, crm, sales_agent, connections, landing, procedure, knowledge, offer_ladder. Cada grupo es una lista de LangChain tools importada en el registry.
- **Sub-agentes especializados:** style_analyzer (analiza tono, frases firma, densidad de emojis del usuario) y web_extractor (scraping + extraccion estructurada de sitios web). Ambos son grafos LangGraph independientes invocados desde tools del copilot.
- **Knowledge ingestion:** Documentos se chunquean (800 chars, 200 overlap via RecursiveCharacterTextSplitter), se embeden y se upsertean en Qdrant. Tambien genera auto-summaries desde Brand+Offer+Connections para el scope "help".
- **Behavior tracking:** El system prompt incluye un resumen de comportamiento del usuario (propuestas aceptadas/rechazadas, nudges, navegaciones, busquedas RAG, procedimientos abandonados) para personalizar respuestas.

## Frontend (Implementado)

El frontend del copilot esta completamente implementado con 23+ archivos:
- **CopilotPanel/CopilotRail/CopilotChat:** UI del chat flotante con panel deslizable.
- **WithCopilot:** Wrapper HOC que hace cualquier campo de formulario "copilot-aware" — muestra boton "+ a Copilot" en hover, borde morado cuando esta seleccionado como contexto.
- **useCopilotFieldSync:** Hook que escucha eventos `copilot:field-update` (CustomEvent) y actualiza el formulario via React Hook Form setValue.
- **useProactiveNudges/NudgeBanner:** Consulta el endpoint /nudge-context y muestra banners contextuales.
- **Rich messages:** AssistantMessage, ProposalCard, ComparisonTable, MetricSummaryCard, NavigationCard, ProgressChecklist, MultiOptionSelector — el copilot renderiza respuestas estructuradas, no solo texto plano.
- **copilot-store (Zustand):** Estado global del copilot: selectedFields, panel open/closed, mensajes.

## Reglas de Negocio

- El copilot es COMPLETAMENTE aislado del sales_agent — distinto estado, distinto proposito (configuracion vs ventas), distintos prompts.
- NUNCA hardcodear nombres de campos en tools del copilot — usar schema_introspection y MODULE_REGISTRY. Campos nuevos se descubren automaticamente.
- Los procedures verifican completitud consultando el MODULE_REGISTRY en tiempo real — no cachean el estado de completitud.
- El system prompt se enriquece con completion_snapshot + behavior_summary + lista de modulos + tools activos en cada invocacion.

## Casos Borde

- **Cloudflare/403 en web_extractor:** El scraping falla silenciosamente cuando el sitio del cliente tiene proteccion anti-bot. No hay fallback automatico — el usuario debe proveer la informacion manualmente.
- **Pydantic ValidationError en mutations:** El LLM puede intentar escribir tipos incorrectos (string a campo Enum). Los mutation tools deben validar via Pydantic antes de persistir.
- **Tool no encontrada:** Si el LLM invoca un tool que no existe en el route scope actual, tool_executor_node devuelve un error message en vez de crashear. El all_tools fallback cubre este caso.
- **Cache de nudges stale:** El cache in-memory de nudges (5 min) puede mostrar sugerencias desactualizadas si el usuario completa un modulo y regresa inmediatamente a la misma ruta.

## CRITICAL — No Violar

- NUNCA importar tools de otros modulos directamente en el copilot — usar MODULE_REGISTRY como intermediario (excepcion permitida por regla DDD: copilot es infra-like).
- NUNCA agregar un modulo nuevo sin registrarlo en module_registry.py — el copilot no lo descubrira.
- NUNCA agregar rutas nuevas sin actualizar ROUTE_TOOL_MAP en registry.py + navigation_map.py — los tools no se activaran en esa ruta.
- El frontend usa CustomEvent (`copilot:field-update`) para sincronizar campos — NO usar state global ni props directos entre copilot y features.
