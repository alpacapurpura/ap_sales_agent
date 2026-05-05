# 03-arch-agentic.md — Eval Runner Foundation (Agentic harness)

---
story_id: sales-agent-eval-runner-foundation
surface: AGENTIC
sub_architect: /architect (acting BE+Agentic — no recursion per /pm prompt)
arch_version: 1
last_modified: 2026-05-05T03:35Z
links:
  spec: "01-spec.md"
  arch_be: "03-arch-be.md"
  story_yaml: "../../../../../../product/stories/sales-agent/sales-agent-eval-runner-foundation.yaml"
  rules:
    - ".claude/rules/sales-agent-brand-voice.md"
    - ".claude/rules/copilot-observability.md"
    - ".claude/rules/anti-duplication.md"
    - ".claude/rules/tenant-isolation.md"
  skills_consulted:
    - sales-agent-expert
    - copilot-expert
    - tessl__langgraph
    - tessl__graceful-degradation
---

## Decisión arquitectónica clave

El **trajectory spy** se implementa como un **observer pasivo encima del `BaseAgentCallbackHandler` existente**, NO como subclase ni mirror. Reusamos verbatim el `SalesAgentObservabilityContext` (factory que ya wrappea `agent_app.ainvoke` con `RunnableConfig` + callback handler que escribe a `sales_agent_trace_event` y `sales_agent_llm_call`). El spy adiciona dos hooks `extra_callbacks` que LangChain compose-encadena:

1. Lee `state["next_node"]` en cada `on_chain_end` (LangGraph node exit) — es la SSoT de routing post-redesign 2026-04 (verificado en `application/orchestrator/state.py:18` + `agents/sales/graph.py:18 _route_after_supervisor`).
2. Lee `tool_name` en cada `on_tool_end` — usa el mismo `serialized.get("name")` ya extraído por la base.

Resultado: **zero changes a `src/modules/sales_agent/`**. El spy vive en `tests/agentic_evals/sales_agent/runner/trajectory_spy.py`, anti-duplication satisfecho — extiende vía composición, NO mirror el handler shared.

**Prompt cache invariant:** el harness invoca `agent_app.ainvoke` con el `initial_state` real construido por `create_initial_state(...)` (state.py) + `build_agent_identity` + `build_brand_voice` (knowledge_builder). Slot 5 `BRAND_VOICE` = `state["brand_voice"]` poblado desde `PersonalityProfile.system_instruction` en runtime (compiler v2 prod path). **Smoke NO override voz, NO modifica slots, NO mide cache_hit_rate.** Decisión B6 ratificó: cache fidelity es scope Story 7 (multi-turn voice grader).

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (extends 03-arch-be audit)

### Audit cross-codebase ejecutado
```bash
# Trayectoria — ¿existe ya un spy de state machine?
grep -rn "specialist_history\|trajectory" backend/src/modules/sales_agent/  # → 0 (campo no existe)
grep -rn "next_node" backend/src/modules/sales_agent/application/agents/sales/nodes.py  # → 9 (routing canónico)

# ¿Existe un trajectory recorder en copilot que podamos lift?
grep -rn "trajectory\|specialist_history" backend/src/modules/copilot/  # → 0
grep -rn "trajectory" backend/src/shared/  # → 0

# ¿Existe agentevals dep?
grep "agentevals" backend/pyproject.toml  # → 0

# Tools registry post-redesign — qué tool names canónicos existen?
grep -n "_REGISTRY\|: tool_" backend/src/modules/sales_agent/application/agents/sales/tools.py
grep -n ": tool_\|REGISTRY" backend/src/modules/sales_agent/application/agents/sales/enrollment_tools.py
grep -n ": tool_" backend/src/modules/sales_agent/application/tools/scheduling/tools.py
grep -n ": tool_" backend/src/modules/sales_agent/application/tools/payment/tools.py
```

### Sistemas existentes encontrados

