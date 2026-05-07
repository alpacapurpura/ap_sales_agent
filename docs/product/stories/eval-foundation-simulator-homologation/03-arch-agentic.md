---
story_id: eval-foundation-simulator-homologation
surface: AGENTIC
sub_architect: /architect-agentic (skill sales-agent-expert + tessl__langgraph + tessl__graceful-degradation)
arch_version: 1
last_modified: 2026-05-07T22:00:00Z
links:
  spec: 01-spec.md
  consolidated: 03-arch.md
  story_yaml: 00-story.md
  be_arch: 03-arch-be.md
  rules:
    - .claude/rules/anti-duplication.md
    - .claude/rules/sales-agent-brand-voice.md
    - .claude/rules/spanish-text.md
    - .claude/rules/architectural-fitness.md
---

> **Owner**: `builder-agentic` (Opus 4.7) for state machine + customer node + termination + schema migrations.
> Sonnet OK for tests/docs sobre agentic per R23 (`production_code: false` — todo bajo
> `backend/tests/agentic_evals/sales_agent/simulator/`).
> Patterns referenced are state-of-the-art **as of 2026-05-07** — sources cited in §15.

## Decisión arquitectónica clave

`backend/tests/agentic_evals/sales_agent/simulator/` es un **harness LangGraph
dual-LLM in-process** sobre `agent_app.ainvoke` con **API pública minimal de 7
nombres** (H9), **schema versioning forward-compatible** (H1), y **zero global
state** (H3) que escala a 1000+ tenants × 5 personas × 3 trials = 15k
simulations vía `asyncio.gather + Semaphore`. Customer LLM via `LLMFactory.get_service()`
con role nuevo `EVAL_USER_SIMULATOR` declarado en **eval-only registry**
(`simulator/_internal/llm_roles.py`) — NO en `LLM_ROLE_BY_SITE` SSoT (decisión
§2 abajo). Cost-bucket separation enforced por tabla DB aparte (BE arch §1)
+ callback handler subclass `EvalSimulatorCallbackHandler` que escribe a
`eval_simulator_llm_call`. Termination + schema versioning como **Strategy +
Registry patterns** (H8 + H1) permiten que stories I (adversarial) + H
(budget cap) + N futuras agreguen criterios sin tocar core.

## Cross-module audit (anti-duplication §0)

```bash
# 1. Mirror detection — observability paths
find backend -name "turn_envelope.py" -o -name "callback_handler.py" -o -name "agent_bridge.py" -o -name "customer_node.py" 2>/dev/null
# → backend/src/shared/agent_observability/recording/turn_envelope.py + base_callback_handler.py
# → backend/src/modules/{copilot,sales_agent}/observability/recording/{turn_envelope,callback_handler}.py
# → client_simulator/src/simulator/{customer_node,agent_bridge}.py (legacy preserve, D6)
# Decisión: REUSE shared verbatim. NEW classes son AGENT-SPECIFIC subclasses
# bajo `simulator/_internal/observability.py` (NO mirror — heredan).

# 2. SimulationState / ActorProfile / TerminationReason inexistentes
grep -rn "class SimulationState\b\|class ActorProfile\b\|class TerminationReason\b\|class AgentErrorSubtype\b" backend/src --include="*.py"
# → cero. NEW types en simulator/_internal/. Justificado: test infrastructure ONLY.

# 3. EVAL_USER_SIMULATOR
grep -rn "EVAL_USER_SIMULATOR" backend/src --include="*.py"
# → cero. NEW. Decisión §2 — NO en LLM_ROLE_BY_SITE (justificado below).

# 4. SCHEMA_MIGRATIONS / TERMINATION_POLICIES registries
grep -rn "TERMINATION_POLICIES\|SCHEMA_MIGRATIONS\|register_termination_policy" backend/src --include="*.py"
# → cero. NEW. Pattern: dict[name, callable].
```

**Anti-duplication verdict**: cero mirror. Cada shared abstraction reused via subclass:
- `BaseObservabilityContext` → subclass `EvalSimulatorObservabilityContext` (NEW, hereda de shared)
- `BaseAgentCallbackHandler` → subclass `EvalSimulatorCallbackHandler` (NEW, hereda)
- `FXResolver.default()` → reused as-is
- `PricingResolver` → reused as-is
- `sanitize_payload` → reused as-is
- `BaseTraceEventRepoProtocol` + `BaseLLMCallRepoProtocol` → impl by `EvalSimulatorTraceEventRepository` + `EvalSimulatorLlmCallRepository` (BE arch §2)

## §1 — LangGraph state machine architecture

### 1.1 SimulationState (Pydantic v2 BaseModel — D4)

Path: `backend/tests/agentic_evals/sales_agent/simulator/state.py`

