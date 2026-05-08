---
name: architect-agentic
description: "Instruction doc Agentic (NO es agent type spawnable — es contexto que `architect-orchestrator` carga cuando story toca copilot/sales_agent). Define qué debe contener la sección AGENTIC de 03-arch.md: tools defs (Pydantic schema), prompt slot architecture, LangGraph state, eval suite path, personas/rubrics asignados, observabilidad (trace + cost), trial policy. Skills cargadas: sales-agent-expert, copilot-expert, tessl__langgraph, claude-api. NUNCA invocar como subagent_type — el orchestrator lee este SKILL.md como guidance contextual."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch, WebFetch
---

# /architect-agentic — Agentic instruction doc (contextual guidance for architect-orchestrator)

> **NO es agent type spawnable.** Solo `architect-orchestrator` existe en `.claude/agents/`. Este SKILL.md sirve como guidance contextual que el orchestrator carga cuando la story toca AGENTIC surface — NO se invoca via Agent tool.

> Owner: `03-arch-agentic.md`. Diseño técnico de la capa agentic (LangGraph state, tools, prompt slots, evals). Output → /architect orchestrator.

## Step 0 — Date check (DATE-AWARE)

```bash
date -u +%Y-%m-%d   # captura para WebSearch + Research Notes
```

Knowledge cutoff Opus 4.7 = Jan 2026. Para LangGraph 2.0 / deepagents / Anthropic prompt caching state-of-the-art post-cutoff → WebSearch con `{current_year}` interpolated o WebFetch canonical docs.

## Skills cargados (HARD GATE)

- `copilot-expert` (si copilot)
- `sales-agent-expert` (si sales_agent)
- `tessl__langgraph` — LangGraph 2.0 patterns
- `claude-api` — Anthropic SDK + prompt caching
- `tessl__graceful-degradation` — recovery
- `tessl__pytest-api-testing` — async test fixtures

## Workflow

### Step 1 — Cross-module audit

```bash
grep -rn "<keyword>" backend/src/shared/agent_observability/
grep -rn "<keyword>" backend/src/shared/infrastructure/llm/
grep -rn "<keyword>" backend/src/modules/{copilot,sales_agent}/
```

Inventario shared abstractions (`.claude/rules/anti-duplication.md`):
- Observability turn envelope → `shared/agent_observability/recording/turn_envelope.py`
- Callback handler → `BaseAgentCallbackHandler`
- PII sanitization → `shared/agent_observability/recording/sanitization.py`
- FX resolver → `FXResolver.default()`
- Pricing resolver → `shared/agent_observability/cost/`
- LLM router + providers → `shared/infrastructure/llm/router.py` + `providers/`
- Tenant billing config → `shared/agent_observability/persistence/`
- Channel format registry → `shared/agent_observability/channels/`

Si tu propuesta requiere nuevo provider / nueva abstraction cross-module → EXTEND, NO mirror local.

### Step 2 — Diseño técnico

Seguir template `docs/specs/templates/03-arch-template.md` con surface=AGENTIC. Llenar:

**Tool definitions:**

```python
# backend/src/modules/{m}/tools/{tool_name}.py
class FetchOfferInput(BaseModel):
    offer_id: str
    tenant_id: str  # ALWAYS

@tool(args_schema=FetchOfferInput)
async def fetch_offer(offer_id: str, tenant_id: str) -> str:
    """Docstring para LLM — qué hace, inputs, outputs claramente."""
    offer = await offer_service.get_by_id(offer_id, tenant_id=tenant_id)
    return offer.summary()
```

Reglas tools:
- `@tool` decorator + Pydantic input schema
- `tenant_id` parameter ALWAYS
- Async signatures
- Llaman SERVICES (no raw repos)
- External HTTP wrapped en `tessl__graceful-degradation` (timeout + fallback + circuit breaker)
- Retorno serializable (str o Pydantic)

**Prompt slot architecture:**

```
SLOT 1 (cacheable, TTL 1h): identity preamble
SLOT 2 (cacheable, TTL 5min): tool registry
SLOT 3 (NOT cached): task instructions
SLOT 4 (NOT cached): user input
SLOT 5 (cacheable, TTL 1h): brand_voice (sales_agent only — SSoT personality_profiles.system_instruction)
                             ↑ cache_control marker ↑
SLOT 6 (NOT cached): conversation history
```

TTL choice justificado en 03-arch-agentic.md.

Forbidden in cache prefix (cualquier cacheable slot):
- Timestamps
- Conversation IDs
- Turn counters
- Random IDs
- Tenant name interpolated mid-block

**LangGraph state:**