| Sistema | Path | Función | T-ticket usage |
|---|---|---|---|
| `BaseAgentCallbackHandler` (shared) | `shared/agent_observability/recording/base_callback_handler.py:80` | 8 LangChain callbacks + Template Method + cost calculation | T3 reuses via `extra_callbacks` chain — NO subclass |
| `SalesAgentCallbackHandler` (sales subclass) | `sales_agent/observability/recording/callback_handler.py:49` | Persists rows to `sales_agent_llm_call` + `sales_agent_trace_event` | T3 reuses verbatim via `build_sales_agent_observability_context` factory |
| `SalesAgentObservabilityContext` | `sales_agent/observability/recording/turn_envelope.py:67` | Wraps `agent_app.ainvoke` with `observe_turn` + `langchain_config()` | T3 invokes verbatim |
| `agent_app` canonical entry | `sales_agent/application/orchestrator/graph.py:52` | Compiled `StateGraph` | T2 `sales_agent_entrypoint` invokes |
| Sales-subgraph topology | `sales_agent/application/agents/sales/graph.py:42 create_sales_subgraph` | supervisor → {qualifier, product_expert, closer, tool_executor, escalation} → signal_accumulator → END | T3 spy reads state at `on_chain_end` |
| Tool registries (4 files unified) | tools listed below | dispatch table for `tool_executor` node | T4 maps B4 spec → real tool names (see § Tool registry mapping) |

### Decisión por sistema

- **`BaseAgentCallbackHandler` + `SalesAgentCallbackHandler`**: **REUSE via composition**. The spy is a `BaseCallbackHandler` (LangChain native) added as a second handler in the same `RunnableConfig.callbacks` list. Both handlers execute in order; the spy reads state from `inputs`/`outputs` of `on_chain_*` calls but never persists to DB (read-only observer). This is canonical LangChain pattern (multiple callback handlers per run).
- **`SalesAgentObservabilityContext`**: **REUSE verbatim**. T2 calls `build_sales_agent_observability_context(...)` — the factory wraps the same handler chain. T3 EXTEND: spy is added to the chain after factory build via `obs_ctx.callback_handler` accessor or by extending `RunnableConfig.callbacks` list at invoke-time.
- **Sales-subgraph**: **READ ONLY**. The spy walks `state["next_node"]` history accumulating per node visit. It never writes back to state.

## State machine details (sales_agent post-redesign 2026-04)

### State shape (canonical fields the spy reads)

From `src/modules/sales_agent/application/orchestrator/state.py:8 AgentState`:

| Field | Type | Spy usage |
|---|---|---|
| `next_node` | `str \| None` | **PRIMARY trajectory marker.** Captured at every `on_chain_end` event. Sequence builds `specialist_history` equivalent. Values per `graph.py:18 _route_after_supervisor`: `qualifier`, `product_expert`, `closer`, `tool_executor`, `escalate`, `respond` |
| `tenant_id` | `UUID \| None` | Asserted vs Visionarias UUID by Capa 4 cross-tenant guard |
| `current_state` | `str \| None` | secondary — stage transition (`rapport`, `discovery`, `presentation`, `closing`) |
| `_pending_tool` | `dict \| None` | secondary — what tool is queued |
| `messages` | `list[dict]` | LAST entry = response text (Capa 3) |
| `lead_data`, `buying_signals`, `qualification_answers` | various | NOT read by smoke (scope Story 6 personas) |

### Topology (from `agents/sales/graph.py:42`)

```
START
  └─→ supervisor
        └─[_route_after_supervisor]─→ {qualifier | product_expert | closer | tool_executor | escalate | respond=END}
              ↓ (specialists return)
              ↓
            signal_accumulator
              └─[_route_after_accumulator]─→ {tool_executor | respond=END}
                    ↓ (tool_executor)
                    ↓
                  supervisor   ← LOOP
```

**Anti-loop guard:** `tool_call_dedup.py::ToolCallDedupTracker` cementado post-fbc79125 (per `sales-agent-expert` skill §3 — "no se toca"). Recursion limit env `COPILOT_RECURSION_LIMIT` default 25. Smoke single-turn input → routing path: `START → supervisor → qualifier → signal_accumulator → END (respond)` — 4 node visits, well under recursion limit.

### Topology classification

- [ ] Single ReAct agent (no — multi-specialist)
- [x] **Supervisor pattern** — `supervisor` is the routing hub. `_route_after_supervisor` is conditional edges. Per `tessl__langgraph` skill `Conditional Branching` pattern.
- [ ] deepagents `task` tool with subagents (no — sales_agent uses native StateGraph per §3 skill rule "no migrar StateGraph a deepagents")