```python
"""SimulationState — LangGraph Pydantic state for dual-LLM simulator.

Decisión D4 (spec): Pydantic-first state machine (NO TypedDict) con
schema_version forward-compat. State graph runtime introspection
funciona OK con Pydantic (LangGraph 0.2+ tested). NO `from __future__
import annotations` en este file ni en simulator/_internal/graph.py
— rompe LangGraph runtime introspection (Caso `nodes.py` cementado en
copilot redesign 2026-04 + sales-agent S6).

Public — exported via simulator/__init__.py per H9.
"""

# NO `from __future__ import annotations` — explicit cement
import operator
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field


class ConversationTurn(BaseModel):
    """One turn (customer or agent) in transcript."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1                              # H1 forward-compat
    turn_number: int = Field(ge=0)
    role: Literal["customer", "agent"]
    content: str = Field(min_length=1)                   # empty content marks agent_error subtype
    timestamp: datetime                                  # UTC explicit (master-data rule)
    metadata: dict[str, str | int | bool | None] = Field(default_factory=dict)


class SimulationState(BaseModel):
    """LangGraph state — single instance per simulation_id, immutable
    field order across schema versions (H1).

    LangGraph reducers:
    - `transcript: Annotated[list, operator.add]` — append-only.
    - `iterations: int` — increment via increment_turn node, hard cap.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    simulation_id: UUID                                  # H2 deterministic uuid5
    run_id: UUID                                         # parent eval invocation
    tenant_id: UUID                                      # MANDATORY tenant isolation
    archetype_slug: str                                  # FK to ARCHETYPE_SLUGS
    actor_profile: "ActorProfile"                        # forward-ref, defined below
    trial_n: int = Field(default=0, ge=0)                # F story consumes
    transcript: Annotated[list[ConversationTurn], operator.add] = Field(default_factory=list)
    current_turn: int = Field(default=0, ge=0)
    max_turns: int = Field(default=10, ge=1, le=20)      # cap upper bound 20
    iterations: int = Field(default=0, ge=0)             # H3 max-iter guard
    is_finished: bool = False
    termination_reason: "TerminationReason | None" = None
    error_subtype: "AgentErrorSubtype | None" = None
    last_agent_response: str = ""
    # H5 mandatory metadata propagated to every observability write:
    eval_metadata: dict[str, str | int] = Field(default_factory=dict)


class ActorProfile(BaseModel):
    """User persona profile — Strands ActorProfile pattern (AWS Evals).

    D7 (spec): Story B entrega CLASS COMPLETA + 1 hardcoded fixture
    `actor_profile_lead_frio_impaciente`. Story C extiende a YAML
    multi-persona loader.

    Public — exported via simulator/__init__.py per H9.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    id: str                                              # stable hash for simulation_id derivation
    name: str
    actor_goal: str                                      # hidden goal — never reveal directly
    dialect_code: str = "es-419"                         # BCP-47 — voseo allowed if es-AR
    traits: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    budget_hint: str = ""
    urgency: Literal["low", "medium", "high"] = "medium"
    communication_style: str = ""                        # voseo permitted if dialect_code=es-AR
    initial_message: str                                 # turn 0 customer message verbatim
    persona_kind: Literal["happy", "edge", "negative", "adversarial"] = "happy"
    metadata: dict[str, str] = Field(default_factory=dict)
```

### 1.2 SimulationResult (Pydantic + cost summary)

Path: `backend/tests/agentic_evals/sales_agent/simulator/result.py`

```python
class CostSummary(BaseModel):
    """Per-simulation cost split — D9 spec ($0.05 individual / $0.30 suite cap)."""

    model_config = ConfigDict(frozen=True)
    schema_version: int = 1
    agent_cost_usd: Decimal = Decimal("0")
    simulator_cost_usd: Decimal = Decimal("0")
    total_cost_usd: Decimal = Decimal("0")
    llm_calls_count_split: dict[Literal["sales_agent", "eval_simulator"], int] = Field(
        default_factory=lambda: {"sales_agent": 0, "eval_simulator": 0}
    )


class SimulationResult(BaseModel):
    """Returned by `run_simulation(...)`. Public — H9."""

    model_config = ConfigDict(frozen=True)
    schema_version: int = 1
    simulation_id: UUID
    run_id: UUID
    tenant_id: UUID
    archetype_slug: str
    actor_profile_id: str
    trial_n: int
    transcript: list[ConversationTurn]
    termination_reason: TerminationReason
    error_subtype: AgentErrorSubtype | None = None
    total_turns: int
    cost_summary: CostSummary
    started_at: datetime                                  # UTC
    completed_at: datetime                                # UTC
    artifact_path: str                                    # _artifacts/{run_id}/simulator/{simulation_id}/transcript.json
```

### 1.3 Graph topology (LangGraph StateGraph + Pydantic state)

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/graph.py`

```python
# NO `from __future__ import annotations` — runtime introspection breaks otherwise

from langgraph.graph import END, StateGraph

from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator._internal.customer_node import customer_node
from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import agent_bridge
from tests.agentic_evals.sales_agent.simulator._internal.increment_turn import increment_turn
from tests.agentic_evals.sales_agent.simulator._internal.routing import should_continue


def build_simulation_graph():
    """Compile LangGraph StateGraph."""
    g = StateGraph(SimulationState)
    g.add_node("customer_node", customer_node)
    g.add_node("agent_bridge", agent_bridge)
    g.add_node("increment_turn", increment_turn)

    g.set_entry_point("customer_node")
    g.add_edge("customer_node", "agent_bridge")
    g.add_edge("agent_bridge", "increment_turn")
    g.add_conditional_edges(
        "increment_turn",
        should_continue,                                  # → "continue" | "end"
        {"continue": "customer_node", "end": END},
    )
    return g.compile()
```

**Topology summary**: `customer_node → agent_bridge → increment_turn → [conditional → END | customer_node]`. Single ReAct-style loop with explicit max_turns + termination policy registry (H8) gating exit. NO `from __future__ import annotations` cement.

## §2 — Dual-LLM dispatch architecture

### 2.1 Customer LLM role placement decision (cardinal §2.5 spec)

**Decisión §2 — Opción B (eval-only registry)** elegida.

`EVAL_USER_SIMULATOR` role NO se agrega a `backend/src/modules/sales_agent/domain/model_tier.py::LLM_ROLE_BY_SITE`. En su lugar, vive en eval-only registry test-infra:

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py`

