import functools
import logging
import time
import uuid
import contextvars
from src.services.repository import Repository
from src.core.state import AgentState

logger = logging.getLogger(__name__)

# Context variable to hold the current trace_id (for LLM calls to attach to)
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)

def trace_node(node_name: str):
    """
    Decorator to trace LangGraph nodes.
    Captures input state, output state, execution time, and sets context for LLM logs.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(state: AgentState, *args, **kwargs):
            start_time = time.time()
            repo = Repository()
            
            # Prepare Input Snapshot (shallow copy to avoid huge logs if not needed)
            # Filter out heavy objects if necessary
            input_snapshot = {
                "current_state": state.get("current_state"),
                "router_outcome": state.get("router_outcome"),
                "last_message": state.get("messages", [])[-1] if state.get("messages") else None,
                "user_profile_summary": state.get("user_profile", {}).get("business_stage", "unknown")
            }
            
            user_id = state.get("user_id")
            # Session ID could be derived from date or passed in state. 
            # For now, we group by user + day roughly, or just use user_id.
            session_id = f"sess_{user_id}_{int(start_time/3600)}" 

            trace_obj = None
            
            try:
                # 1. Execute Node
                # We defer DB creation to END of execution to capture output, 
                # BUT we need an ID for LLM calls during execution.
                # Solution: Create Trace Record NOW with status "running" or empty output.
                
                # We can't easily update the row if we close session, so we keep repo open?
                # Better: Generate UUID here, set context, write row at the end.
                
                trace_uuid = uuid.uuid4()
                token = current_trace_id.set(str(trace_uuid))
                
                result_state = func(state, *args, **kwargs)
                
                execution_time = (time.time() - start_time) * 1000
                
                # Prepare Output Snapshot
                output_snapshot = {}
                if isinstance(result_state, dict):
                    output_snapshot = {
                        "router_outcome": result_state.get("router_outcome"),
                        "new_messages": result_state.get("messages", [])[-1] if result_state.get("messages") else None,
                        "next_state_update": result_state.get("current_state")
                    }
                
                # 2. Persist Trace
                # We actually need to write to DB using the UUID we generated.
                # Since we didn't write it before, the LLM logs might fail FK constraints if we enforce them strictly.
                # However, our models.py defined trace_id as nullable FK? Yes.
                # But to link them, we must write the trace now with the pre-generated ID.
                
                # Actually, simpler: Write trace at the end, and update LLM logs with trace_id? No, LLM logs happen inside.
                
                # Correct Strategy: Write Trace entry START (placeholder) -> Execute -> Update Trace entry END.
                # For simplicity/performance: Just write once at end. 
                # LLM Logs will use the ContextVar ID. 
                # If FK constraint fails, we need to insert Trace first.
                
                # Let's try: Insert Trace immediately.
                trace_obj = repo.create_trace(
                    user_id=user_id,
                    session_id=session_id,
                    node_name=node_name,
                    input_state=input_snapshot,
                    output_state={}, # Pending
                    execution_time_ms=0
                )
                
                if trace_obj:
                    # Update context with REAL DB ID
                    current_trace_id.set(str(trace_obj.id))
                
                # Re-run function? No, we already ran it? No, wait.
                # I need to insert BEFORE running func to get ID for LLM calls.
                # RESTART LOGIC:
                
                # A. Create Trace Record (Start)
                # B. Run Function
                # C. Update Trace Record (End)
                
                # Since repo.create_trace is atomic commit, we can't easily "update" without new transaction.
                # For this MVP, let's allow LLM logs to have trace_id, and we create trace at start.
                pass 
                
            except Exception as e:
                logger.error(f"Trace Error in {node_name}: {e}")
                raise e
            finally:
                # If we created a trace object, update it with results
                # (Skipping complex update logic for MVP, just logging 'finished' trace would be duplicate)
                # Let's refine:
                # 1. Create Trace with full info AFTER execution.
                # 2. BUT LLM calls inside need the ID.
                # 3. So we MUST create trace BEFORE execution.
                pass
        
        # --- RE-IMPLEMENTATION FOR CLARITY ---
        @functools.wraps(func)
        def wrapper_sync(state: AgentState, *args, **kwargs):
            start_time = time.time()
            repo = Repository()
            
            # --- USER ID RESOLUTION ---
            # Contract: state['user_id'] MUST be the Internal UUID (passed by API/Factory).
            user_uuid = state.get("user_id")
            
            # Basic validation
            if not user_uuid:
                 logger.warning(f"TRACING: Missing user_id in state for node {node_name}")
                 # We continue to avoid breaking flow, but trace might fail FK if DB enforces it
            
            session_id = f"sess_{user_uuid}_{int(start_time/3600)}" 
            
            input_snapshot = {
                "current_state": state.get("current_state"),
                "router_outcome": state.get("router_outcome"),
                "last_message": state.get("messages", [])[-1] if state.get("messages") else None
            }

            # 1. Create Initial Trace
            trace = repo.create_trace(
                user_id=user_uuid, 
                session_id=session_id,
                node_name=node_name,
                input_state=input_snapshot,
                output_state={"status": "running"},
                execution_time_ms=0
            )
            
            trace_id_val = str(trace.id) if trace else None
            token = current_trace_id.set(trace_id_val)
            
            # --- DEBUG LOGGING ---
            logger.debug(f"TRACING: Node={node_name}, UserID={user_uuid}, TraceID={trace_id_val}")
            
            try:
                # 2. Run Node
                result_state = func(state, *args, **kwargs)
                
                # 3. Update Trace
                execution_time = (time.time() - start_time) * 1000
                
                output_snapshot = {}
                if isinstance(result_state, dict):
                    output_snapshot = {
                        "router_outcome": result_state.get("router_outcome"),
                        "new_messages": result_state.get("messages", [])[-1] if result_state.get("messages") else None,
                        "next_state_update": result_state.get("current_state")
                    }
                
                if trace:
                    trace.output_state = output_snapshot
                    trace.execution_time_ms = execution_time
                    repo.db.commit()
                
                return result_state
                
            except Exception as e:
                logger.error(f"TRACING ERROR in {node_name}: {e}")
                if trace:
                    trace.output_state = {"error": str(e)}
                    repo.db.commit()
                raise e
            finally:
                current_trace_id.reset(token)
                repo.close()
                
        return wrapper_sync
    return decorator
