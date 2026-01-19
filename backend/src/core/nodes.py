from typing import List, Dict, Any
from src.core.state import AgentState
from src.core.schema import FunnelStage, UserProfile
# from src.services.database import redis_client # Removed to save RAM
from src.core.prompts.base import prompt_loader
from src.services.vector_store import search_knowledge_base
from src.core.llm.factory import LLMFactory
from src.core.content.scripts import SCRIPTS_REGISTRY, get_script
from src.core.tracing import trace_node
from src.services.semantic_router import SemanticRouter
import json
import re

# Helper to handle messages - REMOVED (Postgres is Source of Truth)
# def get_session_history(user_id: str) -> List[Dict[str, str]]: ...
# def save_session_history(user_id: str, role: str, content: str): ...

@trace_node("entry")
def node_entry_point(state: AgentState):
    """
    Check session validity and initialize if needed.
    Now lighter: History is injected by Routes (Postgres).
    """
    # History already loaded in state["messages"] by Routes
    
    # Default state if not set
    if not state.get("current_state"):
        state["current_state"] = FunnelStage.RAPPORT.value
        
    return state

@trace_node("router")
def node_router(state: AgentState):
    """
    Route to specific handlers based on Semantic Intent (FastEmbed).
    Also handles safety guardrails (Regex) as the first step.
    """
    if not state["messages"]:
        return state

    last_msg = state["messages"][-1]["content"]
    
    # 0. Safety Guardrails (Regex)
    # Check for jailbreaks or unsafe content before semantic routing
    injection_patterns = [
        r"ignore.*instructions", r"olvida.*instrucciones", r"actu[aá].*como",
        r"system override", r"dan mode", r"developer mode",
        r"escri[b|v]e.*poema", r"(tu|your).*(new|nuevo).*(role|rol)",
        r"simul(a|ate)", r"(repeat|repite).*(above|arriba|anterior|system|prompt)",
        r"jailbreak", r"unfiltered", r"base64", r"always.*say.*yes"
    ]
    
    last_msg_lower = last_msg.lower()
    for pattern in injection_patterns:
        if re.search(pattern, last_msg_lower):
            state["router_outcome"] = "handled_safety"
            state["objection_type"] = "safety_violation" # Optional context
            return state

    # 1. Semantic Intent Detection (Local, Fast)
    intent, score = SemanticRouter.detect_intent(last_msg, threshold=0.82)
    
    if intent:
        # A. FAQs -> Direct Response (Skip LLM)
        if intent.startswith("faq_") or intent == "disqualification_no_business":
            state["router_outcome"] = "direct_response"
            state["objection_type"] = intent # Store intent to fetch answer later
            return state
            
        # B. Objections -> Critical Handling (Scripted LLM)
        if intent.startswith("objection_"):
            state["router_outcome"] = "critical_objection"
            state["objection_type"] = intent
            return state
            
        # C. Funnel States -> Pass to Manager (Cognitive)
        if intent.startswith("state_pain_"):
            # We can pass this extracted info to the manager via state if needed
            # For now, just flow to sales, Manager will see the message anyway.
            pass
            
    # Default: Normal Sales Flow
    state["router_outcome"] = "sales_flow"
    return state

