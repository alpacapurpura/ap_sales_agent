---
name: agentic-system-architect
description: Expert guide for backend on LangGraph agents and agentic systems (2026 standards). Covers state design, cognitive patterns (Reflexion, LATS, Plan-and-Execute), and SOTA research strategies.
---

# Agentic System Architect

## Description

This skill acts as a Senior Architect for designing, implementing, and refactoring AI agents using LangGraph. It enforces "System 2" thinking, strict state management, and mandates a "Research First" approach to adopt State-of-the-Art (SOTA) patterns suitable for the task.

## When to Use

*   **Designing a new Agent**: When starting a new agent module in `backend/src/core/agents/`.
*   **Refactoring Logic**: When upgrading simple chains (DAGs) to cyclic graphs (Agents) or implementing self-correction.
*   **Optimization**: When the current agent is slow, hallucinating, or failing complex tasks.
*   **Architecture Review**: When deciding between a single agent, a swarm, or a hierarchical flow.

## Instructions

### 1. The SOTA Check (Pattern Discovery)
**CRITICAL**: Before applying a standard pattern, verify if a better approach exists for the specific domain.
*   **Research**: Use the `search` tool to find "LangGraph Design Patterns [Current Year]" or "Agentic Patterns for [Task]".
*   **Deep Dive**: Look for validation in recent papers (arXiv), tech reports, and engineering blogs from top labs (e.g., Anthropic, OpenAI).
*   **Trend Analysis**: Use this data to understand "where the industry is going" and use it as an input for technical decisions, not necessarily as the single source of truth.
*   **Contrast**: Explicitly compare "What we have" (e.g., Orchestrator-Workers) vs. "What is new" (e.g., Dynamic Planning with Re-planning).

### 2. Thinking in LangGraph (The Design Process)
Apply this 5-step process to map requirements to graph primitives:

1.  **Map the Workflow**:
    *   **DAG vs. Cycle**: Is it a pipeline (Onboarding) or a loop (Negotiation)?
    *   **Control Flow**: Who drives the loop? The User? The LLM? A Rule?
2.  **Design the State (`AgentState`)**:
    *   **Single Source of Truth**: All context, history, and internal variables must be in `AgentState`.
    *   **Schema**: Use `TypedDict` or `Pydantic`. Differentiate **Shared State** (Messages) from **Private State** (Thought process).
3.  **Define Nodes (Pure Functions)**:
    *   `Node: (State) -> Partial<State>`. No side effects outside DB/API.
4.  **Define Edges (Routing Logic)**:
    *   **Deterministic**: Rules based on state (e.g., `if count > 5`).
    *   **Probabilistic**: LLM-based routing (e.g., `Router` node).
5.  **Persistence**:
    *   Always use a Postgres checkpointer for production agents to enable "Time Travel" and Human-in-the-Loop.

### 3. LangGraph Implementation Patterns (The "How")
*Best practices for implementing flows using LangGraph primitives.*

| Pattern | Description | LangGraph Implementation |
| :--- | :--- | :--- |
| **Prompt Chaining** | Linear sequence of LLM calls. | Simple DAG: `Node A -> Node B -> Node C`. |
| **Parallelization** | Running multiple tasks at once. | Fan-out branches that write to a shared reducer key (e.g., `messages`). |
| **Routing** | Conditional execution based on input. | `add_conditional_edges` with a classifier function. |
| **Orchestrator-Worker** | Central node delegates sub-tasks dynamically. | Use `Send` API to map inputs to worker nodes in parallel. |
| **Supervisor** | Router that maintains state and delegates to specialized agents. | A stateful node loop: `Supervisor -> (Agent A | Agent B) -> Supervisor`. |

> **Deep Dive**: These patterns are standard. For advanced implementation details, research "LangGraph Best Practices" or check [LangChain Workflows vs Agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents).

### 4. Enterprise Agentic Architectures (The "What")
*High-level conceptual designs for solving complex business problems.*

| Architecture | Complexity | Use Case | Google Cloud / Research Equivalent |
| :--- | :--- | :--- | :--- |
| **ReAct** | Medium | General purpose tasks requiring tool use. | Standard "Agent" pattern. Loop: Reason → Act → Observe. |
| **Evaluator-Optimizer** | High | Quality-critical generation (e.g., Copywriting). | **Reflexion**. A "Critic" node provides feedback to a "Generator" node to refine output. |
| **Hierarchical Teams** | High | Complex domains with distinct sub-specialties. | **Orchestrator-Workers**. A "Manager" agent breaks down goals for "Worker" agents. |
| **Dynamic Planning** | Very High | Ambiguous goals requiring research. | **Plan-and-Execute**. Planner creates a manifest; Executor runs it; Replanner updates it. |

> **Strategic Selection**: We currently use **Reflexion** (Orchestrator) and **Hierarchical Teams** (Sales). For a broader view of when to choose what, research "Google Cloud Agentic Design Patterns" or "Agentic design patterns".

### 5. Implementation Standards

#### Directory Structure
```text
backend/src/core/agents/{agent_name}/
├── graph.py       # Workflow definition (StateGraph, Edges)
├── nodes.py       # Logic units (Pure Functions)
├── state.py       # Schema definition (TypedDict)
├── prompts.py     # System prompts and templates
└── tests/         # Agent-specific tests
```

#### Code Rules
*   **Strict Typing**: All nodes must be typed.
*   **Async Native**: All I/O bound nodes must be `async def`.
*   **No "Vibes"**: Use structured outputs (tools/function calling) for routing/decisions.

### 6. Testing & Observability

*   **Node Isolation**: Test nodes as pure functions with `MockState`.
*   **Graph Integration**: Test the full flow with mocked LLM responses to verify routing logic.
*   **State Reconstruction**: Debug by hydrating the state from a production checkpoint and replaying the failed node.

## Examples

### SOTA Check Prompt
"Search for 'Agentic Design Patterns for Customer Onboarding 2025'. Compare 'Plan-and-Execute' vs 'Finite State Machine' for this use case."

### Reflexion Edge Logic
```python
def should_continue(state: AgentState) -> Literal["generate", "end"]:
    if state["critique_count"] > 3:
        return "end" # Force exit
    if state["quality_score"] < 8:
        return "generate" # Retry with feedback
    return "end"
```
