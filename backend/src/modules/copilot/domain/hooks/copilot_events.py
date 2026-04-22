"""Copilot domain events.

All events are frozen dataclasses. Every event carries ``tenant_id`` and
``occurred_at`` for tenant isolation + observability (CONTRACT §16).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.routing_policy import ClassifierType


@dataclass(frozen=True, slots=True)
class CopilotEvent:
    """Base class for all copilot events.

    Not directly emitted — every concrete event re-declares ``tenant_id``
    and ``occurred_at`` for slot inheritance and immutability guarantees.
    """

    tenant_id: UUID
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ConversationCreated:
    """Emitted by ConversationStore.create."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    user_id: UUID


@dataclass(frozen=True, slots=True)
class MessageSent:
    """User-initiated POST /chat dispatched to the orchestrator."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    message_id: UUID
    length: int


@dataclass(frozen=True, slots=True)
class MessageReceived:
    """Orchestrator finished streaming a response (SSE ``done``)."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    message_id: UUID
    tier: ModelTier
    tokens_in: int
    tokens_out: int


@dataclass(frozen=True, slots=True)
class MutationApplied:
    """Mutation journaled after a successful tool call."""

    tenant_id: UUID
    occurred_at: datetime
    mutation_id: UUID
    conversation_id: UUID
    field_path: str


@dataclass(frozen=True, slots=True)
class MutationReverted:
    """Mutation reverted via the revert endpoint."""

    tenant_id: UUID
    occurred_at: datetime
    mutation_id: UUID
    conversation_id: UUID


@dataclass(frozen=True, slots=True)
class ProcedureAdvanced:
    """``advance_procedure`` tool moved the procedure forward."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    procedure_id: str
    block_before: str
    block_after: str
    coverage: float


@dataclass(frozen=True, slots=True)
class ProcedureCompleted:
    """Procedure reached coverage==1.0."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    procedure_id: str


@dataclass(frozen=True, slots=True)
class TierDecided:
    """Model router finished classifying a turn."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    message_id: UUID
    tier: ModelTier
    reason: str
    classifier: ClassifierType
    confidence: float


@dataclass(frozen=True, slots=True)
class PlanProposed:
    """Plan Mode handshake — plan proposed to the user."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    plan_id: UUID
    message_id: UUID
    steps_count: int
    total_cost: float


@dataclass(frozen=True, slots=True)
class PlanResolved:
    """Plan Mode handshake — plan approved / rejected / expired."""

    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    plan_id: UUID
    decision: str  # "approved" | "rejected" | "expired"