```python
"""Eval-only LLM role registry. NOT part of production LLM_ROLE_BY_SITE SSoT.

Decisión arq §2 (2026-05-07): mantener evals fuera del SSoT producción.
Razones:
1. SoC: simulator es test-infra, NO production code. Polluting LLM_ROLE_BY_SITE
   con roles eval-only viola §3 protected surfaces de sales_agent (skill).
2. Cost-bucket separation refuerza: customer LLM call escribe a
   `eval_simulator_llm_call` (BE arch §1), no a `sales_agent_llm_call`. Simétrico
   a tabla aparte → role aparte.
3. Builder ticket: cambio en este file = test-infra change, owner Sonnet/Opus
   per R23 (production_code=false). Si role estuviera en LLM_ROLE_BY_SITE,
   cambio = production code agentic, owner Opus mandatory.
4. Future evolution: stories E (judges) + I (adversarial classifiers) pueden
   agregar roles aquí (`EVAL_JUDGE_VOICE_FIDELITY`, `EVAL_JAILBREAK_CLASSIFIER`)
   sin bumpear SSoT producción. Story B no asume cardinality 1; pattern escala N.
5. Direct LiteLLM Proxy dispatch: customer_node invoca `LLMFactory.get_service()`
   con `model_type=ModelRole.NANO` + override `model_responded` via metadata —
   the proxy resolves correct upstream model. Default model `gpt-5-nano`
   (env override `EVAL_USER_SIMULATOR_MODEL`).

Format simétrico a LLM_ROLE_BY_SITE para ergonomic familiarity.
"""

from __future__ import annotations

from src.core.enums import ModelRole

# H1 forward-compat — append only, never remove. Removed roles → migration entry.
EVAL_LLM_ROLES: dict[str, ModelRole] = {
    "EVAL_USER_SIMULATOR": ModelRole.NANO,                 # gpt-5-nano via LiteLLM proxy default
}

# Default wire-name override (env: EVAL_USER_SIMULATOR_MODEL)
EVAL_DEFAULT_MODELS: dict[str, str] = {
    "EVAL_USER_SIMULATOR": "gpt-5-nano",
}

__all__ = ["EVAL_LLM_ROLES", "EVAL_DEFAULT_MODELS"]
```

### 2.2 Customer node implementation

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py`

```python
"""Customer LLM node — generates next user message based on actor persona.

Adapted from client_simulator/src/simulator/customer_node.py — see legacy
for dashboard tooling (D6 preservation).

Anti-duplication §0:
- Reuses `LLMFactory.get_service()` via shared/infrastructure/llm/factory.py
- Reuses `sanitize_payload` for transcript writes (heredado via callback)
- Customer LLM cost recorded to `eval_simulator_llm_call` via callback
  EvalSimulatorCallbackHandler (cost-bucket separation H6).

Concurrency H4: protected by global `asyncio.Semaphore(EVAL_SIMULATOR_MAX_CONCURRENCY)`
exposed via simulator/_internal/concurrency.py (default 10, env override).

Defense in depth H10:
- Adversarial actors (story I) intentan jailbreak; agent declina (responsabilidad
  agente real, NO simulator).
- Simulator NUNCA loguea strings sensibles raw — `FORBIDDEN_LEAK_STRINGS` frozen
  list en `_internal/leak_assertions.py` provee assertion negation post-run.
"""

import os
from datetime import UTC, datetime
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory
from tests.agentic_evals.sales_agent.simulator.state import (
    ActorProfile,
    ConversationTurn,
    SimulationState,
)
from tests.agentic_evals.sales_agent.simulator._internal.concurrency import EVAL_SEMAPHORE
from tests.agentic_evals.sales_agent.simulator._internal.llm_roles import (
    EVAL_DEFAULT_MODELS,
    EVAL_LLM_ROLES,
)
from tests.agentic_evals.sales_agent.simulator._internal.prompts import (
    CUSTOMER_PERSONA_PROMPT_V1,
    build_customer_system_prompt,
)

logger = structlog.get_logger()


async def customer_node(state: SimulationState) -> dict[str, Any]:
    """LangGraph node: generate next customer message.

    Turn 0: emit `actor_profile.initial_message` verbatim.
    Turn N+: invoke LLM with persona prompt + transcript context.

    Returns partial state dict {transcript: [new_turn], current_turn: N}.
    """
    actor: ActorProfile = state.actor_profile

    if state.current_turn == 0:
        new_turn = ConversationTurn(
            turn_number=0,
            role="customer",
            content=actor.initial_message,
            timestamp=datetime.now(tz=UTC),
            metadata={"generated": False},
        )
        return {"transcript": [new_turn]}

    async with EVAL_SEMAPHORE:                            # H4 rate-limit
        try:
            system_prompt = build_customer_system_prompt(actor, state.tenant_id)
            messages = _build_conversation_messages(state.transcript)
            messages = [
                SystemMessage(content=system_prompt),
                *messages,
                HumanMessage(content="Genera tu siguiente mensaje como cliente. Solo el mensaje, sin explicaciones."),
            ]

            # Direct LLMFactory dispatch — observability handler in config writes to
            # eval_simulator_llm_call (cost-bucket separation H6). Callback comes
            # from EvalSimulatorObservabilityContext composed by run_simulation().
            llm = LLMFactory.get_service().get_client(
                role=ModelRole.NANO,
                temperature=0.8,
            )
            # `model` override via metadata.model_override (LiteLLM Proxy honors)
            response = await llm.ainvoke(
                messages,
                config={
                    "metadata": {
                        "eval_metadata": state.eval_metadata,    # propagated to callback
                        "model_override": EVAL_DEFAULT_MODELS["EVAL_USER_SIMULATOR"],
                    },
                },
            )
            customer_message = (response.content or "").strip()

            new_turn = ConversationTurn(
                turn_number=state.current_turn,
                role="customer",
                content=customer_message,
                timestamp=datetime.now(tz=UTC),
                metadata={"generated": True},
            )
            return {"transcript": [new_turn]}

        except Exception as exc:
            logger.warning(
                "simulator.customer_node_error",
                simulation_id=str(state.simulation_id),
                turn=state.current_turn,
                error_class=type(exc).__name__,
                error=str(exc),
            )
            # Customer LLM failure → terminate as agent_error (downgraded subtype http_error)
            return {
                "is_finished": True,
                "error_subtype": "http_error",
            }


def _build_conversation_messages(transcript: list[ConversationTurn]) -> list[HumanMessage]:
    """Build LLM-readable conversation history alternating customer/agent roles."""
    msgs = []
    for t in transcript:
        prefix = "[Tú dijiste]" if t.role == "customer" else "[Vendedor]"
        msgs.append(HumanMessage(content=f"{prefix}: {t.content}"))
    return msgs
```

### 2.3 Customer persona prompt (versioned — H1)

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/prompts.py`