@trace_node("manager")
def node_state_manager(state: AgentState):
    """
    Cognitive Brain: Phase A, B, C.
    Decides State Transitions and Strategy.
    """
    
    last_msg = state["messages"][-1]["content"]
    
    # 1. Render Cognitive Prompt
    reasoning_prompt = prompt_loader.render(
        "state_transition.j2",
        current_state=state["current_state"],
        user_profile=state["user_profile"],
        history=state["messages"][:-1],
        router_outcome=state["router_outcome"],
        objection_type=state["objection_type"]
        #last_user_message=last_msg
    )
    
    # 2. Call LLM for Decision
    try:
        # Using a simple generation call. In a real scenario, enforce JSON output.
        # Use SMART model for reasoning (CoT)
        decision_raw = LLMFactory.get_service().generate_response(
            messages=[{"role": "user", "content": last_msg}], 
            system_prompt=reasoning_prompt,
            model_type="smart",
            temperature=0.2,
            max_output_tokens=4000, # Reduced to fit model limit (4096)
            top_p=0.9,
            presence_penalty=0.4,
            frequency_penalty=0.3
        )
        
        # --- PARSE CHAIN OF THOUGHT (XML + JSON) ---
        # 1. Extract Thought Process
        reasoning_match = re.search(r"<thought_process>(.*?)</thought_process>", decision_raw, re.DOTALL)
        if reasoning_match:
            state["latest_reasoning"] = reasoning_match.group(1).strip()
        
        # 2. Extract JSON (Look for code block or just regex for {})
        json_match = re.search(r"```json(.*?)```", decision_raw, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Fallback: Find first { and last }
            start = decision_raw.find("{")
            end = decision_raw.rfind("}")
            if start != -1 and end != -1:
                json_str = decision_raw[start:end+1]
            else:
                json_str = "{}" # Failed to parse

        try:
            decision = json.loads(json_str)
        except json.JSONDecodeError:
            print(f"JSON Parse Error in Manager. Raw: {decision_raw}")
            decision = {}
        
        # 3. Update State
        next_state = decision.get("next_state", state["current_state"])
        extracted_info = decision.get("extracted_info", {})
        
        # Update Profile with new info
        if extracted_info:
            current_profile_data = state.get("user_profile", {})
            # Ensure it's a dict
            if not isinstance(current_profile_data, dict):
                 # Handle Pydantic model if passed directly
                 current_profile_data = current_profile_data.model_dump() if hasattr(current_profile_data, 'model_dump') else dict(current_profile_data)
            
            # Update only non-null values
            for k, v in extracted_info.items():
                if v is not None:
                    current_profile_data[k] = v
            
            # Re-validate with Pydantic (Schema enforces types and ignores extras)
            try:
                validated_profile = UserProfile(**current_profile_data)
                state["user_profile"] = validated_profile.model_dump()
            except Exception as e:
                print(f"Profile Validation Warning: {e}")
                # Fallback: keep partial data even if invalid against schema to avoid data loss
                state["user_profile"] = current_profile_data
            
        # Update Flow State
        state["current_state"] = next_state
        state["active_strategy"] = decision.get("strategy", "Standard")

        # Override Router Outcome/Intent if Manager detects a mismatch
        if decision.get("router_outcome"):
            state["router_outcome"] = decision["router_outcome"]
        
        if decision.get("detected_intent"):
            state["objection_type"] = decision["detected_intent"]

        # Check for Downsell/Exit
        # TODO: Review if we need to handle this or another exit states
        if next_state == FunnelStage.DOWNSELL_EXIT.value:
             state["disqualification_reason"] = decision.get("reason", "User opted out")

        # --- EPISODIC MEMORY GENERATION ---
        # Trigger summary if state changed OR every 5 turns to keep context fresh
        # This acts as the "End of Episode" memory consolidation
        msgs = state.get("messages", [])
        should_summarize = (next_state != state.get("current_state")) or (len(msgs) > 0 and len(msgs) % 5 == 0)
                
        if should_summarize:
            try:
                summary_prompt = prompt_loader.render(
                    "summary_generator.j2",
                    messages=msgs,
                    user_profile=state["user_profile"]
                )
                # Use a cheaper/faster call if possible (using same factory for now)
                summary_text = LLMFactory.get_service().generate_response(
                    messages=[],
                    system_prompt=summary_prompt,
                    model_type="fast",
                    temperature=0.3,
                    max_output_tokens=150,
                    top_p=0.95,
                    presence_penalty=0.0,
                    frequency_penalty=0.0
                )
                
                # Update Profile in State
                current_profile = state.get("user_profile", {})
                current_profile["last_session_summary"] = summary_text.strip()
                state["user_profile"] = current_profile
                
                # Note: The actual DB persist happens in routes.py via repo.persist_agent_state
                # so updating state["user_profile"] here is sufficient.
                
            except Exception as e:
                print(f"Summary Generation Error: {e}")
                # Non-critical failure, continue flow
             
    except Exception as e:
        print(f"State Manager Error: {e}")
        # Fallback: Stay in current state
        pass
        
    return state

@trace_node("response_generation")
def node_response_generation(state: AgentState):
    """
    Generate the response using LLM + RAG (HyDE + Hybrid Search + Reranking + Dynamic Metadata).
    Updated: Safety handling, Unified RAG Pipeline, Expanded Categories.
    """
    router_outcome = state.get("router_outcome", "sales_flow")
    objection_type = state.get("objection_type")
    
    # 0. Safety Guardrails - Immediate Return (Requirement 1)
    if router_outcome == "handled_safety":
        if objection_type == "safety_violation":
             # Static polite refusal as requested
             response_text = "Entiendo tu curiosidad, pero mi función es ayudarte exclusivamente con tu negocio y el programa Visionarias. ¿Te parece si volvemos a enfocarnos en cómo escalar tu proyecto?"
             return {"messages": state["messages"] + [{"role": "assistant", "content": response_text}]}
        return state

    # 1. Advanced RAG Pipeline (Requirement 2 & 3)
    # "A todos los demás debe buscar en la base de datos"
    
    last_user_msg = state["messages"][-1]["content"]
    context_rag = ""
    
    # We run RAG for almost everything now to ensure coherence
    # Skip only for extremely short greetings if needed, but safer to run it.
    
    try:
        # Step A: HyDE (Hypothetical Document Embeddings)
        # Generate a hypothetical answer to improve retrieval
        hyde_prompt = prompt_loader.render("hyde_generator.j2", user_question=last_user_msg)
        hypothetical_doc = LLMFactory.get_service().generate_response(
            messages=[], 
            system_prompt=hyde_prompt,
            model_type="fast",
            temperature=0.7,
            max_output_tokens=300,
            top_p=0.9,
            presence_penalty=0.0,
            frequency_penalty=0.0
        )
        
        # Step B: Dynamic Filter Strategy (UPDATED Categories)
        rag_filters = {}
        msg_lower = last_user_msg.lower()
        
        # New Categories Mapping
        if any(w in msg_lower for w in ["reglas", "filtro", "puntual", "camara", "cámara", "requisito", "computadora", "internet", "boundary"]):
            rag_filters["doc_category"] = "protocol_boundary"
        elif any(w in msg_lower for w in ["miedo", "duda", "esposo", "socio", "no se", "no sé", "pensar", "segura", "estafa", "real", "funciona", "objecion"]):
             rag_filters["doc_category"] = ["sales_persuasion", "avatar_psychology"]
        elif any(w in msg_lower for w in ["precio", "costo", "valor", "cuanto", "cuánto", "dólares", "dolares", "soles", "factura", "boleta", "contrato", "garantia", "garantía", "reembolso", "devolución"]):
             rag_filters["doc_category"] = "financial_legal"
        elif any(w in msg_lower for w in ["fecha", "horario", "cuando", "cuándo", "hora", "dias", "días", "temario", "modulo", "plataforma", "grabacion", "entregable", "clase", "zoom", "producto"]):
             rag_filters["doc_category"] = "product_logic"
        elif any(w in msg_lower for w in ["dolor", "frustra", "estres", "cansad", "sola", "identidad", "emocion", "sentir", "psicologia"]):
             rag_filters["doc_category"] = "avatar_psychology"
        elif any(w in msg_lower for w in ["quien", "quién", "camila", "ileana", "historia", "filosofia", "liberar", "liderar", "experiencia", "autoridad", "marca"]):
             rag_filters["doc_category"] = "brand_authority"
        
        # If router already detected an intent, use it to augment filters
        if objection_type:
            if "price" in objection_type or "cost" in objection_type:
                rag_filters["doc_category"] = "financial_legal"
        
        # Step C: Hybrid Retrieval & Reranking
        context_rag = search_knowledge_base(
            query_text=hypothetical_doc, # Use HyDE doc + Original Query (handled in service)
            limit=5, 
            enable_rerank=True,
            filters=rag_filters
        )
    except Exception as e:
        print(f"RAG Pipeline Error: {e}")
        context_rag = ""

    # 2. Render Final Prompt
    # Requirement 3: Combine State logic + RAG + Router Outcome
    latest_reasoning = state.get("latest_reasoning", "")
    active_strategy = state.get("active_strategy", "Standard")
    
    # Requirement 6: Downsell TODO
    # "Todo lo que tenga que ver con esto comentalo y dejalo para revisarlo luego"
    # TODO: Implement Downsell Logic
    # if state.get("current_state") == FunnelStage.DOWNSELL_EXIT.value:
    #     # Logic for downsell offering would go here
    #     # For now, we rely on the generic response generation to handle it via prompt instructions
    #     pass

    system_prompt = prompt_loader.render(
        "sales_system.j2",
        current_state=state["current_state"],
        user_profile=state["user_profile"],
        context_rag=context_rag,
        active_strategy=active_strategy,
        latest_reasoning=latest_reasoning
    )
    
    try:
        # 3. Call LLM
        # Use SMART model for high quality responses that respect the complex prompt instructions
        response_text = LLMFactory.get_service().generate_response(
            messages=state["messages"],
            system_prompt=system_prompt,
            model_type="smart", 
            temperature=0.7,
            max_output_tokens=800,
            top_p=0.9,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            metadata={"rag_context": context_rag} # Pass RAG chunks for logging
        )
    except Exception as e:
        print(f"LLM Generation Error: {e}")
        response_text = ""

    # FALLBACK: Robustness check
    if not response_text or len(response_text.strip()) < 5:
        print("CRITICAL: Empty response from LLM. Triggering fallback.")
        response_text = "Disculpa, tuve un pequeño lapsus mental procesando eso. ¿Podrías repetírmelo o explicarme un poco más?"
    
    return {"messages": state["messages"] + [{"role": "assistant", "content": response_text}]}

@trace_node("safety_layer")
async def node_safety_layer(state: AgentState):
    """
    Safety Layer Node (formerly 'financial').
    Final gatekeeper to sanitize output and ensure data consistency.
    """
    try:
        from src.services.safety_service import SafetyLayerService
        
        # Get the last message generated by the assistant
        messages = state.get("messages", [])
        if not messages:
            return state
            
        last_msg = messages[-1]
        
        # Handle dict or object
        content = ""
        if isinstance(last_msg, dict):
            content = last_msg.get("content", "")
        elif hasattr(last_msg, "content"):
            content = last_msg.content
        else:
            content = str(last_msg)
            
        # Apply Safety Logic
        safety_service = SafetyLayerService()
        sanitized_content, safety_flag = await safety_service.sanitize_content(content)
        
        # Update state with sanitized content
        # We need to replace the last message content
        if isinstance(last_msg, dict):
            last_msg["content"] = sanitized_content
        elif hasattr(last_msg, "content"):
            last_msg.content = sanitized_content
            
        # Log if safety was triggered
        if safety_flag:
            return {
                "messages": messages, # With sanitized content
                "safety_flag": True # Flag for audit
            }
            
        return {"messages": messages}
        
    except Exception as e:
        print(f"Error in Safety Layer: {e}")
        # Fail safe: Return original state if safety layer crashes
        # (Or could return a generic error message if strict security is required)
        return state

@trace_node("exit_point")
def node_exit_point(state: AgentState):
    """
    Persistence Node.
    Ensures that the final state (Profile, Funnel Stage, Score) is saved to the DB
    so the next interaction continues seamlessly.
    """
    from src.services.database import SessionLocal
    from src.services.db.repositories.user import UserRepository
    from src.services.db.repositories.business import BusinessRepository
    
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        biz_repo = BusinessRepository(db)
        
        user_id = state.get("user_id")
        if not user_id:
            return state # Cannot persist without ID
            
        # 1. Persist User Profile
        if state.get("user_profile"):
            user_repo.update_profile(user_id, state["user_profile"])
            
        # 2. Persist Business State (Enrollment / Funnel)
        # This handles stage updates, lead score, and disqualification
        # The logic is encapsulated in BusinessRepository to keep this node clean.
        biz_repo.persist_agent_state(user_id, state)
        
    except Exception as e:
        # We catch everything because persistence failure should NOT block the response to user.
        # Ideally, we log this to Sentry/Datadog.
        import structlog
        logger = structlog.get_logger()
        logger.error(f"EXIT_POINT_ERROR: Failed to persist state for user {state.get('user_id')}: {e}")
    finally:
        db.close()
        
    return state
