import json
import re
from typing import Dict, Any

from src.core.enums import ModelRole
from src.modules.sales_agent.application.orchestrator.state import AgentState
from src.shared.infrastructure.llm.factory import LLMFactory
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.modules.sales_agent.infrastructure.monitoring.tracing import trace_node
from src.modules.sales_agent.domain.tuning import (
    BUYING_SIGNAL_WEIGHT,
    QUALIFICATION_FIELD_WEIGHT,
    LEAD_SCORE_MAX,
    MAX_INTERNAL_TURNS,
    STAGE_CLOSING_SCORE,
    STAGE_CLOSING_SIGNALS,
    STAGE_PRESENTATION_QA,
    STAGE_DISCOVERY_QA,
    SUPERVISOR_MESSAGE_WINDOW,
)


# ---------------------------------------------------------------------------
# Helpers (shared across nodes)
# ---------------------------------------------------------------------------

def _build_system_prompt(state: AgentState, skill_prompt: str) -> str:
    """Prepend agent_identity (the tenant's 'CLAUDE.md') to any skill prompt."""
    identity = state.get("agent_identity", "")
    if identity:
        return f"{identity}\n\n---\n\n{skill_prompt}"
    return skill_prompt


def _extract_json_block(text: str, block_name: str) -> dict | None:
    """Extract [BLOCK_NAME: {...}] from text."""
    pattern = rf'\[{block_name}:\s*(\{{.*?\}})\]'
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
        r'\[(?:QUALIFICATION_DATA|SIGNALS|TOOL_REQUEST):\s*\{.*?\}\]',
        '',
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
    elif len(qa) >= STAGE_PRESENTATION_QA:
        return "presentation"
    elif len(qa) >= STAGE_DISCOVERY_QA:
        return "discovery"
    elif turn == 0:
        return "rapport"
    else:
        return state.get("current_state", "rapport")


# ---------------------------------------------------------------------------
# Supervisor
# ---------------------------------------------------------------------------

