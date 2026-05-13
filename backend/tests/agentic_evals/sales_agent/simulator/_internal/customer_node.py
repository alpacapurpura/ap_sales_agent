"""Customer LLM node — generates next user message based on persona (T-6).

Adapted from ``client_simulator/src/simulator/customer_node.py`` (legacy
preserved byte-equal under ``client_simulator/`` per D6) — re-shaped to:

* consume the Pydantic ``ActorProfile`` + ``SimulationState`` from T-4
* dispatch via ``LLMFactory.get_service().get_client(role=ModelRole.NANO)``
  (shared LiteLLM Proxy — NOT a fresh ``ChatOpenAI`` instance)
* honor the global ``EVAL_SIMULATOR_SEMAPHORE`` (H4)
* terminate gracefully on LLM failure via H7 ``AgentErrorSubtype`` taxonomy

Anti-duplication §0
===================

* Reuses ``LLMFactory.get_service()`` — NO fresh client construction
* Reuses ``langchain_core.messages.{HumanMessage, SystemMessage}`` types
* Customer LLM cost recorded to ``eval_simulator_llm_call`` via the callback
  handler subclass ``EvalSimulatorCallbackHandler`` (T-5) — wired by
  ``run_simulation`` (T-8) at the LangGraph config level via
  ``ctx.langchain_config()``.

LangGraph contract
==================

* Returns a partial state dict — ``{"transcript": [new_turn]}`` or
  ``{"is_finished": True, "error_subtype": "..."}``. NEVER mutates state.
* Reducer ``Annotated[list[ConversationTurn], operator.add]`` (declared on
  ``SimulationState.transcript``) merges the new turn append-only.
* No ``from __future__ import annotations`` — this module is imported by
  the LangGraph runtime when the graph compiles; LangGraph runtime
  introspection requires resolved annotations. Cement matches T-4 + T-5.

Failure modes (graceful degradation per ``tessl__graceful-degradation``
Rule 2):

* LLM call raises ``TimeoutError`` → ``error_subtype='http_error'`` +
  ``is_finished=True``. Story F future may upgrade to ``timeout`` subtype.
* LLM call raises any other ``Exception`` → ``error_subtype='http_error'`` +
  ``is_finished=True``. Defensive — provider transient issues mapped to a
  retriable taxonomy without bubbling to the orchestrator.
* All failures emit ``structlog.warning("simulator.customer_node_error", ...)``.

# voseo-allowed: structlog event_name strings + comments quote dialect injection
# magic comment escape per .claude/rules/spanish-text.md § R25 (2026-05-05)
"""

# NO ``from __future__ import annotations`` — LangGraph runtime introspection
# requires resolved annotations on this module's async node.

from datetime import UTC, datetime
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from luana_core_platform.core.enums import ModelRole
from luana_core_llm.factory import LLMFactory
from tests.agentic_evals.sales_agent.simulator._internal.concurrency import (
    EVAL_SIMULATOR_SEMAPHORE,
)
from tests.agentic_evals.sales_agent.simulator._internal.customer_persona_prompt import (
    build_customer_prompt,
    build_customer_prompt_v2,
)
from tests.agentic_evals.sales_agent.simulator._internal.llm_roles import (
    EVAL_DEFAULT_MODELS,
)
from tests.agentic_evals.sales_agent.simulator.result import ConversationTurn
from tests.agentic_evals.sales_agent.simulator.state import SimulationState

logger = structlog.get_logger()


_LLM_INSTRUCTION_HUMAN_TURN = "Genera tu siguiente mensaje como cliente. Solo el mensaje, sin explicaciones."


