"""State application module."""

import uuid
from typing import Any, TypedDict
from uuid import UUID


class AgentState(TypedDict):
    """Shared state for all LangGraph agents.

    Provides context for multi-tenant isolation and session management.
    """

    # Messaging
    messages: list[dict[str, Any]]  # [{"role": "user", "content": "..."}, ...]

    # Routing
    next_node: str | None

    # Context
    user_id: UUID | None
    tenant_id: UUID | None
    session_id: str | None

    # Agent Memory (Short Term)
    current_state: str | None  # e.g. "rapport", "discovery", "closing"
    detected_intent: str | None
    lead_score: int | None

    # Lead Data (Captured Information)
    lead_data: dict[str, Any] | None  # { "name": "...", "budget": "..." }

    # Configuration & History
    tenant_config: dict[str, Any] | None
    history: list[dict[str, Any]]
    user_profile: dict[str, Any] | None

    # Session Status
    session_active: bool
    active_enrollment: dict[str, Any] | None
    active_product: dict[str, Any] | None
    last_intent: str | None
    launch_stage: str | None

    # Agent Knowledge System (AKS)
    agent_identity: str | None  # Slot 4 — WHO+WHAT (brand+offers+team+legal). NO voice.
    brand_voice: str | None  # Slot 5 (S7) — HOW (PersonalityProfile.system_instruction).

    # Accumulated Signals (persisted via checkpoint)
    buying_signals: list[dict[str, Any]] | None
    objection_history: list[dict[str, Any]] | None
    qualification_answers: dict[str, Any] | None
    turn_count: int | None
    customer_profile_id: UUID | None
    channel_type: str | None
    close_strategy: str | None

    # Session continuity (Fase 2: cooldowns & greetings)
    session_gap_hours: float | None
    last_session_summary: str | None
    is_returning_user: bool | None

    # Question fatigue tracking (Fase 3)
    consecutive_questions: int | None
    follow_up_cadence: dict[str, Any] | None

    # Internal (graph loop control)
    internal_turn: int | None
    _pending_tool: dict[str, Any] | None
    _llm_service: object | None  # PR-6: BudgetGuardingLLMService injected at turn start

    # Errors
    error: str | None


def create_initial_state(
    user_id: str,
    tenant_id: str,
    session_id: str | None = None,
    lead_data: dict | None = None,
    tenant_config: dict | None = None,
    history: list[dict[str, Any]] | None = None,
    user_profile: dict | None = None,
    session_active: bool = True,
    active_enrollment: dict | None = None,
    active_product: dict | None = None,
    last_intent: str | None = None,
    launch_stage: str | None = None,
    agent_identity: str | None = None,
    brand_voice: str | None = None,
    # Checkpoint-persisted fields
    buying_signals: list[dict[str, Any]] | None = None,
    objection_history: list[dict[str, Any]] | None = None,
    qualification_answers: dict | None = None,
    turn_count: int | None = None,
    customer_profile_id: UUID | None = None,
    channel_type: str | None = None,
    close_strategy: str | None = None,
    current_state: str | None = None,
    lead_score: int | None = None,
    # Session continuity (Fase 2)
    session_gap_hours: float | None = None,
    last_session_summary: str | None = None,
    is_returning_user: bool | None = None,
    # Question fatigue (Fase 3)
    consecutive_questions: int | None = None,
    follow_up_cadence: dict | None = None,
    # PR-6: BudgetGuardingLLMService injected by ConversationPipeline
    _llm_service: object | None = None,
) -> AgentState:
    """Create a clean AgentState.

    Handles UUID conversion and default values.
    """
    # Ensure UUIDs
    try:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
    except Exception:  # noqa: BLE001 — orchestrator resilience
        uid = None

    try:
        tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    except Exception:  # noqa: BLE001 — orchestrator resilience
        tid = None

    return {
        "messages": [],
        "next_node": None,
        "user_id": uid,
        "tenant_id": tid,
        "session_id": session_id or str(uuid.uuid4()),
        "current_state": current_state or "rapport",
        "detected_intent": None,
        "lead_score": lead_score if lead_score is not None else 0,
        "lead_data": lead_data or {},
        "tenant_config": tenant_config or {},
        "history": history or [],
        "user_profile": user_profile or {},
        "session_active": session_active,
        "active_enrollment": active_enrollment,
        "active_product": active_product,
        "last_intent": last_intent,
        "launch_stage": launch_stage,
        "agent_identity": agent_identity,
        "brand_voice": brand_voice,
        # Checkpoint-persisted fields
        "buying_signals": buying_signals or [],
        "objection_history": objection_history or [],
        "qualification_answers": qualification_answers or {},
        "turn_count": turn_count or 0,
        "customer_profile_id": customer_profile_id,
        "channel_type": channel_type,
        "close_strategy": close_strategy,
        # Session continuity
        "session_gap_hours": session_gap_hours,
        "last_session_summary": last_session_summary,
        "is_returning_user": is_returning_user,
        # Question fatigue
        "consecutive_questions": consecutive_questions or 0,
        "follow_up_cadence": follow_up_cadence,
        # Internal
        "internal_turn": 0,
        "_pending_tool": None,
        "_llm_service": _llm_service,  # PR-6: BudgetGuardingLLMService or None
        "error": None,
    }
