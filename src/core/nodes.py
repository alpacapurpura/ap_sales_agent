from typing import List, Dict, Any
from src.core.state import AgentState
from src.services.database import redis_client
from src.core.prompts.base import prompt_loader
from src.services.vector_store import search_knowledge_base
from src.core.llm.factory import LLMFactory
import json

# Helper to handle messages
def get_session_history(user_id: str) -> List[Dict[str, str]]:
    """
    Retrieve history from Redis.
    Returns list of dicts: [{"role": "user", "content": "..."}, ...]
    """
    raw = redis_client.lrange(f"session:{user_id}:history", 0, -1)
    if not raw:
        return []
    
    # Handle backward compatibility if Redis has plain strings
    history = []
    for m in raw:
        try:
            history.append(json.loads(m))
        except json.JSONDecodeError:
            # Fallback for old string messages (assume user or system? let's skip or treat as user)
            history.append({"role": "user", "content": m})
    return history

def save_session_history(user_id: str, role: str, content: str):
    """
    Save message to Redis as JSON.
    """
    msg_obj = {"role": role, "content": content}
    redis_client.rpush(f"session:{user_id}:history", json.dumps(msg_obj))
    redis_client.expire(f"session:{user_id}:history", 21600) # 6 hours

def node_entry_point(state: AgentState):
    """
    Check session validity and initialize if needed.
    Handles merging incoming message with history.
    """
    user_id = state["user_id"]
    
    # 1. Load persistent profile
    profile_raw = redis_client.get(f"session:{user_id}:profile")
    if profile_raw:
        state["user_profile"] = json.loads(profile_raw)
    else:
        state["user_profile"] = {}
        
    # 2. Load History
    history = get_session_history(user_id)
    
    # 3. Handle New Message (from API)
    # The API passes 'messages': [text_string] in the initial state
    input_messages = state.get("messages", [])
    
    if input_messages:
        last_input = input_messages[-1]
        # Check if it's a new string message (not yet in history structure)
        if isinstance(last_input, str):
            # It's a new user message
            new_msg_text = last_input
            save_session_history(user_id, "user", new_msg_text)
            history.append({"role": "user", "content": new_msg_text})
        elif isinstance(last_input, dict):
            # Already structured (maybe re-entry?)
            if last_input not in history:
                save_session_history(user_id, last_input["role"], last_input["content"])
                history.append(last_input)
    
    state["messages"] = history
    
    # Default state if not set
    if not state.get("current_state"):
        state["current_state"] = "S1_Rapport"
        
    return state

def node_guardrails(state: AgentState):
    """
    Safety checks.
    """
    if not state["messages"]:
        return state
        
    last_msg = state["messages"][-1]["content"].lower()
    
    # Simple check example
    if "ignore instructions" in last_msg:
        response = "I cannot do that."
        save_session_history(state["user_id"], "assistant", response)
        return {
            "messages": state["messages"] + [{"role": "assistant", "content": response}], 
            "current_state": state["current_state"]
        }
    return state

def node_router(state: AgentState):
    """
    Route to specific handlers based on keywords.
    """
    if not state["messages"]:
        return state

    last_msg = state["messages"][-1]["content"].lower()
    
    # Medical
    if any(x in last_msg for x in ["ansiedad", "depresión", "embarazo", "médico", "psicólogo"]):
        state["router_outcome"] = "critical_objection"
        state["objection_type"] = "medical_condition"
        return state
        
    # AI Identity
    if any(x in last_msg for x in ["eres un robot", "eres ia", "eres ai", "humano"]):
        state["router_outcome"] = "critical_objection"
        state["objection_type"] = "is_ai"
        return state

    # Tech Issue
    if any(x in last_msg for x in ["error", "no carga", "fallo", "página"]):
        state["router_outcome"] = "critical_objection"
        state["objection_type"] = "tech_issue"
        return state
    
    return state

def node_intent_classifier(state: AgentState):
    """
    Determine the intent of the user.
    """
    if not state["messages"]:
        return state

    last_msg = state["messages"][-1]["content"].lower()
    
    intent = "general"
    if "precio" in last_msg or "cuanto" in last_msg:
        intent = "pricing"
    elif "no" in last_msg and len(last_msg) < 10:
        intent = "objection"
        
    state["last_intent"] = intent
    return state

