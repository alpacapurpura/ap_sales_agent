# Agentic Patterns & LangGraph Best Practices

## LangGraph Architecture
### State Management
- **Schema Definition**: Use `TypedDict` or `Pydantic` models for state. Ensure strict typing.
- **Immutability**: Treat state as immutable where possible; reducers should return new state instances.
- **Granularity**: Keep state minimal. Don't store massive ephemeral data unless necessary for context.
- **Persistence**: Use `MemorySaver` or `PostgresSaver` for long-running threads. Ensure state is serializable.

### Graph Topology
- **Cyclic vs Acyclic**: Use cycles for retries, feedback loops (Reflexion), and iterative refinement. Use DAGs for deterministic pipelines.
- **Conditional Edges**: Use logic to determine control flow dynamically based on LLM output or tool results.
- **Subgraphs**: Encapsulate complex sub-processes into compiled subgraphs to manage complexity.

## Cognitive Architectures
### Reflexion
- **Pattern**: Generate -> Critique -> Revise.
- **Implementation**: A node that evaluates the previous output and generates feedback, leading back to the generation node.
- **Use Case**: Code generation, complex writing, multi-step reasoning.

### Plan-and-Execute
- **Pattern**: Planner Agent (breaks down task) -> Executor Agent (performs steps) -> Re-planner (adjusts plan).
- **Implementation**: Explicit state for `plan` (list of steps) and `current_step`.
- **Use Case**: Long-horizon tasks, research, ambiguous requests.

### Tool Use & ReAct
- **Pattern**: Reason -> Act (Call Tool) -> Observe (Result) -> Reason.
- **Best Practices**:
    - **Robust Schemas**: Pydantic models for tool arguments with clear descriptions.
    - **Error Handling**: Tools should return error messages gracefully to the LLM, not crash the process.
    - **Granularity**: Tools should be atomic and focused (Single Responsibility).

## Deep Agents Concepts
- **Skills**: Modular capabilities (like this one) that extend agent functionality without bloating the core prompt.
- **Memory**:
    - *Short-term*: Conversation history (managed by LangGraph).
    - *Long-term (Core)*: User preferences, facts, project rules (stored in vector DB or structured store).
- **Subagents**: Specialized agents for distinct domains (e.g., "Researcher", "Coder"). Delegate tasks rather than doing everything in one prompt.

## Agentic UX
- **Transparency**: Stream intermediate steps (thought process) to the user.
- **Control**: Implement Human-in-the-loop (interrupts) for sensitive actions (write file, deploy).
- **Feedback**: Allow users to correct the agent's course during execution.