@trace_node("sales_supervisor")
def node_sales_supervisor(state: AgentState) -> Dict[str, Any]:
    """
    Orchestrator: Decides which specialist should handle the next turn.
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
        )
        decision = LLMFactory.get_service().generate_response(
            messages=state["messages"][-SUPERVISOR_MESSAGE_WINDOW:],
            system_prompt=system_prompt,
            model_type=ModelRole.FAST,
            temperature=0.0,
            max_output_tokens=10,
            metadata={"prompt_template": "supervisor_routing"},
        )
        decision = decision.strip().lower().replace('"', '')
    except Exception:
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
def node_qualifier(state: AgentState) -> Dict[str, Any]:
    skill_prompt = prompt_loader.render("specialist_qualifier")
    system_prompt = _build_system_prompt(state, skill_prompt)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type=ModelRole.REASONING,
        temperature=0.2,
        metadata={"prompt_template": "agent_identity + specialist_qualifier"},
    )
    return {"messages": [{"role": "assistant", "content": response}]}


@trace_node("product_expert")
def node_product_expert(state: AgentState) -> Dict[str, Any]:
    skill_prompt = prompt_loader.render(
        "specialist_product_expert",
        context_rag=state.get("context_rag"),
    )
    system_prompt = _build_system_prompt(state, skill_prompt)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type=ModelRole.REASONING,
        temperature=0.2,
        metadata={"prompt_template": "agent_identity + specialist_product_expert"},
    )
    return {"messages": [{"role": "assistant", "content": response}]}


@trace_node("closer")
def node_closer(state: AgentState) -> Dict[str, Any]:
    skill_prompt = prompt_loader.render("specialist_closer")
    system_prompt = _build_system_prompt(state, skill_prompt)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type=ModelRole.REASONING,
        temperature=0.4,
        metadata={"prompt_template": "agent_identity + specialist_closer"},
    )
    return {"messages": [{"role": "assistant", "content": response}]}


# ---------------------------------------------------------------------------
# Signal Accumulator (post-processing hub)
# ---------------------------------------------------------------------------

@trace_node("signal_accumulator")
def node_signal_accumulator(state: AgentState) -> Dict[str, Any]:
    """Post-processes specialist output: extracts structured blocks, updates scores, strips blocks."""
    last_msg = state["messages"][-1]["content"] if state["messages"] else ""
    updates: Dict[str, Any] = {}

    # Parse structured blocks from specialist output
    qual_data = _extract_json_block(last_msg, "QUALIFICATION_DATA")
    signals = _extract_json_block(last_msg, "SIGNALS")
    tool_req = _extract_json_block(last_msg, "TOOL_REQUEST")

    # Update qualification answers
    if qual_data:
        current_qa = dict(state.get("qualification_answers") or {})
        current_qa.update(qual_data)
        updates["qualification_answers"] = current_qa

    # Accumulate buying signals
    current_signals = list(state.get("buying_signals") or [])
    if signals:
        for sig in signals.get("buying", []):
            current_signals.append({"type": sig, "turn": state.get("turn_count", 0)})
        updates["buying_signals"] = current_signals

        # Update objection history
        current_obj = list(state.get("objection_history") or [])
        for obj in signals.get("objections", []):
            current_obj.append({"type": obj, "turn": state.get("turn_count", 0), "resolved": False})
        updates["objection_history"] = current_obj

    # Update lead score
    score = state.get("lead_score", 0)
    if qual_data:
        score += QUALIFICATION_FIELD_WEIGHT * len(qual_data)
    if signals and signals.get("buying"):
        score += BUYING_SIGNAL_WEIGHT * len(signals["buying"])
    updates["lead_score"] = min(score, LEAD_SCORE_MAX)

    # Stage transition logic
    updates["current_state"] = _determine_stage(state, updates)
    updates["turn_count"] = (state.get("turn_count") or 0) + 1
    updates["internal_turn"] = (state.get("internal_turn") or 0) + 1

    # Clean structured blocks from message for user output
    clean_text = _strip_blocks(last_msg)
    if clean_text != last_msg:
        updates["messages"] = [{"role": "assistant", "content": clean_text}]

    # Route decision
    if tool_req:
        updates["next_node"] = "tool_executor"
        updates["_pending_tool"] = tool_req
    elif updates.get("internal_turn", 0) >= MAX_INTERNAL_TURNS:
        updates["next_node"] = "respond"  # Force output after 3 internal loops
    else:
        updates["next_node"] = "respond"  # Default: send to user

    return updates


# ---------------------------------------------------------------------------
# Escalation (human handoff)
# ---------------------------------------------------------------------------

@trace_node("escalation")
def node_escalation(state: AgentState) -> Dict[str, Any]:
    """Sends empathetic handoff message when conversation needs human intervention."""
    return {
        "messages": [{
            "role": "assistant",
            "content": (
                "Entiendo perfectamente. Voy a conectarte con alguien de nuestro "
                "equipo que puede ayudarte mejor con esto. Dame un momento."
            ),
        }],
        "next_node": "respond",
    }


# ---------------------------------------------------------------------------
# Tool Executor
# ---------------------------------------------------------------------------

@trace_node("tool_executor")
def node_tool_executor(state: AgentState) -> Dict[str, Any]:
    """Executes tools requested by specialists via [TOOL_REQUEST: {...}] blocks.

    After execution the graph edge routes back to supervisor, which will
    see the tool result message and decide the next specialist.
    """
    pending = state.get("_pending_tool")
    if not pending:
        return {"next_node": "respond"}

    tool_name = pending.get("tool", "")

    from src.modules.sales_agent.application.agents.sales.tools import TOOL_REGISTRY

    tool_fn = TOOL_REGISTRY.get(tool_name)
    if not tool_fn:
        return {
            "messages": [
                {
                    "role": "tool",
                    "content": json.dumps(
                        {"status": "error", "message": f"Tool '{tool_name}' not found."},
                        ensure_ascii=False,
                    ),
                }
            ],
            "_pending_tool": None,
        }

    try:
        result = tool_fn(state, db=state.get("_db"))
        result_text = json.dumps(result, ensure_ascii=False)
    except Exception as e:
        result_text = json.dumps(
            {"status": "error", "message": str(e)}, ensure_ascii=False
        )

    return {
        "messages": [{"role": "tool", "content": result_text}],
        "_pending_tool": None,
    }