def node_state_manager(state: AgentState):
    """
    Transition logic S1 -> S6 based on intent and history.
    """
    current = state["current_state"]
    intent = state["last_intent"]
    
    # Example transition logic (simplified)
    if current == "S1_Rapport" and intent == "general":
        pass
        
    return state

def node_response_generation(state: AgentState):
    """
    Generate the response using LLM + RAG.
    """
    router_outcome = state.get("router_outcome", "sales_flow")
    user_id = state["user_id"]
    
    # 1. Critical Objection (Deterministic Template)
    if router_outcome == "critical_objection":
        objection_type = state.get("objection_type", "general")
        system_prompt = prompt_loader.render(
            "objection_handling.j2",
            objection_type=objection_type,
            user_profile=state["user_profile"]
        )
        
        # In this case, the template IS the response (mostly), or we use LLM to smooth it.
        # For strict control, we can treat the rendered template as the response 
        # or use a very strict LLM call.
        # Let's use the LLM to deliver it naturally.
        
        response_text = LLMFactory.get_service().generate_response(
            messages=state["messages"],
            system_prompt=f"You are a helpful assistant. Deliver this message exactly: {system_prompt}"
        )
        
        save_session_history(user_id, "assistant", response_text)
        return {"messages": state["messages"] + [{"role": "assistant", "content": response_text}]}

    # 2. RAG Query
    elif router_outcome == "rag_query":
        last_user_msg = state["messages"][-1]["content"]
        
        context_rag = search_knowledge_base(
            query_text=last_user_msg,
            client_id="visionarias", 
            limit=3
        )
        
        if not context_rag:
            context_rag = "No se encontró información específica en la base de conocimientos."
            
        system_prompt = f"Use the following context to answer the user's question:\n{context_rag}"
        
        response_text = LLMFactory.get_service().generate_response(
            messages=state["messages"],
            system_prompt=system_prompt
        )
        
        save_session_history(user_id, "assistant", response_text)
        return {"messages": state["messages"] + [{"role": "assistant", "content": response_text}]}

    # 3. Sales Flow (Standard S1-S6)
    else:
        context_rag = "" # Can inject if needed
        
        system_prompt = prompt_loader.render(
            "sales_system.j2",
            current_state=state["current_state"],
            user_profile=state["user_profile"],
            context_rag=context_rag
        )
        
        response_text = LLMFactory.get_service().generate_response(
            messages=state["messages"],
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        save_session_history(user_id, "assistant", response_text)
        return {"messages": state["messages"] + [{"role": "assistant", "content": response_text}]}

def node_financial_enforcer(state: AgentState):
    """
    Financial Enforcer (Deterministic).
    Overwrites LLM hallucinations regarding price/dates.
    """
    if not state["messages"]:
        return state
        
    last_msg_obj = state["messages"][-1]
    last_response = last_msg_obj["content"]
    
    # --- HARD DATA ---
    PRECIO_OFERTA = "S/. 4,444"
    PRECIO_REGULAR = "S/. 5,925"
    CUOTA_MENSUAL = "S/. 740"
    FECHA_INICIO = "10 de Febrero 2026"
    GARANTIA_DIAS = "7 días"
    
    modified = False
    
    # 1. Price Correction
    if "S/." in last_response or "soles" in last_response.lower():
        if PRECIO_OFERTA not in last_response and PRECIO_REGULAR not in last_response:
            last_response += f"\n\n(Nota: El precio oficial de preventa es {PRECIO_OFERTA} o 6 cuotas de {CUOTA_MENSUAL} sin intereses)."
            modified = True

    # 2. Date Correction
    if "febrero" in last_response.lower() and FECHA_INICIO not in last_response:
        last_response = last_response.replace("febrero", FECHA_INICIO)
        modified = True
        
    # 3. Warranty Correction
    if "garantía" in last_response.lower() and GARANTIA_DIAS not in last_response:
         last_response += f"\n(Recuerda que nuestra garantía es de {GARANTIA_DIAS} de satisfacción total)."
         modified = True

    if modified:
        # Update the last message in state (and ideally Redis, but Redis is append-only usually)
        # We should update Redis for consistency if we want history to be accurate
        # But for now, we just update the state response that goes to the user.
        new_messages = state["messages"][:-1] + [{"role": "assistant", "content": last_response}]
        
        # Optional: Update Redis last message (pop and push)
        # redis_client.rpop(...)
        # save_session_history(...)
        
        return {"messages": new_messages}
    
    return state