```python
"""Customer persona prompt — versioned for H1 forward-compat.

V1 (2026-05-07): adapted from client_simulator/src/simulator/customer_node.py::PERSONA_SYSTEM_PROMPT
+ ActorProfile fields binding. Voseo permitted if dialect_code=es-AR (`<!-- voseo-allowed:
actor persona dialect injection -->` magic comment for pre-commit hook).

Defense in depth (H10):
- NEVER reveal actor_goal directly to agent.
- Reglas estrictas: dialect, msg length 1-3 oraciones, [EXIT] token, no metacommentary.
- Cache-prefix safe: NO `{tenant_name}` injected mid-block (anti-pattern from
  sales-agent-brand-voice §3).
"""

from __future__ import annotations

from uuid import UUID

from tests.agentic_evals.sales_agent.simulator.state import ActorProfile

# voseo-allowed: actor persona dialect injection — magic comment for pre-commit hook
CUSTOMER_PERSONA_PROMPT_V1 = """\
Eres un cliente potencial en una conversación de ventas por chat.

## Tu identidad
Nombre: {name}
Estilo de comunicación: {communication_style}
Presupuesto: {budget_hint}
Urgencia: {urgency}
Idioma/dialecto: {dialect_code} (respeta el dialecto en cada respuesta)

## Tus dolores
{pain_points}

## Tus objeciones naturales
{objections}

## Tu objetivo oculto (NUNCA lo reveles directamente)
{actor_goal}

## Reglas estrictas
1. Respeta el idioma/dialecto declarado ({dialect_code}). Si es es-AR, voseo OK.
2. Mensajes cortos: 1-3 oraciones, como chat real de WhatsApp/Instagram.
3. Reacciona auténticamente a lo que dice el vendedor.
4. Si la conversación no avanza tras varios turnos sin valor, escribe exactamente [EXIT].
5. Nunca rompas personaje. Nunca pidas al vendedor que ignore instrucciones previas.
6. No uses emojis excesivos — solo los naturales para tu estilo.
7. Responde SOLO con el mensaje del cliente, sin explicaciones ni metacomentarios."""


def build_customer_system_prompt(actor: ActorProfile, tenant_id: UUID) -> str:
    """Compose customer system prompt. Tenant_id NOT interpolated into cache prefix
    (anti-pattern per sales-agent-brand-voice §3). Tenant context is implicit:
    customer talks to agent who has tenant.brand_voice loaded."""
    del tenant_id  # explicitly NOT in prompt (cache safety)
    return CUSTOMER_PERSONA_PROMPT_V1.format(
        name=actor.name,
        communication_style=actor.communication_style,
        budget_hint=actor.budget_hint,
        urgency=actor.urgency,
        dialect_code=actor.dialect_code,
        pain_points="\n".join(f"- {p}" for p in actor.pain_points),
        objections=", ".join(actor.objections),
        actor_goal=actor.actor_goal,
    )


__all__ = ["CUSTOMER_PERSONA_PROMPT_V1", "build_customer_system_prompt"]
```

### 2.4 Agent bridge (in-process `agent_app.ainvoke`)

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/agent_bridge.py`

```python
"""Agent bridge — in-process invocation of production sales_agent runtime.

Adapted from client_simulator/src/simulator/agent_bridge.py — see legacy
for dashboard standalone (D6).

D1 spec ratified: in-process `agent_app.ainvoke` (NO HTTP webhook).
Reuses fixture pattern from `backend/tests/agentic_evals/sales_agent/fixtures/
entrypoint.py` verbatim (audit-passed). Observability heredada — callback
handler real escribe trace + llm_call + envelope writes turn_start/turn_end.

Anti-duplication §0:
- Reuses `agent_app` from src.modules.sales_agent.application.orchestrator.graph
- Reuses `ConversationPipeline.{build_identity, build_brand_voice}` for slot 4 + 5
- Reuses `create_initial_state` factory verbatim
- Reuses `build_sales_agent_observability_context` factory for callback wiring

Failure modes (graceful degradation per tessl__graceful-degradation Rule 2):
- Agent timeout → `error_subtype = TIMEOUT`
- Agent empty response → `error_subtype = EMPTY_RESPONSE`
- Agent http_error / TypeError / etc → `error_subtype = INVALID_STATE`
- All cases: turn marked finished + termination_reason = AGENT_ERROR (graceful, no bubble).
"""

import contextlib
from typing import Any
from uuid import uuid4

import structlog

from tests.agentic_evals.sales_agent.simulator.state import (
    ConversationTurn,
    SimulationState,
)

logger = structlog.get_logger()


