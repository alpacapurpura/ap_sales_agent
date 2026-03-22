import functools
import logging
import time
import contextvars
import inspect
from src.modules.sales_agent.infrastructure.memory.audit_repository import AuditRepository
from src.modules.sales_agent.infrastructure.db.database import SessionLocal
from src.modules.sales_agent.application.orchestrator.state import AgentState


logger = logging.getLogger(__name__)

# Context variable to hold the current trace_id (for LLM calls to attach to)
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)

def trace_node(node_name: str):
    """
    Decorator to trace LangGraph nodes.
    Captures input state, output state, execution time, and sets context for LLM logs.
    Supports both sync and async functions.
    """
    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)
        
        def _setup_trace(state):
            start_time = time.time()
            db = SessionLocal()
            repo = AuditRepository(db)
            
            # --- USER ID RESOLUTION ---
            user_uuid = state.get("user_id")
            tenant_uuid = state.get("tenant_id")
            
            if not user_uuid:
                 logger.warning(f"TRACING: Missing user_id in state for node {node_name}")
            
            session_id = f"sess_{user_uuid}_{int(start_time/3600)}" 
            
            messages = state.get("messages", [])
            input_snapshot = {
                "current_state": state.get("current_state"),
                "detected_intent": state.get("detected_intent"),
                "lead_score": state.get("lead_score"),
                "next_node": state.get("next_node"),
                "last_message": messages[-1] if messages else None,
                "message_count": len(messages),
                "has_agent_identity": bool(state.get("agent_identity")),
                "lead_data": state.get("lead_data"),
                "user_profile": state.get("user_profile"),
                "session_active": state.get("session_active"),
                "launch_stage": state.get("launch_stage"),
            }

            # 1. Create Initial Trace
            trace = repo.create_trace(
                user_id=user_uuid, 
                tenant_id=tenant_uuid,
                session_id=session_id,
                node_name=node_name,
                input_state=input_snapshot,
                output_state={"status": "running"},
                execution_time_ms=0
            )
            
            trace_id_val = str(trace.id) if trace else None
            token = current_trace_id.set(trace_id_val)
            
            logger.debug(f"TRACING: Node={node_name}, UserID={user_uuid}, TraceID={trace_id_val}")
            
            return start_time, db, repo, trace, token

        def _finalize_trace(start_time, repo, trace, token, result_state):
            try:
                # 3. Update Trace
                execution_time = (time.time() - start_time) * 1000
                
                output_snapshot = {}
                if isinstance(result_state, dict):
                    result_messages = result_state.get("messages", [])
                    output_snapshot = {
                        "next_node": result_state.get("next_node"),
                        "current_state": result_state.get("current_state"),
                        "detected_intent": result_state.get("detected_intent"),
                        "lead_score": result_state.get("lead_score"),
                        "new_message": result_messages[-1] if result_messages else None,
                        "message_count": len(result_messages),
                        "lead_data": result_state.get("lead_data"),
                        "error": result_state.get("error"),
                    }
                
                if trace:
                    trace.output_state = output_snapshot
                    trace.execution_time_ms = execution_time
                    
                    # RL / Data Flywheel Extraction
                    if isinstance(result_state, dict):
                         if "action" in result_state:
                             trace.action = result_state["action"]
                         if "reward" in result_state:
                             trace.reward = result_state["reward"]
                         if "feedback" in result_state:
                             trace.feedback = result_state["feedback"]
                             
                    repo.db.commit()
            except Exception as e:
                logger.error(f"TRACING FINALIZE ERROR in {node_name}: {e}")
            finally:
                current_trace_id.reset(token)
                repo.close()

        def _handle_error(e, repo, trace, token):
            logger.error(f"TRACING ERROR in {node_name}: {e}")
            if trace:
                try:
                    trace.output_state = {"error": str(e)}
                    repo.db.commit()
                except Exception:
                    pass
            current_trace_id.reset(token)
            repo.close()

        if is_async:
            @functools.wraps(func)
            async def wrapper_async(state: AgentState, *args, **kwargs):
                start_time, db, repo, trace, token = _setup_trace(state)
                try:
                    # 2. Run Node (Async)
                    result_state = await func(state, *args, **kwargs)
                    _finalize_trace(start_time, repo, trace, token, result_state)
                    return result_state
                except Exception as e:
                    _handle_error(e, repo, trace, token)
                    raise e
            return wrapper_async
        else:
            @functools.wraps(func)
            def wrapper_sync(state: AgentState, *args, **kwargs):
                start_time, db, repo, trace, token = _setup_trace(state)
                try:
                    # 2. Run Node (Sync)
                    result_state = func(state, *args, **kwargs)
                    _finalize_trace(start_time, repo, trace, token, result_state)
                    return result_state
                except Exception as e:
                    _handle_error(e, repo, trace, token)
                    raise e
            return wrapper_sync
            
    return decorator
