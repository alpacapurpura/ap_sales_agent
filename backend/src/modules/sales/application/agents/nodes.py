from typing import Dict, Any
from src.shared.application.orchestrator.state import AgentState
from src.shared.infrastructure.llm.factory import LLMFactory
from src.modules.sales.application.agents.prompts import (
    SUPERVISOR_PROMPT, QUALIFIER_PROMPT, EXPERT_PROMPT, CLOSER_PROMPT
)
from src.shared.infrastructure.monitoring.tracing import trace_node

@trace_node("sales_supervisor")
def node_sales_supervisor(state: AgentState) -> Dict[str, Any]:
    """
    Orchestrator: Decides which specialist should handle the next turn.
    """
    # Simple heuristic fallback or LLM-based routing
    # For speed/cost, we might use "fast" model here
    
    # If explicit tool/action needed, route there.
    
    intent = state.get("detected_intent", "unknown")
    stage = state.get("current_state", "rapport")
    
    try:
        decision = LLMFactory.get_service().generate_response(
            messages=state["messages"][-3:], # Short context
            system_prompt=SUPERVISOR_PROMPT.format(
                intent=intent,
                lead_score=state.get("lead_score", 0),
                stage=stage
            ),
            model_type="fast",
            temperature=0.0,
            max_output_tokens=10
        )
        decision = decision.strip().lower().replace('"', '')
    except Exception:
        decision = "qualifier" # Default
        
    # Map to valid nodes
    valid_nodes = ["qualifier", "product_expert", "closer", "scheduler"]
    if decision not in valid_nodes:
        # Fallback logic based on stage
        if stage == "closing":
            decision = "closer"
        else:
            decision = "qualifier"
            
    return {"next_node": decision}

@trace_node("qualifier")
def node_qualifier(state: AgentState) -> Dict[str, Any]:
    # In a real implementation, this would pull Qualification Criteria from the Offer Context
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=QUALIFIER_PROMPT.format(
            qualification_criteria="Budget > $2k, B2B Niche", # Placeholder
            history=state["messages"]
        ),
        model_type="smart",
        temperature=0.2
    )
    return {"messages": [{"role": "assistant", "content": response}]}

@trace_node("product_expert")
def node_product_expert(state: AgentState) -> Dict[str, Any]:
    # RAG Retrieval would happen here
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=EXPERT_PROMPT.format(
            context="[Retrieved Context Placeholder]", 
            history=state["messages"]
        ),
        model_type="smart",
        temperature=0.2
    )
    return {"messages": [{"role": "assistant", "content": response}]}

@trace_node("closer")
def node_closer(state: AgentState) -> Dict[str, Any]:
    response = LLMFactory.get_service().generate_response(
        messages=state["messages"],
        system_prompt=CLOSER_PROMPT.format(
            offer_details="High Ticket Mastermind - $5000", # Placeholder
            history=state["messages"]
        ),
        model_type="smart",
        temperature=0.4 # Slightly higher for persuasion
    )
    return {"messages": [{"role": "assistant", "content": response}]}
