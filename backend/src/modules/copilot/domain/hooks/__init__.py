"""Copilot hook plugin domain types (events + registry protocol)."""

from luana_core_copilot.domain.hooks.copilot_events import (
    ConversationCreated,
    CopilotEvent,
    MessageReceived,
    MessageSent,
    MutationApplied,
    MutationReverted,
    PlanProposed,
    PlanResolved,
    ProcedureAdvanced,
    ProcedureCompleted,
    TierDecided,
)
from luana_core_copilot.domain.hooks.hook_registry import (
    HookHandler,
    HookRegistry,
)

__all__ = [
    "ConversationCreated",
    "CopilotEvent",
    "HookHandler",
    "HookRegistry",
    "MessageReceived",
    "MessageSent",
    "MutationApplied",
    "MutationReverted",
    "PlanProposed",
    "PlanResolved",
    "ProcedureAdvanced",
    "ProcedureCompleted",
    "TierDecided",
]
