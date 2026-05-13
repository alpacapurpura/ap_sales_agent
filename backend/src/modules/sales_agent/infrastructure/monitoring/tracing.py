"""Tracing infrastructure module."""

from __future__ import annotations

import contextvars
import functools
import inspect
import logging
import time
from typing import TYPE_CHECKING, Any

from luana_core_sales_agent.infrastructure.db.database import SessionLocal
from luana_core_sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from luana_core_sales_agent.application.orchestrator.state import AgentState
    from luana_core_sales_agent.infrastructure.models.agent_trace_model import AgentTrace

logger = logging.getLogger(__name__)

# Context variable to hold the current trace_id (for LLM calls to attach to)
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)


def _build_input_snapshot(state: dict) -> dict:
    """Build the input snapshot dict from agent state."""
    messages = state.get("messages", [])
    return {
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


def _build_output_snapshot(result_state: dict) -> dict:
    """Build the output snapshot dict from result state."""
    if not isinstance(result_state, dict):
        return {}
    result_messages = result_state.get("messages", [])
    return {
        "next_node": result_state.get("next_node"),
        "current_state": result_state.get("current_state"),
        "detected_intent": result_state.get("detected_intent"),
        "lead_score": result_state.get("lead_score"),
        "new_message": result_messages[-1] if result_messages else None,
        "message_count": len(result_messages),
        "lead_data": result_state.get("lead_data"),
        "error": result_state.get("error"),
    }


def _setup_trace(
    node_name: str,
    state: dict,
) -> tuple[float, Any, AuditRepository, AgentTrace | None, contextvars.Token[str | None]]:
    """Create initial trace and set context variable. Returns trace context tuple."""
    start_time = time.time()
    db = SessionLocal()
    repo = AuditRepository(db)

    user_uuid = state.get("user_id")
    tenant_uuid = state.get("tenant_id")

    if not user_uuid:
        logger.warning("TRACING: Missing user_id in state for node %s", node_name)

    session_id = f"sess_{user_uuid}_{int(start_time / 3600)}"
    input_snapshot = _build_input_snapshot(state)

    trace = repo.create_trace(
        user_id=user_uuid,
        tenant_id=tenant_uuid,
        session_id=session_id,
        node_name=node_name,
        input_state=input_snapshot,
        output_state={"status": "running"},
        execution_time_ms=0,
    )

    trace_id_val = str(trace.id) if trace else None
    token = current_trace_id.set(trace_id_val)

    logger.debug(
        "TRACING: Node=%s, UserID=%s, TraceID=%s",
        node_name,
        user_uuid,
        trace_id_val,
    )

    return start_time, db, repo, trace, token


def _extract_rl_fields(trace: AgentTrace | None, result_state: dict) -> None:
    """Extract RL / Data Flywheel fields from result into trace."""
    if not isinstance(result_state, dict):
        return
    for field in ("action", "reward", "feedback"):
        if field in result_state:
            setattr(trace, field, result_state[field])


def _finalize_trace(
    node_name: str,
    start_time: float,
    repo: AuditRepository,
    trace: AgentTrace | None,
    token: contextvars.Token[str | None],
    result_state: dict,
) -> None:
    """Update trace with output snapshot and commit."""
    try:
        execution_time = (time.time() - start_time) * 1000
        output_snapshot = _build_output_snapshot(result_state)

        if trace:
            trace.output_state = output_snapshot
            trace.execution_time_ms = execution_time
            _extract_rl_fields(trace, result_state)
            repo.db.commit()
    except Exception:
        logger.exception("TRACING FINALIZE ERROR in %s", node_name)
    finally:
        current_trace_id.reset(token)
        repo.close()


def _handle_trace_error(
    node_name: str,
    e: Exception,
    repo: AuditRepository,
    trace: AgentTrace | None,
    token: contextvars.Token[str | None],
) -> None:
    """Handle trace error: log, persist error state, clean up."""
    logger.error("TRACING ERROR in %s: %s", node_name, e)
    if trace:
        try:
            trace.output_state = {"error": str(e)}
            repo.db.commit()
        except Exception:  # noqa: BLE001 — agent resilience
            pass
    current_trace_id.reset(token)
    repo.close()


def trace_node(node_name: str) -> Callable:
    """Trace LangGraph nodes.

    Captures input state, output state, execution time, and sets context for LLM logs.
    Supports both sync and async functions.
    """

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            return _make_async_wrapper(func, node_name)
        return _make_sync_wrapper(func, node_name)

    return decorator


def _make_async_wrapper(func: Callable, node_name: str) -> Callable:
    """Create an async tracing wrapper for the given function."""

    @functools.wraps(func)
    async def wrapper_async(state: AgentState, *args: Any, **kwargs: Any) -> dict:  # noqa: ANN401
        start_time, _db, repo, trace, token = _setup_trace(node_name, state)
        try:
            result_state = await func(state, *args, **kwargs)
            _finalize_trace(node_name, start_time, repo, trace, token, result_state)
        except Exception as e:
            _handle_trace_error(node_name, e, repo, trace, token)
            raise

        else:
            return result_state

    return wrapper_async


def _make_sync_wrapper(func: Callable, node_name: str) -> Callable:
    """Create a sync tracing wrapper for the given function."""

    @functools.wraps(func)
    def wrapper_sync(state: AgentState, *args: Any, **kwargs: Any) -> dict:  # noqa: ANN401
        start_time, _db, repo, trace, token = _setup_trace(node_name, state)
        try:
            result_state = func(state, *args, **kwargs)
            _finalize_trace(node_name, start_time, repo, trace, token, result_state)
        except Exception as e:
            _handle_trace_error(node_name, e, repo, trace, token)
            raise

        else:
            return result_state

    return wrapper_sync
