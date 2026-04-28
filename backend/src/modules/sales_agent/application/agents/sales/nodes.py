"""Nodes application module."""

import json
import re
from typing import Any

from src.modules.sales_agent.application.orchestrator.state import AgentState
from src.modules.sales_agent.application.prompts.compose import (
    SpecialistRole,
    build_specialist_system_prompt,
)
from src.modules.sales_agent.domain.model_tier import SPECIALIST_TO_ROLE
from src.modules.sales_agent.domain.tuning import (
    BUYING_SIGNAL_WEIGHT,
    FOLLOW_UP_CADENCES,
    LEAD_SCORE_MAX,
    MAX_INTERNAL_TURNS,
    QUALIFICATION_FIELD_WEIGHT,
    STAGE_CLOSING_SCORE,
    STAGE_CLOSING_SIGNALS,
    STAGE_DISCOVERY_QA,
    STAGE_PRESENTATION_QA,
    SUPERVISOR_MESSAGE_WINDOW,
)
from src.modules.sales_agent.infrastructure.monitoring.tracing import trace_node
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.shared.infrastructure.llm.factory import LLMFactory

# ---------------------------------------------------------------------------
# Helpers (shared across nodes)
# ---------------------------------------------------------------------------


def _extract_json_block(text: str, block_name: str) -> dict | None:
    """Extract [BLOCK_NAME: {...}] from text."""
    pattern = rf"\[{block_name}:\s*(\{{.*?\}})\]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None


def _strip_blocks(text: str) -> str:
    """Remove all structured [BLOCK: {...}] from text."""
    cleaned = re.sub(
        r"\[(?:QUALIFICATION_DATA|SIGNALS|TOOL_REQUEST):\s*\{.*?\}\]",
        "",
        text,
        flags=re.DOTALL,
    )
    return cleaned.strip()


def _determine_stage(state: dict, updates: dict) -> str:
    """Determine conversation stage based on accumulated data."""
    qa = updates.get("qualification_answers") or state.get("qualification_answers") or {}
    signals = updates.get("buying_signals") or state.get("buying_signals") or []
    score = updates.get("lead_score", state.get("lead_score", 0))
    turn = state.get("turn_count", 0)

    if score >= STAGE_CLOSING_SCORE and len(signals) >= STAGE_CLOSING_SIGNALS:
        return "closing"
    if len(qa) >= STAGE_PRESENTATION_QA:
        return "presentation"
    if len(qa) >= STAGE_DISCOVERY_QA:
        return "discovery"
    if turn == 0:
        return "rapport"
    return state.get("current_state", "rapport")


# ---------------------------------------------------------------------------
# Supervisor
# ---------------------------------------------------------------------------


@trace_node("sales_supervisor")
def node_sales_supervisor(state: AgentState) -> dict[str, Any]:
    """Orchestrator: Decides which specialist should handle the next turn.

    Uses accumulated signals and context for smarter routing.
    """
    intent = state.get("detected_intent", "unknown")
    stage = state.get("current_state", "rapport")

    try:
        system_prompt = prompt_loader.render(
            "supervisor_routing",
            intent=intent,
            lead_score=state.get("lead_score", 0),
            stage=stage,
            lead_data=state.get("lead_data"),
            user_profile=state.get("user_profile"),
            buying_signals_count=len(state.get("buying_signals") or []),
            objection_count=len(state.get("objection_history") or []),
            qualification_completeness=len(state.get("qualification_answers") or {}),
            last_specialist=state.get("last_specialist"),
            turn_count=state.get("turn_count", 0),
            consecutive_questions=state.get("consecutive_questions", 0),
            session_gap_hours=state.get("session_gap_hours"),
        )
        decision = LLMFactory.get_service().generate_response(
            messages=state["messages"][-SUPERVISOR_MESSAGE_WINDOW:],
            system_prompt=system_prompt,
            model_type=SPECIALIST_TO_ROLE["supervisor"],
            temperature=0.0,
            max_output_tokens=10,
            metadata={"prompt_template": "supervisor_routing"},
        )
        decision = decision.strip().lower().replace('"', "")
    except Exception:  # noqa: BLE001 — agent resilience
        decision = "qualifier"

    # Map scheduler → closer for backward compat
    if decision == "scheduler":
        decision = "closer"

    valid_nodes = ["qualifier", "product_expert", "closer", "escalate", "respond"]
    if decision not in valid_nodes:
        decision = "closer" if stage == "closing" else "qualifier"

    return {"next_node": decision}


# ---------------------------------------------------------------------------
# Specialists
# ---------------------------------------------------------------------------


