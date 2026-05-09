"""Agent bridge — in-process invocation of production sales_agent runtime (T-7).

Adapted from ``client_simulator/src/simulator/agent_bridge.py`` (legacy
preserved byte-equal under ``client_simulator/`` per D6) — re-shaped to:

* Replace the legacy HTTP webhook (``httpx.AsyncClient.post``) with an
  in-process ``await agent_app.ainvoke(...)`` call (D1 spec ratified).
* Reuse the production ``ConversationPipeline.{build_identity,
  build_brand_voice, create_initial_state}`` helpers — paridad with
  ``backend/tests/agentic_evals/sales_agent/fixtures/entrypoint.py``.
* Wire ``EvalSimulatorObservabilityContext`` (T-5) so every persisted
  row carries the H5 6-key ``eval_metadata`` jsonb — cost-bucket
  separation enforced at the table level (eval_simulator_llm_call vs
  sales_agent_llm_call).
* Map every failure mode to :class:`AgentErrorSubtype` + emit a
  canonical ``structlog`` event per H7 taxonomy.
* Apply :func:`assert_no_leak` post-extract as a defense-in-depth
  warning (NEVER raises here — adversarial smoke tests in T-10 own the
  raise).

Anti-duplication §0
===================

This module REUSES verbatim:

* :data:`agent_app` — production graph entrypoint
  (``backend/src/modules/sales_agent/application/orchestrator/graph.py:52``).
* :class:`TenantKnowledgeBuilder` — slots 4 + 5 builders
  (``build_identity`` + ``build_brand_voice``). Production canonical.
* :func:`create_initial_state` — Pydantic-free TypedDict factory
  (``backend/src/modules/sales_agent/application/orchestrator/state.py``).
* :func:`build_eval_simulator_observability_context` — T-5 factory.

Zero mirror — these symbols are imported, not redeclared.

LangGraph contract
==================

* Returns a partial state dict (NEVER mutates ``state`` in place).
  Success path::

      {"transcript": [agent_turn], "last_agent_response": text}

  Failure path (4 modes per H7 taxonomy)::

      {"is_finished": True,
       "termination_reason": TerminationReason.AGENT_ERROR,
       "error_subtype": AgentErrorSubtype.<MODE>}

* Reducer ``Annotated[list[ConversationTurn], operator.add]`` (declared
  on :class:`SimulationState.transcript`) merges the new turn append-only.
* No ``from __future__ import annotations`` — LangGraph runtime
  introspection requires resolved annotations on async nodes (story-wide
  cement; same root cause as ``state.py`` / ``customer_node.py`` /
  ``observability.py``).

Failure mode taxonomy (H7)
==========================

+-----------------------------+--------------------------------------+----------------------------------+
| Trigger                     | Mapped ``AgentErrorSubtype``         | Emitted ``structlog`` event      |
+=============================+======================================+==================================+
| ``asyncio.TimeoutError``    | :data:`AgentErrorSubtype.TIMEOUT`    | ``simulator.agent_timeout``      |
| Empty agent response        | :data:`AgentErrorSubtype.EMPTY_RESP..| ``simulator.agent_empty_response``|
| ``httpx.HTTPStatusError``   | :data:`AgentErrorSubtype.HTTP_ERROR` | ``simulator.agent_http_error``   |
| Missing last customer turn  | :data:`AgentErrorSubtype.INVALID_S.. | ``simulator.agent_invalid_state``|
| Other ``Exception``         | :data:`AgentErrorSubtype.INVALID_S.. | ``simulator.agent_invalid_state``|
+-----------------------------+--------------------------------------+----------------------------------+

Each failure path returns ``is_finished=True`` + ``termination_reason=AGENT_ERROR``
so the graph conditional edge (T-8 ``should_continue``) terminates the
simulation cleanly without bubbling.

Defense in depth (H10)
======================

Post-extract, the agent response is scanned for forbidden leak strings
via :func:`assert_no_leak`. Match → ``simulator.system_prompt_leak_detected``
warning emitted (and ``AssertionError`` raised inside the helper, but
the bridge catches it: the warning is the actionable signal; raising
here would corrupt the transcript). Adversarial smoke tests (T-10 Story
I) call ``assert_no_leak`` directly on the full transcript with raise
enabled.

# voseo-allowed: docstring quotes structlog event names + voice anchor markers
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4).
# Same root cause as ``state.py`` / ``customer_node.py`` / ``observability.py``:
# LangGraph runtime introspection requires resolved annotations on the
# async node defined here.

import contextlib
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import httpx
import structlog

from tests.agentic_evals.sales_agent.simulator._internal.leak_assertions import (
    assert_no_leak,
)
from tests.agentic_evals.sales_agent.simulator.result import ConversationTurn
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
)

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════
# Session resolver — internal helper. The ``run_simulation`` orchestrator
# (``_internal/runner.py``) sets the ``_simulation_db_session_var`` ContextVar
# on entry and resets it on exit (try/finally). This helper reads the var.
#
# ContextVars are asyncio-task-local — safe under concurrent simulations
# (each ``asyncio.gather`` task gets its own copy). They were the canonical
# bridge sketched in the T-7 stub docstring; DEEPER-A regression
# (2026-05-08 post Story D archive) cemented the wiring once a real-LLM
# smoke run surfaced ``SessionUnavailable`` despite the runner accepting
# ``db_session`` correctly.
#
# Existing T-7 unit tests that monkeypatch this helper directly continue
# to work — ``monkeypatch.setattr(bridge_mod, "_resolve_session_for_simulation",
# lambda _state: stub)`` replaces the function, bypassing the ContextVar
# read entirely.
# ════════════════════════════════════════════════════════════════════════

# Module-level ContextVar — default ``None`` matches the legacy "session
# unavailable" branch when no runner has set it (e.g. helper invoked
# outside a ``run_simulation`` task scope).
_simulation_db_session_var: ContextVar[Any | None] = ContextVar(
    "_simulation_db_session_var",
    default=None,
)


def _set_simulation_db_session(session: Any) -> Token[Any | None]:
    """Set the simulation's SQLAlchemy session for the current asyncio task.

    Returns a :class:`contextvars.Token` the caller MUST pass back to
    :func:`_reset_simulation_db_session` (typically inside a try/finally
    block) so the ContextVar is restored to its previous value — even if
    the wrapped invocation raises.

    Used by ``run_simulation`` to bridge its ``db_session`` parameter to
    ``_resolve_session_for_simulation``.

    Args:
        session: The SQLAlchemy ``Session`` to expose to the bridge. May
            be ``None`` to explicitly mark "no session for this turn"
            (the bridge will then take the INVALID_STATE termination path).

    Returns:
        A :class:`contextvars.Token` for restoration.
    """
    return _simulation_db_session_var.set(session)


def _reset_simulation_db_session(token: Token[Any | None]) -> None:
    """Restore the ContextVar to the value it held before the matching
    :func:`_set_simulation_db_session` call.

    Idempotent — calling with the same token multiple times raises
    :class:`LookupError`; callers should invoke this exactly once per
    set, inside a ``try/finally`` block.

    Args:
        token: The token returned by the matching set call.
    """
    _simulation_db_session_var.reset(token)


def _resolve_session_for_simulation(state: SimulationState) -> Any:
    """Resolve the SQLAlchemy ``Session`` for the current simulation.

    Reads the ``_simulation_db_session_var`` ContextVar. The value is set
    by ``run_simulation`` (``_internal/runner.py``) before invoking the
    LangGraph and reset after — ContextVars are asyncio-task-local so
    concurrent simulations do not collide.

    Returning ``None`` triggers an :class:`AgentErrorSubtype.INVALID_STATE`
    termination — the bridge cannot persist observability rows or load the
    agent_identity / brand_voice without a session.

    Args:
        state: Current simulation state. Reserved for future per-state
            resolution (e.g. multi-tenant simulator pools); unused today.

    Returns:
        SQLAlchemy ``Session`` bound to the eval tenant, or ``None`` when
        the runner did not inject one (e.g. ``db_session=None`` caller).
    """
    del state  # reserved for future per-state resolution
    return _simulation_db_session_var.get()


# ════════════════════════════════════════════════════════════════════════
# Public LangGraph node
# ════════════════════════════════════════════════════════════════════════


def _build_terminal_dict(
    error_subtype: AgentErrorSubtype,
) -> dict[str, Any]:
    """Build the canonical terminal-state partial dict for a failure mode.

    Centralized so every except branch writes a consistent shape — the
    H8 termination registry's ``_agent_error_predicate`` (T-4) reads
    ``state.is_finished`` AND ``state.termination_reason`` to confirm
    AGENT_ERROR. ``error_subtype`` carries the H7 taxonomy detail.
    """
    return {
        "is_finished": True,
        "termination_reason": TerminationReason.AGENT_ERROR,
        "error_subtype": error_subtype,
    }


async def agent_bridge(state: SimulationState) -> dict[str, Any]:  # noqa: PLR0911 — H7 taxonomy: each failure-mode path returns a distinct terminal dict (4 modes + 2 success/cleanup). Centralizing via _build_terminal_dict already, but each except branch needs its own canonical structlog event before returning. This is the cement of the H7 cardinal — refactoring to a single return would conflate event names.
    """LangGraph node — invoke production ``agent_app`` in-process.

    Topology (per 03-arch-agentic §2.4):

    1. Extract last customer turn from ``state.transcript`` (or terminate
       INVALID_STATE).
    2. Resolve the simulation's SQLAlchemy session (or terminate
       INVALID_STATE).
    3. Lazy-import the production ``agent_app`` + ``TenantKnowledgeBuilder``
       + ``create_initial_state`` (paridad with ``outbound_orchestrator.py``
       and ``fixtures/entrypoint.py``).
    4. Build slots 4 (agent_identity) + 5 (brand_voice) via the canonical
       knowledge builder (no override — production cement).
    5. Compose the agent's initial state via ``create_initial_state`` with
       ``channel_type='eval_simulator'`` so the agent runtime's downstream
       observability marker is set correctly.
    6. Build the eval-simulator observability context (T-5 factory).
       Failure → ``None``, the bridge falls back to invocation without
       observability (best-effort per copilot-observability rule).
    7. Invoke ``await agent_app.ainvoke(initial_state, config=...)``
       INSIDE ``async with obs.observe_turn(...)`` so ``turn_start`` and
       ``turn_end`` rows persist around the LangGraph stream.
    8. Extract the agent's text response from the final state's last
       message.
    9. Apply :func:`assert_no_leak` post-extract (defense-in-depth H10 —
       warning only, no raise).
    10. Append the agent turn to the transcript via the LangGraph
        ``operator.add`` reducer (return ``{"transcript": [agent_turn]}``).

    Failure modes (H7 taxonomy) — each returns a terminal partial dict:

    * ``asyncio.TimeoutError`` → :data:`AgentErrorSubtype.TIMEOUT`
    * Empty agent response → :data:`AgentErrorSubtype.EMPTY_RESPONSE`
    * ``httpx.HTTPStatusError`` (wrapped or raw) →
      :data:`AgentErrorSubtype.HTTP_ERROR`
    * Missing customer turn / session resolution failure / generic
      ``Exception`` → :data:`AgentErrorSubtype.INVALID_STATE`

    Args:
        state: Current :class:`SimulationState` (Pydantic). The node
            reads ``transcript`` / ``tenant_id`` / ``simulation_id`` /
            ``run_id`` / ``archetype_slug`` / ``actor_profile.id`` /
            ``trial_n``; it never mutates ``state``.

    Returns:
        A partial state dict — either ``{"transcript": [agent_turn], ...}``
        on success or ``{"is_finished": True, ...}`` on failure.
    """
    # ── Step 1: Extract last customer turn ────────────────────────────
    last_customer_turn = next(
        (t for t in reversed(state.transcript) if t.role == "customer"),
        None,
    )
    if last_customer_turn is None:
        logger.warning(
            "simulator.agent_invalid_state",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class="MissingCustomerTurn",
            error="No customer turn in transcript — cannot dispatch to agent",
        )
        return _build_terminal_dict(AgentErrorSubtype.INVALID_STATE)

    # ── Step 2: Resolve session ───────────────────────────────────────
    db = _resolve_session_for_simulation(state)
    if db is None:
        logger.warning(
            "simulator.agent_invalid_state",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class="SessionUnavailable",
            error="Runner failed to inject SQLAlchemy session for simulation",
        )
        return _build_terminal_dict(AgentErrorSubtype.INVALID_STATE)

    # ── Step 3: Lazy imports (paridad customer_node + outbound_orchestrator) ─
    # Lazy so the agentic_evals subtree can be collected without forcing
    # the production sales_agent module to import-resolve at test
    # collection time. Tests patch the canonical module symbols so the
    # lazy load picks up the mocks.
    from src.modules.sales_agent.application.orchestrator.graph import agent_app
    from src.modules.sales_agent.application.orchestrator.state import (
        create_initial_state,
    )
    from src.modules.sales_agent.application.services.knowledge_builder import (
        TenantKnowledgeBuilder,
    )
    from tests.agentic_evals.sales_agent.simulator._internal.observability import (
        build_eval_simulator_observability_context,
    )

    # ── Step 4: Build slot 4 + slot 5 via production canonical builder ─
    try:
        knowledge_builder = TenantKnowledgeBuilder(db)
        agent_identity = knowledge_builder.build_identity(state.tenant_id)
        brand_voice = knowledge_builder.build_brand_voice(state.tenant_id)
    except Exception as exc:  # noqa: BLE001 — graceful-degradation Rule 2
        logger.warning(
            "simulator.agent_invalid_state",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class=type(exc).__name__,
            error=str(exc),
            stage="knowledge_builder",
        )
        return _build_terminal_dict(AgentErrorSubtype.INVALID_STATE)

    # ── Step 5: Compose agent's initial state ─────────────────────────
    # Build a synthetic user_id (no real lead — eval simulator does not
    # touch crm.lead). The production state uses str(UUID), tenant_id is
    # str. channel_type='eval_simulator' marks the downstream observability
    # path so the agent runtime's callback can route accordingly.
    try:
        synthetic_user_id = str(uuid4())
        history = [{"role": t.role, "content": t.content} for t in state.transcript]
        initial_state = create_initial_state(
            user_id=synthetic_user_id,
            tenant_id=str(state.tenant_id),
            agent_identity=agent_identity,
            brand_voice=brand_voice,
            channel_type="eval_simulator",
            history=history,
        )
        # Inject the latest user message as the most recent turn so the
        # graph's first specialist sees what the customer just said.
        initial_state["messages"] = [
            {"role": "user", "content": last_customer_turn.content},
        ]
    except Exception as exc:  # noqa: BLE001 — graceful-degradation Rule 2
        logger.warning(
            "simulator.agent_invalid_state",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class=type(exc).__name__,
            error=str(exc),
            stage="create_initial_state",
        )
        return _build_terminal_dict(AgentErrorSubtype.INVALID_STATE)

    # ── Step 6: Build eval observability context ─────────────────────
    # H5 mandatory — propagates the 6-key eval_metadata to every persisted
    # row. Best-effort: factory returns None on construction failure;
    # bridge falls back to invocation without observability.
    obs_ctx = build_eval_simulator_observability_context(
        db=db,
        tenant_id=state.tenant_id,
        archetype_slug=state.archetype_slug,
        actor_profile_id=state.actor_profile.id,
        trial_n=state.trial_n,
        simulation_id=state.simulation_id,
        run_id=state.run_id,
        turn_id=uuid4(),
        role="agent",
    )

    # ── Step 7: Invoke agent_app.ainvoke (in-process — D1) ───────────
    # The shared ``BaseObservabilityContext.langchain_config()`` returns
    # ``dict[str, Any]`` (untyped legacy contract) — Pregel.ainvoke expects
    # ``RunnableConfig | None`` which is a TypedDict alias. We cast at the
    # call site to satisfy mypy strict; runtime behavior is unchanged
    # (LangChain accepts any dict-shape that conforms to RunnableConfig
    # protocol).
    from langchain_core.runnables import RunnableConfig

    try:
        if obs_ctx is not None:
            async with obs_ctx.observe_turn(
                message=last_customer_turn.content,
                route="sales_agent",
            ):
                lc_config = cast("RunnableConfig", obs_ctx.langchain_config())
                result = await agent_app.ainvoke(
                    initial_state,
                    config=lc_config,
                )
        else:
            # Best-effort fallback when obs context unavailable.
            # Pass None for `config` — mypy strict requires RunnableConfig
            # | None. None matches the production outbound_orchestrator
            # signature when there's no observability.
            result = await agent_app.ainvoke(initial_state, config=None)
    except TimeoutError as exc:
        logger.warning(
            "simulator.agent_timeout",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class=type(exc).__name__,
            error=str(exc),
        )
        return _build_terminal_dict(AgentErrorSubtype.TIMEOUT)
    except httpx.HTTPStatusError as exc:
        # Either raw or wrapped (some LiteLLM Proxy errors bubble up as
        # HTTPStatusError when the upstream LLM provider returns 5xx).
        logger.warning(
            "simulator.agent_http_error",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class=type(exc).__name__,
            error=str(exc),
            status_code=exc.response.status_code if exc.response is not None else None,
        )
        return _build_terminal_dict(AgentErrorSubtype.HTTP_ERROR)
    except Exception as exc:  # noqa: BLE001 — graceful-degradation Rule 2
        logger.warning(
            "simulator.agent_invalid_state",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class=type(exc).__name__,
            error=str(exc),
            stage="agent_app_ainvoke",
        )
        return _build_terminal_dict(AgentErrorSubtype.INVALID_STATE)

    # ── Step 8: Extract response text ────────────────────────────────
    agent_text = _extract_agent_text(result)

    # ── Step 9: Empty response → EMPTY_RESPONSE termination ──────────
    if not agent_text.strip():
        logger.warning(
            "simulator.agent_empty_response",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            error_class=None,
            error="Agent returned blank response (silent failure)",
        )
        return _build_terminal_dict(AgentErrorSubtype.EMPTY_RESPONSE)

    # ── Step 10: Defense in depth — assert_no_leak (warning only) ────
    # H10 cement: smoke tests (T-10) call assert_no_leak with raise
    # enabled. Inside the bridge we MUST NOT raise — a leaked token
    # should not corrupt the transcript or terminate the simulation
    # (the smoke test owns the policy decision). The structlog warning
    # emitted by ``assert_no_leak`` itself stands as the breadcrumb.
    with contextlib.suppress(AssertionError):
        assert_no_leak(agent_text)

    # ── Step 11: Build agent turn + return transcript-append partial ─
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


# ════════════════════════════════════════════════════════════════════════
# Helpers — text extraction from the agent_app.ainvoke result shape
# ════════════════════════════════════════════════════════════════════════


def _extract_agent_text(result: dict[str, Any]) -> str:
    """Extract the agent's text response from the production graph result.

    The production ``agent_app`` returns a dict with ``messages`` containing
    AIMessage-like objects (or message dicts when serialized). The bridge
    accepts both shapes — paridad with the heuristic in
    ``outbound_orchestrator.py`` and ``chat.py``.

    Args:
        result: Final state dict returned by ``agent_app.ainvoke``.

    Returns:
        The agent's last message content as a string. Empty string if no
        message was produced (caller maps to EMPTY_RESPONSE termination).
    """
    messages = result.get("messages") if isinstance(result, dict) else None
    if not messages:
        return ""
    last_msg = messages[-1]
    # Dict-shape (serialized) or AIMessage-shape (langchain object)
    if isinstance(last_msg, dict):
        content = last_msg.get("content", "")
        return str(content) if content is not None else ""
    # langchain BaseMessage-like — has .content attribute
    content = getattr(last_msg, "content", "")
    return str(content) if content is not None else ""


__all__ = ["agent_bridge"]
