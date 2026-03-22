# 06 — LangGraph Architecture

## Vision General

El Sales Agent usa **LangGraph** (de LangChain) para modelar su flujo de decision como un grafo dirigido con estado. La arquitectura tiene dos niveles: un **Main Workflow** (supervisor general) y un **Sales Subgraph** (especialistas de ventas).

```
┌─────────────────────────────────────────────┐
│           MAIN WORKFLOW (graph.py)           │
│                                             │
│   ┌────────────┐                            │
│   │ supervisor  │ ← Entry point             │
│   │ (routing)   │                            │
│   └─────┬──────┘                            │
│         │ next_node = "sales_agent"          │
│   ┌─────▼──────────────────────────┐        │
│   │   SALES SUBGRAPH (sales/graph) │        │
│   │                                │        │
│   │   ┌────────────┐              │        │
│   │   │ supervisor  │              │        │
│   │   │ (LLM route) │              │        │
│   │   └──┬──┬──┬───┘              │        │
│   │      │  │  │                   │        │
│   │   ┌──▼┐┌▼──▼┐┌──────┐        │        │
│   │   │ Q ││ PE ││  C   │        │        │
│   │   └───┘└────┘└──────┘        │        │
│   │      │  │  │                   │        │
│   │      └──┴──┘ → END            │        │
│   └────────────────────────────────┘        │
│                  │                           │
│                 END                          │
└─────────────────────────────────────────────┘

Q = Qualifier | PE = Product Expert | C = Closer
```

---

## 1. AgentState (Estado Compartido)

**Archivo:** `backend/src/modules/sales_agent/application/orchestrator/state.py` (L4-45)

```python
class AgentState(TypedDict):
    # Messaging
    messages: List[Dict[str, Any]]        # [{"role": "user", "content": "..."}]

    # Routing
    next_node: Optional[str]              # Decisión del supervisor

    # Context
    user_id: Optional[UUID]
    tenant_id: Optional[UUID]
    session_id: Optional[str]

    # Agent Memory
    current_state: Optional[str]          # "rapport", "discovery", "closing"
    detected_intent: Optional[str]        # Del SemanticRouter
    lead_score: Optional[int]

    # Lead Data
    lead_data: Optional[Dict[str, Any]]   # {"name": "...", "budget": "..."}

    # Configuration
    tenant_config: Optional[Dict[str, Any]]
    history: List[Dict[str, Any]]         # Ultimas 10 interacciones
    user_profile: Optional[Dict[str, Any]]

    # Session Status
    session_active: bool
    active_enrollment: Optional[Dict[str, Any]]
    active_product: Optional[Dict[str, Any]]
    last_intent: Optional[str]
    launch_stage: Optional[str]

    # AKS
    agent_identity: Optional[str]         # Rendered identity prompt

    # Errors
    error: Optional[str]
```

### create_initial_state Factory (L46-97)
```python
def create_initial_state(...) -> AgentState:
    return {
        "messages": [],
        "next_node": None,
        "current_state": "rapport",    # Default: inicio de conversación
        "detected_intent": None,
        "lead_score": 0,
        "lead_data": lead_data or {},
        "tenant_config": tenant_config or {},
        "history": history or [],
        "session_active": session_active,
        "agent_identity": agent_identity,
        ...
    }
```
- **`current_state = "rapport"`:** Default. El agente siempre empieza en modo rapport (construccion de relacion).
- **UUIDs con manejo de error:** Si el conversion a UUID falla, se pone `None` en vez de crashear.

---

## 2. Main Workflow

**Archivo:** `backend/src/modules/sales_agent/application/orchestrator/graph.py` (L1-43)

```python
@trace_node("main_supervisor")
def supervisor_node(state: AgentState):
    """Main entry point. Routes to sub-agents."""
    return {"next_node": "sales_agent"}  # Pass-through for now

@trace_node("sales_agent_subgraph_wrapper")
def sales_agent_node(state: AgentState):
    """Wraps the Sales Subgraph."""
    result = sales_app.invoke(state)
    return result

# Graph Construction
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sales_agent", sales_agent_node)
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges("supervisor", lambda x: x["next_node"],
    {"sales_agent": "sales_agent", "end": END})
workflow.add_edge("sales_agent", END)
agent_app = workflow.compile()
```

### Por que un supervisor de "pass-through"?
El diseno es **forward-looking**. Actualmente solo existe el sub-agente de ventas, pero la arquitectura soporta:
- **Support Agent:** Para post-venta, soporte tecnico
- **Content Agent:** Para distribucion de contenido
- **Retention Agent:** Para reactivacion de clientes frios

Cuando se agreguen, el supervisor usara un LLM para decidir a cual agente rutear (similar al sales supervisor).

### trace_node Decorator
Cada nodo esta decorado con `@trace_node("nombre")`. Esto:
1. Crea un registro en `agent_traces` antes de ejecutar el nodo
2. Captura input/output state
3. Mide tiempo de ejecucion
4. Setea `current_trace_id` en contextvars para que los LLM logs se attachen

Ver [11-OBSERVABILITY.md](11-OBSERVABILITY.md).

---

## 3. Sales Subgraph

**Archivo:** `backend/src/modules/sales_agent/application/agents/sales/graph.py` (L1-43)

```python
def create_sales_subgraph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", node_sales_supervisor)
    workflow.add_node("qualifier", node_qualifier)
    workflow.add_node("product_expert", node_product_expert)
    workflow.add_node("closer", node_closer)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges("supervisor", lambda x: x["next_node"],
        {"qualifier": "qualifier", "product_expert": "product_expert",
         "closer": "closer", "scheduler": "closer"})  # scheduler fallback

    workflow.add_edge("qualifier", END)
    workflow.add_edge("product_expert", END)
    workflow.add_edge("closer", END)

    return workflow.compile()

sales_app = create_sales_subgraph()
```