async def customer_node(state: SimulationState) -> dict[str, Any]:
    """LangGraph node: generate next customer message.

    Turn 0 short-circuit: emit ``actor_profile.initial_message`` verbatim
    without an LLM call (deterministic opening). The semaphore is NOT
    acquired in this path — the rate-limited resource (LLM provider) is
    untouched.

    Turn N+: invoke the customer LLM via ``LLMFactory`` with the persona
    prompt + transcript history. Wrapped by ``async with
    EVAL_SIMULATOR_SEMAPHORE`` (H4 cap default 10).

    Args:
        state: ``SimulationState`` (Pydantic). The node reads ``actor_profile``,
            ``current_turn``, and ``transcript``; it never mutates ``state``.

    Returns:
        A partial state dict. On success::

            {"transcript": [new_turn]}

        On failure (LLM exception)::

            {"is_finished": True, "error_subtype": "http_error"}
    """
    actor = state.actor_profile

    # Turn 0 — verbatim initial_message, no LLM call, no semaphore acquire
    if state.current_turn == 0:
        new_turn = ConversationTurn(
            turn_number=0,
            role="customer",
            content=actor.initial_message,
            timestamp=datetime.now(tz=UTC),
            metadata={"generated": False},
        )
        return {"transcript": [new_turn]}

    # Build prompt + messages outside the semaphore (cheap CPU ops).
    # T-5 dispatch — V1/V2 routed by ``actor_profile.schema_version``:
    #   ≥ 2 → V2 builder (sub-slot pain/objection rotation per turn)
    #   == 1 → V1 builder (frozen template, byte-equal back-compat for legacy
    #          fixtures + frozen golden v1 — H10 cement Story B preserved)
    if actor.schema_version >= 2:
        system_prompt = build_customer_prompt_v2(actor, current_turn=state.current_turn)
        # Cache TTL informational hint (Anthropic prompt caching slot architecture
        # per 02-design-agentic.md §5). The actual cache wiring rides through the
        # LiteLLM Proxy headers Story B path; this log is purely diagnostic so
        # operators can confirm the V2 dispatch path was taken without scanning
        # the rendered prompt body.
        logger.info(
            "simulator.customer_node_prompt_v2_dispatched",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            schema_version=actor.schema_version,
            persona_kind=actor.persona_kind,
            cache_ttl_slots_1_2="1h",
            cache_ttl_slots_3a_3b="5min",
        )
    else:
        system_prompt = build_customer_prompt(actor)
        logger.info(
            "simulator.customer_node_prompt_v1_dispatched",
            simulation_id=str(state.simulation_id),
            turn=state.current_turn,
            schema_version=actor.schema_version,
            persona_kind=actor.persona_kind,
        )

    history_messages = _build_conversation_messages(state.transcript)
    messages: list[Any] = [
        SystemMessage(content=system_prompt),
        *history_messages,
        HumanMessage(content=_LLM_INSTRUCTION_HUMAN_TURN),
    ]

    # T-5 — extend ``eval_metadata`` with 3 NEW keys for the LLM call only.
    # The state field itself remains the H5 6-key dict (LangGraph node
    # contract — never mutate state; the dict() copy below is the boundary).
    # The 3 NEW keys are forwarded to the EvalSimulatorCallbackHandler via
    # ``config["metadata"]["eval_metadata"]`` and persisted onto every
    # ``eval_simulator_llm_call.eval_metadata`` jsonb row, where they enable
    # downstream cost-by-persona-kind aggregation queries (Story F+ scope).
    extended_eval_metadata: dict[str, Any] = dict(state.eval_metadata)
    extended_eval_metadata["persona_kind"] = actor.persona_kind
    # str() for jsonb compatibility — eval_metadata is dict[str, str|int] in
    # state.py but the Postgres jsonb column is open shape; downstream filters
    # ``WHERE eval_metadata->>'schema_version' = '2'`` expect string values.
    extended_eval_metadata["schema_version"] = str(actor.schema_version)
    # ``metadata.archetype`` is the persona's tenant_archetype tag (set by
    # the YAML loader / fixture). Defaults to '' to keep the column shape
    # uniform across legacy fixtures whose ``metadata`` dict may not declare
    # the key.
    extended_eval_metadata["archetype"] = actor.metadata.get("archetype", "")

    # H4 — wrap ONLY the rate-limited resource (LLM ainvoke).
    async with EVAL_SIMULATOR_SEMAPHORE:
        try:
            llm = LLMFactory.get_service().get_client(
                role=ModelRole.NANO,
                temperature=0.8,
            )
            # ``model_override`` propagates to the LiteLLM Proxy via metadata.
            # ``eval_metadata`` propagates to the EvalSimulatorCallbackHandler
            # so every persisted row carries the H5 invariant 6-key dict +
            # the 3 NEW Story C keys (persona_kind, schema_version, archetype).
            response = await llm.ainvoke(
                messages,
                config={
                    "metadata": {
                        "eval_metadata": extended_eval_metadata,
                        "model_override": EVAL_DEFAULT_MODELS["EVAL_USER_SIMULATOR"],
                    },
                },
            )
            customer_message = (response.content or "").strip()
            if not customer_message:
                # Empty response: terminate via H7 — agent_bridge has its own
                # EMPTY_RESPONSE handling; for the customer LLM we map to
                # http_error to keep the failure-mode taxonomy minimal.
                logger.warning(
                    "simulator.customer_node_empty_response",
                    simulation_id=str(state.simulation_id),
                    turn=state.current_turn,
                )
                return {"is_finished": True, "error_subtype": "http_error"}

            new_turn = ConversationTurn(
                turn_number=state.current_turn,
                role="customer",
                content=customer_message,
                timestamp=datetime.now(tz=UTC),
                metadata={"generated": True},
            )
            return {"transcript": [new_turn]}

        except TimeoutError as exc:
            logger.warning(
                "simulator.customer_node_timeout",
                simulation_id=str(state.simulation_id),
                turn=state.current_turn,
                error_class=type(exc).__name__,
                error=str(exc),
            )
            return {"is_finished": True, "error_subtype": "http_error"}
        except Exception as exc:  # noqa: BLE001 — graceful-degradation Rule 2
            logger.warning(
                "simulator.customer_node_error",
                simulation_id=str(state.simulation_id),
                turn=state.current_turn,
                error_class=type(exc).__name__,
                error=str(exc),
            )
            return {"is_finished": True, "error_subtype": "http_error"}


def _build_conversation_messages(
    transcript: list[ConversationTurn],
) -> list[HumanMessage]:
    """Render the transcript as alternating ``HumanMessage`` entries for the LLM.

    The customer LLM is generating the customer side of the dialog, so both
    the customer's prior turns and the agent's responses are presented as
    HumanMessage with role-prefix tags. Pattern paridad with the legacy
    ``client_simulator/customer_node.py`` (D6 byte-equal preserved upstream).

    Args:
        transcript: Append-only list of ``ConversationTurn`` (frozen).

    Returns:
        A list of ``HumanMessage`` entries to splice between the SystemMessage
        and the final instruction ``HumanMessage``.
    """
    messages: list[HumanMessage] = []
    for turn in transcript:
        prefix = "[Tú dijiste]" if turn.role == "customer" else "[Vendedor]"
        messages.append(HumanMessage(content=f"{prefix}: {turn.content}"))
    return messages


__all__ = ["customer_node"]