## Trajectory spy design (T3 detail)

### Class shape

```python
# tests/agentic_evals/sales_agent/runner/trajectory_spy.py
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID
from langchain_core.callbacks import BaseCallbackHandler

@dataclass
class TrajectorySpy(BaseCallbackHandler):
    """Read-only observer of LangGraph state transitions for eval harness.

    Adds zero persistence — purely in-memory accumulation. Pairs with
    `SalesAgentCallbackHandler` in the same `RunnableConfig.callbacks`
    list. NEVER writes to sales_agent_trace_event/_llm_call (the sister
    handler does that). NEVER mutates state.

    Cohabits with the `trace_node` decorator on supervisor + sales_agent
    nodes (`infrastructure/monitoring/tracing.py`) — both observers run
    independently per LangChain callback contract.
    """
    specialist_history: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    node_visits: list[dict[str, Any]] = field(default_factory=list)

    def on_chain_end(self, outputs: dict[str, Any], *,
                     run_id: UUID, parent_run_id: UUID | None = None,
                     **kwargs: Any) -> None:
        """Capture state.next_node from outputs after each LangGraph node exit."""
        if isinstance(outputs, dict):
            next_node = outputs.get("next_node")
            if isinstance(next_node, str) and next_node not in {"respond", None}:
                self.specialist_history.append(next_node)

    def on_tool_end(self, output: Any, *, run_id: UUID,
                    parent_run_id: UUID | None = None,
                    **kwargs: Any) -> None:
        """Append tool call name to the captured list. Name extraction
        relies on the parent on_tool_start having already cached run_id
        in our local span dict — but we use a simpler approach: capture
        from kwargs.get('serialized', {}).get('name') via on_tool_start.
        """
        # Implementation detail: we maintain a local _tool_runs dict
        # keyed by run_id, populated from on_tool_start, drained here.
        ...

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, *,
                      run_id: UUID, **kwargs: Any) -> None:
        """Cache tool name + input for later pairing in on_tool_end."""
        ...

    def reset(self) -> None:
        """Clear accumulated state. Called by fixture teardown."""
        self.specialist_history.clear()
        self.tool_calls.clear()
        self.node_visits.clear()

    def to_artifact_dict(self) -> dict[str, Any]:
        """Serialize for trace.json (sanitize_payload applied by writer)."""
        return {
            "specialist_history": self.specialist_history,
            "tool_calls": self.tool_calls,
            "node_visits": self.node_visits,
        }
```

### Wiring into the run

```python
# In sales_agent_entrypoint fixture (T2):
spy = TrajectorySpy()
obs_ctx = build_sales_agent_observability_context(...)  # native handler (writes DB)

# Compose callbacks list at invoke time:
config = obs_ctx.langchain_config()
existing_callbacks = config.get("callbacks", [])
config["callbacks"] = list(existing_callbacks) + [spy]

async with obs_ctx.observe_turn(...):
    result = await agent_app.ainvoke(initial_state, config=config)
```

`tessl__graceful-degradation` Rule 6: spy callbacks wrapped in `try/except` + `structlog.warning` (best-effort) — never break the eval if spy logic crashes.

### Artifacts persistence (T3)

After `agent_app.ainvoke` returns:
```python
# tests/agentic_evals/sales_agent/runner/artifacts.py
def write_run_artifacts(run_id: UUID, *, spy: TrajectorySpy, response_text: str,
                        assertions_results: dict[str, Any]) -> Path:
    base = Path("backend/tests/agentic_evals/sales_agent/_artifacts") / str(run_id)
    base.mkdir(parents=True, exist_ok=True)
    # PII safety: sanitize_payload applied to spy state + response (per spec NFR PII)
    (base / "trace.json").write_text(json.dumps(
        sanitize_payload(spy.to_artifact_dict()), indent=2, default=str
    ))
    (base / "response.txt").write_text(sanitize_payload({"response": response_text})["response"])
    (base / "assertions.json").write_text(json.dumps(assertions_results, indent=2, default=str))
    return base
```

`sanitize_payload` reused from `shared/agent_observability/recording/sanitization.py` per anti-duplication rule.

## Tool registry mapping (B4 → actual tool names)

**Decision B4 ratified intent:**
- `required: [entry intent classifier tool]`
- `forbidden: [payment_*, scheduling_*, closer_finalize_*]`