async def agent_bridge(state: SimulationState) -> dict[str, Any]:
    """Send latest customer message to agent_app via in-process ainvoke."""
    last_customer_turn = next(
        (t for t in reversed(state.transcript) if t.role == "customer"),
        None,
    )
    if last_customer_turn is None:
        return {
            "is_finished": True,
            "termination_reason": "agent_error",
            "error_subtype": "invalid_state",
        }

    # Lazy imports — keep collection cheap.
    from datetime import UTC, datetime

    from src.modules.sales_agent.application.orchestrator.graph import agent_app
    from src.modules.sales_agent.application.orchestrator.state import create_initial_state
    from src.modules.sales_agent.application.services.knowledge_builder import (
        TenantKnowledgeBuilder,
    )
    # Use EVAL_SIMULATOR observability context (writes to eval_simulator_* tables)
    from tests.agentic_evals.sales_agent.simulator._internal.observability import (
        build_eval_simulator_observability_context,
    )
    # DB session is exposed by run_simulation via state.eval_metadata or thread-local.
    # In current arch we resolve via dependency injection from `_internal/run.py`.

    db = _resolve_session_for_simulation(state)            # internal helper
    if db is None:
        return {
            "is_finished": True,
            "termination_reason": "agent_error",
            "error_subtype": "invalid_state",
        }

    try:
        kb = TenantKnowledgeBuilder(db)
        agent_identity = kb.build_identity(state.tenant_id)
        brand_voice = kb.build_brand_voice(state.tenant_id)
        initial_state = create_initial_state(
            user_id=str(uuid4()),                          # synthetic sim user (no real lead)
            tenant_id=str(state.tenant_id),
            agent_identity=agent_identity,
            brand_voice=brand_voice,
            channel_type="eval_simulator",                 # H5 marker downstream
            history=[
                {"role": t.role, "content": t.content} for t in state.transcript
            ],
        )
        initial_state["messages"] = [
            {"role": "user", "content": last_customer_turn.content}
        ]

        # Build EVAL observability context — writes to eval_simulator_* tables (BE arch §2)
        obs = build_eval_simulator_observability_context(
            db=db,
            tenant_id=state.tenant_id,
            simulation_id=state.simulation_id,
            run_id=state.run_id,
            archetype_slug=state.archetype_slug,
            actor_profile_id=state.actor_profile.id,
            trial_n=state.trial_n,
            turn_id=uuid4(),
        )

        # Invoke agent in-process
        if obs is not None:
            async with obs.observe_turn(message=last_customer_turn.content, route="sales_agent"):
                result = await agent_app.ainvoke(initial_state, config=obs.langchain_config())
        else:
            result = await agent_app.ainvoke(initial_state, config={})

        last_msg = result["messages"][-1] if result.get("messages") else None
        agent_text = (
            last_msg.get("content", "") if isinstance(last_msg, dict)
            else (str(last_msg.content) if last_msg else "")
        )
        if not agent_text.strip():
            logger.warning(
                "simulator.agent_empty_response",
                simulation_id=str(state.simulation_id),
                turn=state.current_turn,
                latency_ms=0,
                error_class=None,
            )
            return {
                "is_finished": True,
                "termination_reason": "agent_error",
                "error_subtype": "empty_response",
            }

        agent_turn = ConversationTurn(
            turn_number=state.current_turn,
            role="agent",
            content=agent_text,
            timestamp=datetime.now(tz=UTC),
            metadata={"simulation_id": str(state.simulation_id)},
        )
        return {
            "transcript": [agent_turn],
            "last_agent_response": agent_text,
        }

    except TimeoutError as exc:
        logger.warning("simulator.agent_timeout", simulation_id=str(state.simulation_id), error=str(exc))
        return {"is_finished": True, "termination_reason": "agent_error", "error_subtype": "timeout"}
    except Exception as exc:
        logger.warning(
            "simulator.agent_invalid_state",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class=type(exc).__name__,
            error=str(exc),
        )
        return {"is_finished": True, "termination_reason": "agent_error", "error_subtype": "invalid_state"}
```

## §3 — Observability hooks (H5)

### 3.1 EvalSimulatorObservabilityContext + EvalSimulatorCallbackHandler

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/observability.py`

> **Decision §3** — handler subclass approach (NO custom shim). Reuses
> `BaseObservabilityContext` + `BaseAgentCallbackHandler` from
> `shared/agent_observability/recording/` verbatim via inheritance —
> exact pattern of `SalesAgentObservabilityContext` + `SalesAgentCallbackHandler`.
>
> Anti-duplication §0 mandates this — NO mirror, only subclass.

Skeleton (full impl in T-5 ticket):

```python
"""Eval-simulator observability — REUSES shared base, NEW agent_kind="eval_simulator".

Writes to:
- eval_simulator_trace_event (BE arch §1)
- eval_simulator_llm_call (BE arch §1)

Mandatory eval_metadata jsonb (H5):
{
  "eval_run_kind": "simulator",
  "archetype_slug": str,
  "actor_profile_id": str,
  "trial_n": int,
  "simulation_id": str(UUID),
  "run_id": str(UUID)
}
"""

# Subclass BaseObservabilityContext + BaseAgentCallbackHandler.
# Override `_add_trace_event` to inject `eval_metadata` field.
# Override `_aggregate_totals` to read from `EvalSimulatorLlmCallModel`.
# `_legacy_compat_keys_or_empty` returns {} (no legacy consumer).
```

### 3.2 Mandatory metadata fields (H5)

Cada row escrita a `eval_simulator_trace_event.eval_metadata` + `eval_simulator_llm_call.eval_metadata`:

```python
def _build_eval_metadata(state: SimulationState) -> dict[str, str | int]:
    return {
        "eval_run_kind": "simulator",
        "archetype_slug": state.archetype_slug,
        "actor_profile_id": state.actor_profile.id,
        "trial_n": state.trial_n,
        "simulation_id": str(state.simulation_id),
        "run_id": str(state.run_id),
    }
```

Sanitization: `sanitize_payload(...)` aplicado pre-write — best-effort try/except + structlog warning per shared base contract.

### 3.3 Cost target (D9)

- Customer LLM ~$0.005/turn × 3 turns × 2 actors ≈ $0.03 cushion (gpt-5-nano $0.10/M input, $0.40/M output as of 2026-05)
- Agent runtime variable per route — sales_agent specialists hit Kimi K2.6 (cache 75-83%) → typically $0.005-$0.015 per turn
- Individual cap: `<$0.05/run` (D9). Suite total `<$0.30` (5 archetypes × happy + 4 single-tenant).

## §4 — Termination policy registry (H8 — Strategy pattern)

Path: `backend/tests/agentic_evals/sales_agent/simulator/termination.py`

