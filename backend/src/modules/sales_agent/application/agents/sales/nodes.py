from typing import Dict, Any
from src.modules.sales_agent.application.orchestrator.state import AgentState
from src.shared.infrastructure.llm.factory import LLMFactory
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.modules.sales_agent.infrastructure.monitoring.tracing import trace_node


def _build_system_prompt(state: AgentState, skill_prompt: str) -> str:
    """Prepend agent_identity (the tenant's 'CLAUDE.md') to any skill prompt."""
    identity = state.get("agent_identity", "")
    if identity:
        return f"{identity}\n\n---\n\n{skill_prompt}"
    return skill_prompt


@trace_node("sales_supervisor")
def node_sales_supervisor(state: AgentState) -> Dict[str, Any]:
    """
    Orchestrator: Decides which specialist should handle the next turn.
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
        )
        decision = LLMFactory.get_service().generate_response(
            messages=state["messages"][-3:],
            system_prompt=system_prompt,
            model_type="fast",
            temperature=0.0,
            max_output_tokens=10,
            metadata={"prompt_template": "supervisor_routing"},
        )
        decision = decision.strip().lower().replace('"', '')
    except Exception:
        decision = "qualifier"

    valid_nodes = ["qualifier", "product_expert", "closer", "scheduler"]
    if decision not in valid_nodes:
        decision = "closer" if stage == "closing" else "qualifier"

    return {"next_node": decision}


@trace_node("qualifier")
def node_qualifier(state: AgentState) -> Dict[str, Any]:
    skill_prompt = prompt_loader.render("specialist_qualifier")
    system_prompt = _build_system_prompt(state, skill_prompt)
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=system_prompt,
        model_type="smart",
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
        model_type="smart",
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
        model_type="smart",
        temperature=0.4,
        metadata={"prompt_template": "agent_identity + specialist_closer"},
    )
    return {"messages": [{"role": "assistant", "content": response}]}