### Required tools — RESOLVED: `[]` (empty list)

**Finding:** post-redesign 2026-04, sales_agent does NOT use a "tool"-style intent classifier. Intent detection is a **service** call inside `ConversationPipeline.prepare_messages_and_intent` (`conversation_pipeline.py:430`):

```python
detected_intent, intent_score, updated_signals = SemanticRouter.detect_and_accumulate(
    incoming.text, existing_signals=initial_state.get("buying_signals", []),
    tenant_id=tenant_uuid,
)
```

`SemanticRouter` (`application/services/semantic_router.py:38`) uses cosine similarity over embeddings — NOT a LangChain `@tool`. It runs **before** `agent_app.ainvoke`, so it never appears in `on_tool_start`/`on_tool_end` callbacks. The actual entry "intent" is the **`supervisor` node** (StateGraph routing function `_route_after_supervisor`) which is a chain node, not a tool.

**Resolution:** golden YAML sets `required_tools: []` (empty). Smoke single-turn cold lead expectation = qualifier specialist asks discovery questions, **does NOT call any tool**. Capa 1 (trajectory) covers the entry classifier intent via `state.next_node = "qualifier"`. Capa 2 (required tools) is empty by design for this turn.

**Story 8 future-proof:** if `SemanticRouter` is migrated to a `@tool` (post-PI-12), add its name to `required_tools`. Documented in T6 README + golden `metadata.notes`.

### Forbidden tools — RESOLVED: actual tool name strings

From cross-codebase grep of `_REGISTRY` dicts (verified 2026-05-05):

| Spec intent (B4) | Actual tool names (post-redesign 2026-04) | Source path |
|---|---|---|
| `payment_*` | `send_payment_link`, `generate_payment_link`, `create_payment_link`, `verify_payment_status`, `mark_enrollment_paid_manual`, `check_payment_status`, `grant_access` | `agents/sales/tools.py:108`, `agents/sales/enrollment_tools.py:326-333`, `tools/payment/tools.py:400` |
| `scheduling_*` | `check_schedule`, `create_booking_link`, `verify_booking_status`, `get_available_slots` | `agents/sales/tools.py:109`, `tools/scheduling/tools.py:313-316` |
| `closer_finalize_*` | `create_enrollment`, `mark_enrollment_paid_manual`, `promote_waitlist_to_edition`, `grant_access` | `agents/sales/enrollment_tools.py:328-333`, `tools/payment/tools.py:403` |

**Final golden `forbidden_tools` list (deduplicated):**
```yaml
forbidden_tools:
  # payment family
  - send_payment_link
  - generate_payment_link
  - create_payment_link
  - verify_payment_status
  - mark_enrollment_paid_manual
  - check_payment_status
  - grant_access
  # scheduling family
  - check_schedule
  - create_booking_link
  - verify_booking_status
  - get_available_slots
  # closer-finalize family (NOT yet listed in payment/scheduling)
  - create_enrollment
  - promote_waitlist_to_edition
```

These are **canonical names per `STAGE_TOOL_SCOPE`** (`application/tools/registry.py:56`) — closing-stage-only tools that should never appear in a cold-lead first turn.

**Permitted tools in rapport stage** (per `STAGE_TOOL_SCOPE["rapport"] = frozenset()` + `ALWAYS_AVAILABLE`):
- `escalate_to_human`, `recommend_product` (cross-stage utilities — not asserted required, not asserted forbidden)

## Prompt cache invariants honored (B6 boundary)

The harness invokes `agent_app.ainvoke` with `initial_state["agent_identity"]` + `initial_state["brand_voice"]` populated by the production `TenantKnowledgeBuilder` (no test-only override). The compose-time slot composition (slots 1-6 cacheable cross-tenant + per-tenant, slot 7+ volatile per-turn) is owned by `application/prompts/compose.py` per `sales-agent-expert` skill §SSoT — **untouched by harness**.

The trajectory spy reads state AFTER node execution; the LLM call has already happened with the production prefix. **Cache_hit_rate is observed by the production callback handler** writing to `sales_agent_llm_call.cached_read_tokens` — visible to the harness via Capa 4 SQL query, BUT smoke does NOT assert on it (Decision B6: cache rate is multi-turn metric, single-turn smoke cannot measure rate).