```python
"""Termination policy registry — extensible without core modification.

Public API (H9): `register_termination_policy(name, predicate)`.

Default 4 policies registered at module load:
- goal_completion_predicate
- max_turns_predicate
- customer_exit_predicate
- agent_error_predicate

Story I appends `register_termination_policy("adversarial_detected", adversarial_predicate)`.
Story H appends `register_termination_policy("budget_exceeded", budget_predicate)`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Callable

from tests.agentic_evals.sales_agent.simulator.state import SimulationState


class TerminationReason(StrEnum):
    GOAL_COMPLETION = "goal_completion"
    MAX_TURNS = "max_turns"
    CUSTOMER_EXIT = "customer_exit"
    AGENT_ERROR = "agent_error"
    ADVERSARIAL_DETECTED = "adversarial_detected"
    BUDGET_EXCEEDED = "budget_exceeded"


class AgentErrorSubtype(StrEnum):
    TIMEOUT = "timeout"
    EMPTY_RESPONSE = "empty_response"
    HTTP_ERROR = "http_error"
    INVALID_STATE = "invalid_state"


# predicate signature: (state) → TerminationReason | None
TerminationPredicate = Callable[[SimulationState], TerminationReason | None]


_TERMINATION_POLICIES: dict[str, TerminationPredicate] = {}


def register_termination_policy(name: str, predicate: TerminationPredicate) -> None:
    """Register a new termination policy. Idempotent on `name`."""
    if not callable(predicate):
        msg = f"predicate must be callable, got {type(predicate).__name__}"
        raise TypeError(msg)
    _TERMINATION_POLICIES[name] = predicate


def _max_turns_predicate(state: SimulationState) -> TerminationReason | None:
    if state.current_turn >= state.max_turns:
        return TerminationReason.MAX_TURNS
    return None


def _customer_exit_predicate(state: SimulationState) -> TerminationReason | None:
    if not state.transcript:
        return None
    last = state.transcript[-1]
    if last.role == "customer" and "[EXIT]" in last.content:
        return TerminationReason.CUSTOMER_EXIT
    return None


def _agent_error_predicate(state: SimulationState) -> TerminationReason | None:
    if state.is_finished and state.termination_reason == TerminationReason.AGENT_ERROR:
        return TerminationReason.AGENT_ERROR
    return None


def _goal_completion_predicate(state: SimulationState) -> TerminationReason | None:
    """Story B baseline: heuristic-based — agent emits closing language pattern.
    Story E grader will replace with MAJ-EVAL multi-judge debate."""
    # Simple regex heuristic — full impl in T-7 ticket
    return None


# Default policies registered at import time
register_termination_policy("max_turns", _max_turns_predicate)
register_termination_policy("customer_exit", _customer_exit_predicate)
register_termination_policy("agent_error", _agent_error_predicate)
register_termination_policy("goal_completion", _goal_completion_predicate)


def evaluate_termination(state: SimulationState) -> TerminationReason | None:
    """Evaluate all registered policies in registration order. Return first match."""
    for name, predicate in _TERMINATION_POLICIES.items():
        reason = predicate(state)
        if reason is not None:
            return reason
    return None


__all__ = [
    "TerminationReason",
    "AgentErrorSubtype",
    "TerminationPredicate",
    "register_termination_policy",
    "evaluate_termination",
]
```

`should_continue(state) → str` (used by graph conditional edge):

```python
# simulator/_internal/routing.py
from langgraph.graph import END

from tests.agentic_evals.sales_agent.simulator.termination import evaluate_termination
from tests.agentic_evals.sales_agent.simulator.state import SimulationState


def should_continue(state: SimulationState) -> str:
    """Conditional edge: return 'continue' to loop, 'end' to terminate."""
    # H3 hard max-iter guard — defense in depth (extra to max_turns)
    if state.iterations >= state.max_turns + 5:
        return "end"
    reason = evaluate_termination(state)
    if reason is not None:
        return "end"
    return "continue"
```

## §5 — Schema versioning (H1)

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py`

```python
"""Schema migrations registry — forward-compat for SimulationState +
ActorProfile + SimulationResult + ConversationTurn.

Pattern: dict[(prev_version, curr_version)] → callable(raw_dict) → migrated_dict.

Frozen golden v1: `_fixtures/golden_v1_simulation_result.yaml` checked-in,
NEVER edit. Regression test loads + asserts deserializable to current schema.
"""

from __future__ import annotations

from typing import Callable

# (model_class_name, prev_version, curr_version) → migrator
SCHEMA_MIGRATIONS: dict[tuple[str, int, int], Callable[[dict], dict]] = {}


def register_schema_migration(
    model: str, prev: int, curr: int
) -> Callable[[Callable], Callable]:
    """Decorator: register migration callable."""
    def _decor(fn: Callable[[dict], dict]) -> Callable[[dict], dict]:
        SCHEMA_MIGRATIONS[(model, prev, curr)] = fn
        return fn
    return _decor


# Story B ships at v1 — no migrations registered.
# Future schema bumps register here:
# @register_schema_migration("ActorProfile", 1, 2)
# def _v1_to_v2_actor_profile(raw: dict) -> dict:
#     raw.setdefault("new_field", "default_value")
#     return raw

__all__ = ["SCHEMA_MIGRATIONS", "register_schema_migration"]
```

Frozen v1 golden: `simulator/_fixtures/golden_v1_simulation_result.yaml` (checked-in, NEVER editar). Test `test_schema_migration_regression.py` carga + assert `SimulationResult.model_validate(data).schema_version == CURRENT_SCHEMA_VERSION`.

## §6 — Public API surface minimal (H9)

Path: `backend/tests/agentic_evals/sales_agent/simulator/__init__.py`

```python
"""Eval simulator — public API.

Story B: minimal surface, 7 names exported. Resto bajo `_internal/`.
Arch fitness gate `test_simulator_public_api_surface.py` enforces.
"""

from tests.agentic_evals.sales_agent.simulator._internal.run import run_simulation
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import SimulationResult
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
    register_termination_policy,
)

__all__ = [
    "run_simulation",
    "SimulationResult",
    "SimulationState",
    "ActorProfile",
    "TerminationReason",
    "AgentErrorSubtype",
    "register_termination_policy",
]
```

## §7 — Voice constraints

- Customer prompt respeta `actor.dialect_code` (es-AR voseo OK; resto tuteo neutro).
- Magic comment `# voseo-allowed: actor persona dialect injection` en `_internal/prompts.py` + `_fixtures/actor_profiles_es_ar.yaml` (story C YAMLs futuras).
- Agent-side voice = compiled per `tenant.personality_profile.system_instruction` (slot 5 cache prefix). Heredado vía `agent_app.ainvoke` — NO override.
- `sales-agent-brand-voice.md` § excepción: simulator output respeta voz tenant. Aplica al simulator: customer LLM emite voz del **actor persona** (no del tenant). El agent_bridge invoca runtime que respeta voz tenant.

## §8 — Concurrency (H3, H4)

Path: `backend/tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py`