```python
from typing import TypedDict, Annotated, Sequence
from langgraph.graph.message import add_messages
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tenant_id: str                       # ALWAYS — tenant isolation
    conversation_id: str
    iterations: int                      # max-iter guard
    accumulated_findings: Annotated[list[dict], operator.add]  # parallel-safe reducer
```

**Nodes + edges:**

| Node | Async fn signature | Returns | Edge type |
|---|---|---|---|
| `route` | `async def route(state) -> dict` | `{"next_specialist": str, "iterations": +1}` | conditional |
| `specialist` | `async def specialist(state) -> dict` | `{"messages": [...]}` | direct → synth |
| `synth` | `async def synth(state) -> dict` | `{"messages": [final], "task_complete": True}` | → END |

Conditional edges total — every branch reaches END. Max-iter exit explicit.

**Topology:**

- [ ] Single ReAct agent
- [ ] Supervisor pattern (`langgraph_supervisor.create_supervisor`)
- [ ] deepagents `task` tool with subagents (SubAgentMiddleware filtering)

**Checkpointer:**

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
checkpointer = AsyncPostgresSaver.from_conn_string(settings.postgres_dsn)
graph = builder.compile(checkpointer=checkpointer)
```

**NEVER MemorySaver en producción.**

**Eval suite:**

```python
# backend/tests/agentic_evals/{m}/{story_id}_eval.py

import pytest
from agentic_eval_runner import run_trial

@pytest.mark.asyncio
async def test_happy_path():
    persona = load_persona("docs/specs/personas/tenant-novato-tech.yaml")
    rubrics = [
        load_rubric("docs/specs/rubrics/completeness.md"),
        load_rubric("docs/specs/rubrics/voice-fidelity.md"),
        load_rubric("docs/specs/rubrics/no-hallucination.md"),
    ]

    results = await run_trial(
        scenario_id="happy-path-typical-persona",
        persona=persona,
        rubrics=rubrics,
        trials=3,
    )

    pass_k = sum(r.passed for r in results) / len(results)
    assert pass_k >= 0.5, f"Pass^3 {pass_k} below threshold 0.5"
```

**Trial policy** (lift desde story YAML):
```yaml
trials_per_scenario: 3
per_trial_pass_threshold: 0.66
pass_k_threshold: 0.5
```

**Observabilidad mandatory:**

```python
# Every LLM call MUST be wrapped:
async def call_llm_with_observability(client, model, messages, tenant_id, conversation_id, node_name):
    # ... timeout + fallback ...
    response = await client.messages.create(...)

    # Cost recording (best-effort try/except)
    try:
        await llm_call_recorder.write(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            node_name=node_name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_creation_input_tokens=response.usage.cache_creation_input_tokens,
            cache_read_input_tokens=response.usage.cache_read_input_tokens,
            cost_usd=compute_cost(...),
        )
    except Exception as e:
        logger.warning("llm_call_recording_failed", error=str(e))  # never break turn

    # Trace event (best-effort)
    try:
        await trace_recorder.emit("llm_call", { ... PII sanitized ... })
    except Exception as e:
        logger.warning("trace_emit_failed", error=str(e))

    return response
```

**Validation hooks:**
- `cache_read_input_tokens > 0` on iter 2+ (else silent invalidator)
- `cost_usd <= budget_usd` per session
- TTFT p95 < 2s

### Step 3 — Default-flip detection

Si tu propuesta toca `core/config.py` defaults agentic-controlled (`USE_OUTBOX_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`):

→ Llenar § 9.5 Tests audit en 03-arch-agentic.md (igual que /architect-be).

### Step 4 — Hand off

Output al orchestrator:
```
done -> docs/product/stories/{story-id}/03-arch-agentic.md
```

## Anti-patterns

- ❌ Hardcoded model names — use `llm_router.get_for_role(...)`
- ❌ `MemorySaver` en producción
- ❌ Naked LLM calls (sin observability wrapper)
- ❌ Cache prefix con timestamps/conversation_id (silent invalidator)
- ❌ `cache_control` marker en non-final cacheable block
- ❌ Tools sin `tenant_id`
- ❌ Tools llamando raw repos (use services)
- ❌ Voseo en copilot UI strings (sales_agent SÍ respeta voz tenant)
- ❌ Hardcoded brand voice (use `personality_profiles.system_instruction`)
- ❌ Skip eval goldens en sales_agent specialist nuevo
- ❌ Nuevo Qdrant client (use `KnowledgeService`)
- ❌ Mirror layer cuando shared existe (anti-duplication)
- ❌ Diseñar BE business surface (eso es /architect-be)
- ❌ Diseñar FE (eso es /architect-fe)

## Output format

Single artifact: `03-arch-agentic.md`. Self-contained. Builder agentic lee SOLO esto + handoff + spec.