@trace_node("qualifier")
def node_qualifier(state: AgentState) -> dict[str, Any]:
    """Node qualifier."""
    system_prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type=SPECIALIST_TO_ROLE["qualifier"],
        temperature=0.2,
        metadata={"prompt_template": "compose:specialist_qualifier"},
    )
    return {"messages": [{"role": "assistant", "content": response}]}


@trace_node("product_expert")
def node_product_expert(state: AgentState) -> dict[str, Any]:
    """Node product expert."""
    system_prompt = build_specialist_system_prompt(state, SpecialistRole.PRODUCT_EXPERT)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type=SPECIALIST_TO_ROLE["product_expert"],
        temperature=0.2,
        metadata={"prompt_template": "compose:specialist_product_expert"},
    )
    return {"messages": [{"role": "assistant", "content": response}]}


@trace_node("closer")
def node_closer(state: AgentState) -> dict[str, Any]:
    """Node closer.

    Routes to ``ModelRole.AGENT`` (Kimi K2.6 by default via
    ``AI_PROVIDER_AGENT=kimi``) for long-form objection handling. The
    higher temperature (0.4) is requested by the closer for creativity;
    Kimi clamps it to its server-required 0.6 in
    ``KimiService._get_chat_model`` when ``AI_MODEL_AGENT`` is a K2 SKU.
    """
    system_prompt = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type=SPECIALIST_TO_ROLE["closer"],
        temperature=0.4,
        metadata={"prompt_template": "compose:specialist_closer"},
    )
    return {"messages": [{"role": "assistant", "content": response}]}


# ---------------------------------------------------------------------------
# Signal Accumulator (post-processing hub)
# ---------------------------------------------------------------------------


def _accumulate_qualification(
    state: AgentState,
    qual_data: dict | None,
    updates: dict,
) -> None:
    """Merge qualification data into updates."""
    if qual_data:
        current_qa = dict(state.get("qualification_answers") or {})
        current_qa.update(qual_data)
        updates["qualification_answers"] = current_qa


def _accumulate_signals(state: AgentState, signals: dict | None, updates: dict) -> None:
    """Merge buying signals and objections into updates."""
    if not signals:
        return
    current_signals = list(state.get("buying_signals") or [])
    turn = state.get("turn_count", 0)
    current_signals.extend({"type": sig, "turn": turn} for sig in signals.get("buying", []))
    updates["buying_signals"] = current_signals

    current_obj = list(state.get("objection_history") or [])
    current_obj.extend({"type": obj, "turn": turn, "resolved": False} for obj in signals.get("objections", []))
    updates["objection_history"] = current_obj


def _compute_lead_score(
    state: AgentState,
    qual_data: dict | None,
    signals: dict | None,
) -> int:
    """Compute updated lead score based on qualification data and signals."""
    score = state.get("lead_score", 0)
    if qual_data:
        score += QUALIFICATION_FIELD_WEIGHT * len(qual_data)
    if signals and signals.get("buying"):
        score += BUYING_SIGNAL_WEIGHT * len(signals["buying"])
    return min(score, LEAD_SCORE_MAX)