**Forbidden in the harness (would invalidate cache):**
- ❌ Inject `{tenant_name}` mid-block in slot prefix
- ❌ Override `system_instruction` with a test fixture
- ❌ Force `temperature` ≠ default per spec
- ❌ Wipe `agent_identity` / `brand_voice` (would break slot 4/5 cache)

**Validation runtime check** (T3 spy adds soft assertion):
```python
def assert_cache_prefix_intact(initial_state: dict) -> None:
    """Defensive — log warning (NOT fail) if slot 4/5 fields are empty."""
    if not initial_state.get("agent_identity"):
        logger.warning("eval_runner_slot4_empty",
                       msg="agent_identity unset; cache prefix may underperform")
    if not initial_state.get("brand_voice"):
        logger.warning("eval_runner_slot5_empty",
                       msg="brand_voice unset; voice fidelity at risk")
```

This is logged in `_artifacts/{run_id}/trace.json` for Story 7 voice grader to inspect post-hoc.

## Voice fidelity grader hooks (Story 7 future-proof)

The assertion library exposes a placeholder slot per spec §"Voice fidelity grader hooks":

```python
# tests/agentic_evals/sales_agent/runner/assertions.py (T4)
def assert_voice_fidelity(response: str, *, threshold: float = 0.7,
                          personality_profile_id: UUID | None = None) -> None:
    """Story 7 LLM-as-judge slot. NOT invoked in smoke (Decision B6).

    Story 7 will implement: load PersonalityProfile.system_instruction,
    call NANO LLM-as-judge with rubric "voice_anchors_match", parse
    score, raise if score < threshold. For now, the function exists so
    Story 7 builders don't need to reshape the assertion API.
    """
    raise NotImplementedError(
        "assert_voice_fidelity is a Story 7 placeholder. "
        "Smoke (foundation) does not validate voice — see Decision B6."
    )
```

Tests for Story 7 will replace `raise NotImplementedError` with the real grader. The smoke tests do NOT call this function — calling it raises NotImplementedError loudly so accidental misuse is caught.

## PersonalityProfile.system_instruction NOT overridden

Per `.claude/rules/sales-agent-brand-voice.md` § "Excepción" + Decision B6:
- Fixture `sales_agent_entrypoint` calls `TenantKnowledgeBuilder(db).build_brand_voice(visionarias_id)` — production compiler v2 path.
- Output `state["brand_voice"]` populated from `personality_profiles.system_instruction` row in DB (real Visionarias config).
- If Visionarias has voseo voice → output may have voseo. `assert_output` validates Spanish density (langdetect + marker count), NEVER style. Compliant with skill rule "voseo del tenant respetado — NO aplica `.claude/rules/spanish-text.md` al output del agente".

## Eval goldens (B6 + B7)

**Foundation deliverable (B7):**
- 1 YAML golden checked-in: `tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml`
- 4 scenarios in `test_eval_runner_smoke.py` (happy + flag-omitted-skip + degraded-mock + cross-tenant-leak)
- **NO voice fidelity grader call** — Story 7 scope per B6
- **NO pass^k aggregation** — Story 2 scope per B1 (`trials_per_scenario: 1` for smoke)

**Story 5 future-proof (3-tenant goldens):**
- `golden_loader.py` (T5) accepts `*.yaml` glob — drops in `goldens/visionarias-*.yaml`, `goldens/T2-*.yaml`, etc.
- Each YAML carries `tenant_id_env` referencing env var; fixture resolves to UUID at run time. Multi-tenant goldens drop in without harness changes.
- pytest-parametrize loop already supported via `pytest.mark.parametrize` over `golden_loader.list_goldens()`.

## RAG / Qdrant

**Not applicable** for this story. Sales_agent does NOT consume RAG via `KnowledgeService` in the smoke turn (smoke is single-turn input, no knowledge retrieval). Story 5 (3-tenant goldens) may include knowledge_search-triggering inputs — at which point T6 README will document the precondition.

## Skill decisions referenced