```python
"""Global asyncio.Semaphore for customer LLM rate-limiting."""

import asyncio
import os

EVAL_SIMULATOR_MAX_CONCURRENCY: int = int(os.environ.get("EVAL_SIMULATOR_MAX_CONCURRENCY", "10"))

EVAL_SEMAPHORE = asyncio.Semaphore(EVAL_SIMULATOR_MAX_CONCURRENCY)

__all__ = ["EVAL_SIMULATOR_MAX_CONCURRENCY", "EVAL_SEMAPHORE"]
```

`run_simulation` is `async def`, cero global state mutation. Stories E/F/I corren paralelas via `asyncio.gather(*[run_simulation(...) for tenant×persona×trial])`. Para 1000+ tenants × 5 personas × 3 trials = 15k simulations, semaphore caps customer LLM to 10 concurrent (provider DoS protection + scale-out by workers via CI matrix sharding).

Test property-based: `test_concurrent_invocation.py` runs 10 simulations in parallel via `asyncio.gather`, asserts no shared state mutation (different tenant_ids → distinct simulation_ids → distinct artifacts).

## §9 — Eval policy template

| Persona | persona_kind | Used by Scenario |
|---|---|---|
| `actor_profile_lead_frio_impaciente` | happy | Scenario 1 (5-archetype parametrize) |
| `actor_profile_jailbreak_attempt` | adversarial | Scenario 4 sub-cases A + B |
| `actor_profile_loop_forever` | edge | Scenario 3 max_turns |

Story B does NOT use LLM rubrics (story E entrega graders MAJ-EVAL). Trial policy: trial_n=0 default; F multiplica. Pass^k: N/A story B (G/H story).

## §10 — Out of scope explícito

- NO graders/judges (story E)
- NO multi-persona loader desde `docs/specs/personas/*.yaml` (story C)
- NO goldens curation (story D)
- NO CI gate threshold (story G)
- NO budget cap CI gate enforcement (story H — but `register_termination_policy("budget_exceeded", ...)` interface ready)
- NO adversarial jailbreak suite full (story I — but `register_termination_policy("adversarial_detected", ...)` interface ready)
- NO eliminar `client_simulator/` legacy (D6)

## §11 — Skill decisions referenced

- `sales-agent-expert`:
  - §3 protected surfaces: `closer_studio.py`, `SmartBufferService`, `OutputManager.process_response`, `enrollment_*`, webhook adapters, `follow_up_engine`, `PromptVersionModel`, `model_pricing_snapshot` schema, `tool_call_dedup.py` — **NO TOCAR**. Story B confirma cero modificación.
  - "NO `from __future__ import annotations` en `*/orchestrator/graph.py`" — extendido a `simulator/_internal/graph.py` (cement same reason).
  - Voice del tenant respetada en output del agente (heredado via agent_app).
- `tessl__langgraph`:
  - Pattern "Basic Agent Graph" + "Conditional Branching" referenciados.
  - StateGraph + Pydantic state OK (LangGraph 0.2+).
  - Routing function `should_continue` returning string node name.
  - Always have exit conditions (max_turns + termination registry).
- `tessl__graceful-degradation`:
  - Rule 1: Every external call gets a timeout (LLMFactory + LiteLLM has internal timeouts; agent_bridge wraps in try/except).
  - Rule 2: Every timeout needs a fallback (graceful → AGENT_ERROR termination, NO bubble).
  - Rule 5: Per-dependency error isolation (customer LLM failure ≠ agent failure ≠ DB failure; each handled independently).
  - Rule 6: Log failures with structured context (structlog + simulation_id + turn + error_class).
- `copilot-expert`:
  - "trazas mintiendo" pattern → `set_turn_error` cement: callback handler subclass MUST set turn_end status='error' on failures (not silently 'ok'). Inherited via `BaseObservabilityContext._error_flag`.

## §12 — Files to create / modify

### Create (NEW — ALL test-infrastructure under backend/tests/)