def _build_follow_up_cadence(state: AgentState, updates: dict) -> dict | None:
    """Build follow-up cadence dict when transitioning to closing stage."""
    prev_stage = state.get("current_state")
    new_stage = updates.get("current_state", prev_stage)
    if new_stage != "closing" or prev_stage == "closing" or state.get("follow_up_cadence"):
        return None

    product = state.get("active_product") or {}
    price = product.get("price") or 0
    try:
        price = float(price)
    except (ValueError, TypeError):
        price = 0

    tier = "high" if price > 500 else ("mid" if price > 100 else "low")

    from datetime import datetime, timezone

    return {
        **FOLLOW_UP_CADENCES.get(tier, FOLLOW_UP_CADENCES["mid"]),
        "tier": tier,
        "follow_ups_sent": 0,
        "last_follow_up_at": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


def _decide_route(updates: dict, tool_req: dict | None) -> None:
    """Set next_node and pending tool in updates based on routing logic."""
    if tool_req:
        updates["next_node"] = "tool_executor"
        updates["_pending_tool"] = tool_req
    elif updates.get("internal_turn", 0) >= MAX_INTERNAL_TURNS:
        updates["next_node"] = "respond"  # Force output after 3 internal loops
    else:
        updates["next_node"] = "respond"  # Default: send to user


@trace_node("signal_accumulator")
def node_signal_accumulator(state: AgentState) -> dict[str, Any]:
    """Post-processes specialist output: extracts structured blocks, updates scores, strips blocks."""
    last_msg = state["messages"][-1]["content"] if state["messages"] else ""
    updates: dict[str, Any] = {}

    # Parse structured blocks from specialist output
    qual_data = _extract_json_block(last_msg, "QUALIFICATION_DATA")
    signals = _extract_json_block(last_msg, "SIGNALS")
    tool_req = _extract_json_block(last_msg, "TOOL_REQUEST")

    # Accumulate structured data
    _accumulate_qualification(state, qual_data, updates)
    _accumulate_signals(state, signals, updates)
    updates["lead_score"] = _compute_lead_score(state, qual_data, signals)

    # Stage transition + counters
    updates["current_state"] = _determine_stage(state, updates)
    updates["turn_count"] = (state.get("turn_count") or 0) + 1
    updates["internal_turn"] = (state.get("internal_turn") or 0) + 1

    # Track consecutive questions (Fase 3: fatigue detection)
    current_next = state.get("next_node")
    updates["consecutive_questions"] = (
        (state.get("consecutive_questions") or 0) + 1 if current_next == "qualifier" else 0
    )

    # Initialize follow-up cadence when transitioning to closing (Fase 4)
    cadence = _build_follow_up_cadence(state, updates)
    if cadence is not None:
        updates["follow_up_cadence"] = cadence

    # Clean structured blocks from message for user output
    clean_text = _strip_blocks(last_msg)
    if clean_text != last_msg:
        updates["messages"] = [{"role": "assistant", "content": clean_text}]

    # Route decision
    _decide_route(updates, tool_req)

    return updates


# ---------------------------------------------------------------------------
# Escalation (human handoff)
# ---------------------------------------------------------------------------


@trace_node("escalation")
def node_escalation(state: AgentState) -> dict[str, Any]:
    """Send empathetic handoff message when conversation needs human intervention."""
    return {
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "Entiendo perfectamente. Voy a conectarte con alguien de nuestro "
                    "equipo que puede ayudarte mejor con esto. Dame un momento."
                ),
            },
        ],
        "next_node": "respond",
    }


# ---------------------------------------------------------------------------
# Tool Executor
# ---------------------------------------------------------------------------


@trace_node("tool_executor")
def node_tool_executor(state: AgentState) -> dict[str, Any]:
    """Execute tools requested by specialists via [TOOL_REQUEST: {...}] blocks.

    Per-turn dedup guard (S1, mirror of copilot anti-loop): the
    orchestrator seeds ``state['_tool_dedup_tracker']`` with a fresh
    :class:`ToolCallDedupTracker` at the start of every turn. Before
    dispatching the tool we ``observe`` the call. If the tracker
    returns ``WARN`` we wrap the result with an anti-loop directive so
    the LLM sees the rail next turn. If it raises ``ToolCallLoopError``
    we end the loop with a tool-error message and the supervisor will
    route to ``respond`` next.

    After execution the graph edge routes back to supervisor.
    """
    from src.modules.sales_agent.application.orchestrator.tool_call_dedup import (
        DedupVerdict,
        ToolCallLoopError,
        augment_tool_message_for_warn,
    )

    pending = state.get("_pending_tool")
    if not pending:
        return {"next_node": "respond"}

    tool_name = pending.get("tool", "")
    tool_args = pending.get("args") or {}

    from src.modules.sales_agent.application.agents.sales.tools import TOOL_REGISTRY

    tool_fn = TOOL_REGISTRY.get(tool_name)
    if not tool_fn:
        return {
            "messages": [
                {
                    "role": "tool",
                    "content": json.dumps(
                        {
                            "status": "error",
                            "message": f"Tool '{tool_name}' not found.",
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "_pending_tool": None,
        }

    tracker = state.get("_tool_dedup_tracker")
    verdict = DedupVerdict.OK
    if tracker is not None:
        try:
            verdict = tracker.observe(tool_name, tool_args)
        except ToolCallLoopError as exc:
            return {
                "messages": [
                    {
                        "role": "tool",
                        "content": json.dumps(
                            {
                                "status": "error",
                                "message": str(exc),
                                "tool_name": exc.tool_name,
                                "repeat_count": exc.repeat_count,
                                "args_hash": exc.args_hash,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                "_pending_tool": None,
                "next_node": "respond",
            }

    try:
        result = tool_fn(state, db=state.get("_db"))
        result_text = json.dumps(result, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001 — agent resilience
        result_text = json.dumps(
            {"status": "error", "message": str(e)},
            ensure_ascii=False,
        )

    if verdict == DedupVerdict.WARN:
        result_text = augment_tool_message_for_warn(
            tool_name=tool_name,
            tool_args=tool_args,
            original_content=result_text,
        )

    return {
        "messages": [{"role": "tool", "content": result_text}],
        "_pending_tool": None,
    }