- **`sales-agent-expert`** §3 "NO se toca" — confirmed: harness does NOT touch `closer_studio.py`, `BufferService`, `OutputManager` chunking, enrollment_*, webhook adapters, follow_up_engine, or `tool_call_dedup`. All accessed surfaces are read-only.
- **`sales-agent-expert`** §"Anti-patterns" — confirmed: no StateGraph→deepagents migration, no subagent creation, no canal hardcoding (uses `channel_type="eval_harness"` registered as ad-hoc literal — documented in T2).
- **`sales-agent-expert`** SSoT — voice via `personality_profiles.system_instruction` slot 5 prefix; harness honors prod compiler.
- **`copilot-expert`** §"Stop. Lee primero" — same diagnosis discipline; bug = trazas first. Harness's Capa 4 (cost) verifies `sales_agent_llm_call` writes; if 0 rows + structlog warning, harness fails explicit "Cost layer un-verifiable".
- **`tessl__langgraph`** "Conditional Branching" pattern — sales_agent topology classified as supervisor pattern. State management via TypedDict canonical.
- **`tessl__graceful-degradation`** Rule 1 (every external call timeout): LiteLLM client already has 5s timeout (`tessl__graceful-degradation` cemented in `providers/litellm.py`). Harness inherits.
- **`tessl__graceful-degradation`** Rule 6 (log failures with context): trajectory spy + artifacts writer wrapped in `try/except` + `structlog.warning` per copilot-observability best-effort rule.
- **`anti-duplication`** §0: `BaseAgentCallbackHandler`, `SalesAgentCallbackHandler`, `SalesAgentObservabilityContext`, `FXResolver.default()`, `PricingResolver`, `sanitize_payload`, `TenantKnowledgeBuilder` — all reused verbatim. Zero new mirror.

## Riesgos y mitigaciones (agentic-specific)

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Spy callbacks colisionan con `trace_node` decorator + native handler → orden no determinístico | medium | LangChain spec: callbacks ejecutan en orden de la lista. Spy AÑADIDO al final de `config["callbacks"]`. Native handler ejecuta primero (DB write), spy después (in-memory read). Documentado en T3 inline. |
| `tool_call_dedup.py` interfiere con tool capture en spy | low | Dedup vive dentro del `tool_executor` node (post-tool-end persiste el dedup tracker). Spy lee `on_tool_end` callback ANTES — captura todos los intentos pre-dedup. Para smoke single-turn no aplica (no tools fired). |
| Silent prompt cache invalidation por sub-test (Scenario 3 mockea LLM) | medium | Scenario 3 reemplaza `LiteLLMService.generate_response` por mock — bypass del LLM real, NO invalida cache (cache es server-side Anthropic prefix; client mock no afecta). Documentado en T5. |
| Real LLM costo por flake en CI nightly (Story 8) | medium | Spec NFR `< $0.01/run`. Alert `>$0.05` flag potential loop. Story 3 budget cap implementa hard limit. |
| `state["next_node"]` ausente en algunos `on_chain_end` outputs (LangGraph behavior) | low | Spy chequea `isinstance(next_node, str)` antes de append. Defensive — si nodo no setea `next_node`, queda fuera del history (consistente con `_route_after_supervisor` default). |

## Decisiones registradas

- **2026-05-05 — composition over subclass:** spy es `BaseCallbackHandler` independiente, NO subclase de `BaseAgentCallbackHandler`. Razón: subclase requiere reimplementar abstract methods `_persist_*` con stubs vacíos → noisy. Composition (lista de callbacks) es canonical LangChain pattern + zero abstract method override.
- **2026-05-05 — `state["next_node"]` como SSoT trayectoria:** descartado agregar `state["specialist_history"]: list[str]` (sería cambio en `state.py` = `src/` modification, fuera del out-of-scope del story). El spy reconstruye history desde `on_chain_end` events — equivalent semantics, zero src/ change.
- **2026-05-05 — `required_tools: []` en smoke:** descubrimiento: post-redesign 2026-04, intent classification es service (`SemanticRouter`), no tool. Capa 1 trajectory cubre intent via `next_node = "qualifier"`. Documentado para Story 8 si futura migración a `@tool` reabre.
- **2026-05-05 — Scenario 3 monkeypatch target:** mockea `LiteLLMService.generate_response` (no `agent_app.ainvoke`) → preserva el flujo del state machine + spy real, solo inyecta payload degradado en el LLM response. Test del harness, no del agente.

## Próximo paso

`done -> 03-arch-agentic.md` (devuelvo referencia al orchestrator /architect).
