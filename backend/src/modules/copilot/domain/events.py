"""Copilot domain events.

Published by the orchestrator (`chat.py`), tools, and `extraction_card_flow`.
Consumed by `src.modules.copilot.observability.recording.domain_subscribers`
which mirrors them into ``copilot_trace_event`` / ``copilot_routing_log`` rows.

Pattern aligns with sibling shared events (``SaleCompletedEvent``,
``LeadCapturedEvent``): each class extends :class:`DomainEvent` and exposes a
``create`` classmethod that bundles the typed args into the bus's stringly-typed
``payload: dict``. The bus dispatches by ``event_name``, so subclasses MUST
keep their ``event_name`` constant consistent with the ``EVENT_*`` literals
in :mod:`src.modules.copilot.observability.recording.domain_subscribers`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from luana_core_platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from uuid import UUID


# ── Event-name catalogue ────────────────────────────────────────────────
# Mirrored in ``observability/recording/domain_subscribers.py`` —
# subscribers and producers MUST agree on these literals.

EVENT_TURN_STARTED: str = "copilot_turn_started"
EVENT_TURN_ENDED: str = "copilot_turn_ended"
EVENT_CARD_EMITTED: str = "copilot_card_emitted"
EVENT_ROUTING_DECIDED: str = "copilot_routing_decided"
EVENT_SUGGESTION_SHOWN: str = "copilot_suggestion_shown"
EVENT_SUGGESTION_ACCEPTED: str = "copilot_suggestion_accepted"


def _str_or_none(value: object) -> str | None:
    """Serialise UUIDs / Decimals / None to JSONB-safe scalars."""
    return None if value is None else str(value)


@dataclass
class TurnStarted(DomainEvent):
    """Emitted by ``CopilotOrchestrator.stream_chat`` at the top of every turn."""

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        conversation_id: UUID | None,
        turn_id: UUID,
        message_preview: str,
        current_route: str | None,
        guided_mode: bool,
        attachment_count: int,
    ) -> TurnStarted:
        """Build a ``copilot_turn_started`` event."""
        return cls(
            event_name=EVENT_TURN_STARTED,
            tenant_id=tenant_id,
            payload={
                "turn_id": _str_or_none(turn_id),
                "conversation_id": _str_or_none(conversation_id),
                "user_id": _str_or_none(user_id),
                "message_preview": message_preview,
                "current_route": current_route,
                "guided_mode": guided_mode,
                "attachment_count": int(attachment_count),
            },
        )


@dataclass
class TurnEnded(DomainEvent):
    """Emitted by ``CopilotOrchestrator.stream_chat`` after the stream drains."""

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        response_length: int,
        message_count: int,
        block_count: int,
        duration_ms: int,
        error_type: str | None,
    ) -> TurnEnded:
        """Build a ``copilot_turn_ended`` event."""
        return cls(
            event_name=EVENT_TURN_ENDED,
            tenant_id=tenant_id,
            payload={
                "turn_id": _str_or_none(turn_id),
                "response_length": int(response_length),
                "message_count": int(message_count),
                "block_count": int(block_count),
                "duration_ms": int(duration_ms),
                "error_type": error_type,
            },
        )


@dataclass
class CardEmitted(DomainEvent):
    """Emitted whenever a typed CardBlock is appended to the assistant message.

    Sources today:

    * ``CopilotOrchestrator._handle_tool_end_v2`` — UI cards from tools.
    * ``CopilotOrchestrator._maybe_emit_plan_card`` — deep-agent plan cards.
    * ``extraction_card_flow.emit_section_complete_pill`` — navigation pills.
    * ``extraction_card_flow.emit_extraction_summary_card`` — final summary.
    """

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        conversation_id: UUID | None,
        card_kind: str,
        source_tool: str,
        payload_keys: list[str],
    ) -> CardEmitted:
        """Build a ``copilot_card_emitted`` event."""
        return cls(
            event_name=EVENT_CARD_EMITTED,
            tenant_id=tenant_id,
            payload={
                "turn_id": _str_or_none(turn_id),
                "conversation_id": _str_or_none(conversation_id),
                "card_kind": card_kind,
                "source_tool": source_tool,
                "payload_keys": list(payload_keys),
            },
        )


@dataclass
class RoutingDecided(DomainEvent):
    """Emitted by ``CopilotOrchestrator._record_routing_decision*`` for telemetry.

    The orchestrator already inserts the canonical row into ``copilot_routing_log``;
    this event lets observability mirror the decision into ``copilot_trace_event``
    so a single SQL query reconstructs the per-turn timeline.
    """

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        role_selected: str,
        classifier_used: str,
        reason: str,
        confidence: Decimal | float | None,
        user_msg_length: int,
        tools_available: int,
    ) -> RoutingDecided:
        """Build a ``copilot_routing_decided`` event."""
        confidence_str: str | None
        if confidence is None:
            confidence_str = None
        elif isinstance(confidence, Decimal):
            confidence_str = format(confidence, "f")
        else:
            confidence_str = str(confidence)

        return cls(
            event_name=EVENT_ROUTING_DECIDED,
            tenant_id=tenant_id,
            payload={
                "conversation_id": _str_or_none(conversation_id),
                "message_id": _str_or_none(message_id),
                "role": role_selected,
                "classifier": classifier_used,
                "reason": reason,
                "confidence": confidence_str,
                "user_msg_length": int(user_msg_length),
                "tools_available": int(tools_available),
            },
        )


@dataclass
class SuggestionShown(DomainEvent):
    """Emitted when ``SuggestionEngine.get_suggestions(...)`` returns ≥1 chip.

    [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
    """

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        conversation_id: UUID | None,
        current_route: str | None,
        suggestion_ids: list[UUID],
        provider_breakdown: dict[str, int],
        latency_ms: int,
    ) -> SuggestionShown:
        """Build a ``copilot_suggestion_shown`` event."""
        return cls(
            event_name=EVENT_SUGGESTION_SHOWN,
            tenant_id=tenant_id,
            payload={
                "user_id": _str_or_none(user_id),
                "conversation_id": _str_or_none(conversation_id),
                "current_route": current_route,
                "suggestion_ids": [_str_or_none(sid) for sid in suggestion_ids],
                "provider_breakdown": dict(provider_breakdown),
                "latency_ms": int(latency_ms),
            },
        )


@dataclass
class SuggestionAccepted(DomainEvent):
    """Emitted when API receives ``POST /suggestions/{id}/accept`` (FE click chip).

    [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
    """

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        conversation_id: UUID | None,
        suggestion_id: UUID,
        source_module: str,
        category: str,
    ) -> SuggestionAccepted:
        """Build a ``copilot_suggestion_accepted`` event."""
        return cls(
            event_name=EVENT_SUGGESTION_ACCEPTED,
            tenant_id=tenant_id,
            payload={
                "user_id": _str_or_none(user_id),
                "conversation_id": _str_or_none(conversation_id),
                "suggestion_id": _str_or_none(suggestion_id),
                "source_module": source_module,
                "category": category,
            },
        )


__all__ = [
    "EVENT_CARD_EMITTED",
    "EVENT_ROUTING_DECIDED",
    "EVENT_SUGGESTION_ACCEPTED",
    "EVENT_SUGGESTION_SHOWN",
    "EVENT_TURN_ENDED",
    "EVENT_TURN_STARTED",
    "CardEmitted",
    "RoutingDecided",
    "SuggestionAccepted",
    "SuggestionShown",
    "TurnEnded",
    "TurnStarted",
]