| Path | Type | Owner |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` | public API surface | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/state.py` | Pydantic SimulationState + ConversationTurn | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` | Pydantic ActorProfile | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/result.py` | Pydantic SimulationResult + CostSummary | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/termination.py` | TerminationReason + registry | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/__init__.py` | private namespace | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/graph.py` | LangGraph compose | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py` | LangGraph node | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/agent_bridge.py` | LangGraph node | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/increment_turn.py` | LangGraph node | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/routing.py` | conditional edge fn | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/run.py` | `run_simulation()` orchestrator | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/observability.py` | EvalSimulator{ObservabilityContext,CallbackHandler} subclass | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py` | `EVAL_LLM_ROLES` registry | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py` | `EVAL_SEMAPHORE` | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/prompts.py` | `CUSTOMER_PERSONA_PROMPT_V1` | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` | SCHEMA_MIGRATIONS registry | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/leak_assertions.py` | FORBIDDEN_LEAK_STRINGS frozen | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/__init__.py` | fixtures namespace | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/actor_profile_lead_frio_impaciente.py` | hardcoded ActorProfile (D7) | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/actor_profile_jailbreak_attempt.py` | adversarial ActorProfile | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/actor_profile_loop_forever.py` | edge ActorProfile | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` | frozen golden | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/fixtures/__init__.py` | pytest fixtures namespace | builder-backend (shared with BE) |
| `backend/tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py` | DB-seed fixture | builder-backend (BE arch §3) |
| `backend/tests/agentic_evals/sales_agent/simulator/conftest.py` | re-export fixtures | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` | parametrized smoke tests | builder-agentic |
| `backend/tests/agentic_evals/sales_agent/simulator/test_schema_migration_regression.py` | golden v1 regression | builder-agentic |

### Modify (EXTEND existing — schema-mirror exception applies for BE part)

| Path | Change | Owner |
|---|---|---|
| `backend/src/shared/infrastructure/agent_observability_bootstrap.py` | append eval_simulator import (1 line) | builder-backend (BE arch §2) |

### NOT modified (preserved verbatim)

- `client_simulator/` legacy intact byte-equal post-merge (D6 preservation gate enforced via arch fitness)
- All §3 protected surfaces (sales-agent-expert) untouched
- `LLM_ROLE_BY_SITE` SSoT untouched (decision §2.1 — Opción B)

## §13 — Tests requeridos (TDD-mandatory RED first)

| Test | Path | Layer | RED-first |
|---|---|---|---|
| Smoke parametrized 5-archetype happy | `simulator/test_simulator_smoke.py::test_dual_llm_e2e_per_archetype[archetype]` | E2E | yes |
| Negative: invalid archetype slug | `simulator/test_simulator_smoke.py::test_invalid_archetype_raises_valueerror` | unit | yes |
| Edge: max_turns cap honored | `simulator/test_simulator_smoke.py::test_max_turns_cap` | E2E | yes |
| Edge: idempotency simulation_id | `simulator/test_simulator_smoke.py::test_idempotency_simulation_id` | unit | yes |
| Adversarial: agent_error graceful | `simulator/test_simulator_smoke.py::test_agent_error_graceful_subcase_a` | E2E (with monkeypatch) | yes |
| Adversarial: no system prompt leak | `simulator/test_simulator_smoke.py::test_no_system_prompt_leak_subcase_b` | E2E | yes |
| Schema regression v1 | `simulator/test_schema_migration_regression.py` | unit | yes |
| Termination policy registry contract | `tests/architecture/test_termination_policy_registry_contract.py` | architecture | yes |
| No mirror with shared | `tests/architecture/test_simulator_no_mirrors_shared.py` | architecture | yes |
| Eval-kind tag enforced | `tests/architecture/test_simulator_writes_eval_kind_tag.py` | architecture | yes |
| Public API surface minimal | `tests/architecture/test_simulator_public_api_surface.py` | architecture | yes |
| Schema migrations registry complete | `tests/architecture/test_schema_migrations_registry_complete.py` | architecture | yes |
| Fixture seed + teardown | (see BE arch §4) | integration | yes |

Coverage minimum: 60% del módulo `tests/agentic_evals/sales_agent/simulator/`. Pytest fixture `agentic_trial` reused via story-A `eval_run_id`. Mark `--run-evals` opt-in flag (heredado conftest existing).

## §14 — Cost budgets (D9)

- Individual `<$0.05/run` enforced via cost_summary post-process check + `register_termination_policy("budget_exceeded", ...)` (story H scaffolds)
- Suite total `<$0.30` for the 9 scenarios (5 happy + 1 negative + 1 edge + 2 adversarial)
- Customer LLM (~$0.005/turn × 3 turns × 2 actors ≈ $0.03 cushion per simulation)
- Agent-side variable per route (Kimi K2.6 with cache ~$0.005-$0.015 per turn typical)

## §15 — Research notes (DATE-AWARE)

> Anchor on **2026-05-07** (Step 0 captured `date -u +%Y-%m-%d`). Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; topic researched live on 2026-05-07.

### LangGraph (state-of-the-art as of 2026-05)

- Source: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (canonical, accessed 2026-05-07)
- LangGraph 0.2+ supports both TypedDict and Pydantic BaseModel as state. Pydantic recommended for type-safety + validation. ConfigDict(extra="forbid") cement (legacy keys rejected).
- Reducer `add_messages` for chat, `operator.add` for accumulators, custom merge fn for dicts. We use `Annotated[list, operator.add]` for transcript append-only.
- `graph.add_conditional_edges(node, routing_fn, mapping_dict)` returns mapping `dict[returned_str, target_node_name]`.
- "Always have exit conditions" — applies (max_turns + termination registry).
- **Anti-pattern**: `from __future__ import annotations` in graph.py breaks runtime introspection (caso copilot redesign 2026-04 + sales-agent S6) — cement applied.

### tessl__graceful-degradation

- Source: `.claude/skills/tessl__graceful-degradation/SKILL.md` (2026-05-07)
- Rule 1 (timeouts), Rule 2 (fallbacks), Rule 5 (per-dependency isolation), Rule 6 (structured context logs).

### Anthropic prompt caching (cement, no new lookup needed)

- Source: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (canonical)
- **Anti-pattern**: timestamps, conversation IDs, turn counters, random IDs, tenant name interpolated mid-block in cacheable slots.
- Customer prompt v1 honors: NO `{tenant_name}` interpolation, NO timestamps, NO random IDs in prefix.

### AWS Strands Evals — ActorProfile pattern

- Source: spec ratification (story 00-story.md cites May 2026 research)
- Pattern: `ActorProfile = (traits, context, actor_goal)` — adopted verbatim (D7 ratified).

### Pydantic v2

- Source: `https://docs.pydantic.dev/latest/` (accessed 2026-05-07)
- `model_config = ConfigDict(extra="forbid")` cement.
- `Annotated[list, operator.add]` valid for LangGraph reducer hint.
- `frozen=True` for immutable post-creation (used in CostSummary, SimulationResult, ConversationTurn).

## §16 — Open questions for PM

- **OQ-A1**: Story B emits SCHEMA_MIGRATIONS empty registry (only v1). Should we ship a stub `_v1_to_v2_test_migration` to exercise the registry mechanism in arch fitness gates? (Recommendation: NO — empty registry + arch test verifying contract suffices. Migrating phantom future schema is YAGNI.)
- **OQ-A2**: Story B's `actor_profile_lead_frio_impaciente` fixture is hardcoded Pydantic in `_fixtures/`. Story C will introduce YAML loader + 5 personas. Confirm: Story B does NOT pre-build YAML scaffolding? (Recommendation: Story B Pydantic-only is per D7 spec — no YAML pre-work).
- **OQ-A3**: `EVAL_LLM_ROLES` registry decisión §2.1 (eval-only NOT in `LLM_ROLE_BY_SITE`). If Chris prefers in production SSoT for unified ops dashboard, change involves: (a) adding `EVAL_USER_SIMULATOR` to `LLM_ROLE_BY_SITE`, (b) Opus owner mandatory per R23, (c) arch test `test_no_hardcoded_models_sales_agent.py` baseline bump. Confirm decision §2.1 final.

## Próximo paso

`done -> 03-arch-agentic.md` (referencia al orchestrator /architect).