### Flujo
```
supervisor (LLM routing) → qualifier | product_expert | closer → END
```

- **Single turn:** Los workers ejecutan 1 turno y terminan. No hay loop back al supervisor.
- **Scheduler fallback:** `"scheduler": "closer"` — mientras el scheduler no este implementado, las solicitudes de agendar van al closer.

---

## 4. Sales Nodes (Nodos Especialistas)

**Archivo:** `backend/src/modules/sales_agent/application/agents/sales/nodes.py` (L1-95)

### node_sales_supervisor (L17-49) — El Router LLM
```python
@trace_node("sales_supervisor")
def node_sales_supervisor(state: AgentState) -> Dict[str, Any]:
    intent = state.get("detected_intent", "unknown")
    stage = state.get("current_state", "rapport")

    system_prompt = prompt_loader.render("supervisor_routing",
        intent=intent, lead_score=state.get("lead_score", 0),
        stage=stage, lead_data=state.get("lead_data"),
        user_profile=state.get("user_profile"))

    decision = LLMFactory.get_service().generate_response(
        messages=state["messages"][-3:],     # Solo ultimos 3 mensajes
        system_prompt=system_prompt,
        model_type="fast",                   # Modelo rápido
        temperature=0.0,                     # Determinístico
        max_output_tokens=10,                # Solo 1 palabra
        metadata={"prompt_template": "supervisor_routing"},
    )

    decision = decision.strip().lower().replace('"', '')
    valid_nodes = ["qualifier", "product_expert", "closer", "scheduler"]
    if decision not in valid_nodes:
        decision = "closer" if stage == "closing" else "qualifier"

    return {"next_node": decision}
```

**Decisiones de diseno:**
- **model_type="fast":** Usa el modelo mas rapido (GPT-4o-mini, Haiku) porque solo necesita decidir 1 palabra.
- **temperature=0.0:** Queremos routing determinista. No queremos "creatividad" en la decision.
- **max_output_tokens=10:** Safeguard — solo necesita 1 palabra pero dejamos margen.
- **Fallback inteligente:** Si la decision no es valida, va a "closer" si estamos en fase de closing, o "qualifier" si estamos al inicio.

### node_qualifier (L53-63)
```python
@trace_node("qualifier")
def node_qualifier(state: AgentState) -> Dict[str, Any]:
    skill_prompt = prompt_loader.render("specialist_qualifier")
    system_prompt = _build_system_prompt(state, skill_prompt)  # identity + skill
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type="smart",        # Modelo inteligente (GPT-4o, Sonnet)
        temperature=0.2,           # Algo de variabilidad, pero controlado
    )
    return {"messages": [{"role": "assistant", "content": response}]}
```

### node_product_expert (L67-80)
```python
@trace_node("product_expert")
def node_product_expert(state: AgentState) -> Dict[str, Any]:
    skill_prompt = prompt_loader.render("specialist_product_expert",
        context_rag=state.get("context_rag"))  # RAG context si disponible
    system_prompt = _build_system_prompt(state, skill_prompt)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type="smart", temperature=0.2)
    return {"messages": [{"role": "assistant", "content": response}]}
```

### node_closer (L84-95)
```python
@trace_node("closer")
def node_closer(state: AgentState) -> Dict[str, Any]:
    skill_prompt = prompt_loader.render("specialist_closer")
    system_prompt = _build_system_prompt(state, skill_prompt)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type="smart",
        temperature=0.4)  # Más creatividad para closing
    return {"messages": [{"role": "assistant", "content": response}]}
```

**Nota sobre temperature:**
- **Qualifier (0.2):** Preguntas deben ser consistentes y relevantes.
- **Product Expert (0.2):** Informacion debe ser precisa.
- **Closer (0.4):** Mas creatividad para persuasion y manejo de objeciones.

---

## 5. Patron de Composicion de Prompts

```
┌──────────────────────────────────────────┐
│ Nodo Qualifier                           │
│                                          │
│ system_prompt = (                        │
│   agent_identity.j2      ← PER-TENANT   │
│   +                                      │
│   specialist_qualifier.j2 ← ESTATICO    │
│ )                                        │
│                                          │
│ messages = [                             │
│   {"role": "user", "content": "Hola..."}│
│ ]                                        │
└──────────────────────────────────────────┘
```

La funcion `_build_system_prompt()` (`nodes.py:8-13`) combina:
1. **agent_identity:** Identidad del negocio (quien eres, que vendes)
2. **skill_prompt:** Instrucciones del rol (que hacer ahora)

Separados por `\n\n---\n\n`.

---

## Casuisticas

### Que pasa si el supervisor no puede decidir?
El fallback esta en `nodes.py:46-47`:
```python
if decision not in valid_nodes:
    decision = "closer" if stage == "closing" else "qualifier"
```
- En etapa temprana → Qualifier (sigue descubriendo)
- En etapa tardía → Closer (intenta cerrar)

### Se puede agregar un nodo nuevo (ej: Scheduler)?
Si. Solo se necesita:
1. Crear `node_scheduler` en `nodes.py`
2. Agregar `workflow.add_node("scheduler", node_scheduler)` en `sales/graph.py`
3. Cambiar el fallback de `"scheduler": "closer"` a `"scheduler": "scheduler"`
4. Crear `specialist_scheduler.j2` template

### Por que los workers van directo a END y no vuelven al supervisor?
Diseno de **single turn**: cada interaccion del usuario genera 1 respuesta. El "loop" natural es que el usuario responda y se procese un nuevo mensaje completo. Esto simplifica el grafo y evita loops infinitos.
