"""AuditEmitter — domain events, journey tracking, WS notifications.

Carved out of :class:`ChatOrchestrator` (S11B Strangler Fig step 1). Owns
every side-effect that announces "something happened" to the rest of the
system (``event_bus``, ``journey_repo``, ``ws_manager``). Stateless;
methods are independent — caller decides which to invoke based on the
lifecycle state of the turn.

Best-effort: per-method failures are logged but never propagate. The
chat flow keeps running even if a journey event fails to persist or a
WS connection drops.

Cohesión: the orchestrator no longer knows about EventBus, journey
event shapes, or the WS protocol — it calls one of four methods on
this class.

# [SALES-AGENT-AUDIT-EMITTER-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

import structlog

from src.shared.domain.events import LeadCapturedEvent
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.domain.messages import IncomingMessage

# Cross-module models stay opaque so the arch ratchet
# (test_no_new_sales_agent_module_imports) keeps the count frozen.
# Callers pass duck-typed instances; runtime never inspects them.
_CustomerProfile = Any
_Lead = Any

logger = structlog.get_logger()


class AuditEmitter:
    """Side-effect publisher for chat flow events.

    Stateless static class. Lives outside the orchestrator so unit tests
    can drive each method in isolation; the orchestrator composes them
    along the happy path of ``process_chat_flow``.
    """

    @staticmethod
    def track_message_received(
        db: Session,
        tenant_uuid: UUID,
        customer: _CustomerProfile,
        capture_slug: str,
        channel_type: str,
        incoming: IncomingMessage,
    ) -> None:
        """Track ``message_received`` journey event for capture metrics."""
        try:
            from src.shared.links.ports.crm_repos import (
                get_journey_event_repository,
            )

            journey_repo = get_journey_event_repository(db)
            event_props = {
                "channel_slug": capture_slug,
                "channel_type": channel_type,
                "message_direction": "inbound",
            }
            mid = incoming.metadata.get("message_id")
            if mid:
                event_props["message_id"] = mid
            journey_repo.track_event(
                profile_id=customer.id,
                tenant_id=tenant_uuid,
                event_name="message_received",
                event_type="track",
                properties=event_props,
            )
        except Exception:  # noqa: BLE001 — orchestrator resilience
            logger.warning("failed_to_track_message_received", exc_info=True)

    @staticmethod
    def publish_lead_captured(
        db: Session,
        tenant_uuid: UUID,
        customer: _CustomerProfile,
        capture_slug: str,
        channel_type: str,
    ) -> None:
        """Publish ``LeadCapturedEvent`` when a new customer is created."""
        EventBus.publish(
            LeadCapturedEvent.create(
                tenant_id=tenant_uuid,
                profile_id=customer.id,
                channel_slug=capture_slug,
                extracted_field="external_id",
                source_channel_type=channel_type,
            ),
            session=db,
        )

    @staticmethod
    async def emit_assistant_message(
        tenant_uuid: UUID,
        user: _Lead,
        bot_text: str,
        result: dict,
    ) -> None:
        """Emit Closer Studio WS event after the agent replies (best-effort)."""
        try:
            from src.modules.sales_agent.infrastructure.ws_manager import ws_manager

            await ws_manager.emit(
                str(tenant_uuid),
                {
                    "type": "new_message",
                    "lead_id": str(user.id),
                    "role": "assistant",
                    "content": bot_text[:200],
                    "handler_mode": "ai",
                    "lead_score": result.get("lead_score", 0),
                    "funnel_stage": result.get("current_state", "rapport"),
                },
            )
        except Exception:  # noqa: BLE001 — orchestrator resilience
            with contextlib.suppress(Exception):
                logger.warning("ws_emit_assistant_failed", exc_info=True)

    @staticmethod
    async def emit_human_mode_message(
        tenant_uuid: UUID | None,
        user: _Lead,
        incoming: IncomingMessage,
    ) -> None:
        """Emit WS event when a lead message arrives while ``handler_mode='human'``."""
        try:
            from src.modules.sales_agent.infrastructure.ws_manager import ws_manager

            await ws_manager.emit(
                str(tenant_uuid),
                {
                    "type": "new_message",
                    "lead_id": str(user.id),
                    "role": "user",
                    "content": incoming.text[:200],
                    "handler_mode": "human",
                },
            )
        except Exception:  # noqa: BLE001 — orchestrator resilience
            with contextlib.suppress(Exception):
                logger.warning("ws_emit_human_mode_failed", exc_info=True)


__all__ = ["AuditEmitter"]
