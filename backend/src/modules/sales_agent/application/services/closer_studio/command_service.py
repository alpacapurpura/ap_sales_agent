"""ConversationCommandService — Closer Studio write-side (S11B step 5).

Handles ``stop_ai`` / ``resume_ai`` / ``send_message`` / ``reactivate`` /
``diagnose`` (which writes ``frozen_diagnosis`` after generating it).
Logs `[SYSTEM]` events when the operator changes the handler mode.
"""

from __future__ import annotations

import uuid as uuid_mod
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from src.modules.sales_agent.application.services.closer_studio.lead_helpers import (
    get_checkpoint,
)
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
        AgentStateCheckpointModel,
    )

logger = structlog.get_logger()


class ConversationCommandService:
    """Write-side service for Closer Studio actions."""

    def __init__(self, db: Session) -> None:
        """Bind the service to a SQLAlchemy session."""
        self.db = db

    # ── STOP ────────────────────────────────────────────────────────────

    def stop_ai(self, tenant_id: UUID, lead_id: UUID, user_id: UUID) -> dict | None:
        """Switch ``handler_mode`` to ``human`` and log a system event."""
        checkpoint = get_checkpoint(self.db, tenant_id, lead_id)
        if not checkpoint:
            return None

        checkpoint.handler_mode = "human"
        checkpoint.paused_at = datetime.now(timezone.utc)
        checkpoint.paused_by = user_id
        self.db.flush()

        self._log_system_event(
            tenant_id,
            lead_id,
            checkpoint.channel_type,
            "[SYSTEM] Owner took control of the conversation",
        )

        return {
            "lead_id": lead_id,
            "handler_mode": "human",
            "paused_at": checkpoint.paused_at,
        }

    # ── RESUME ──────────────────────────────────────────────────────────

    def resume_ai(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        objective: str | None = None,
    ) -> dict | None:
        """Switch ``handler_mode`` back to ``ai`` and seed the resume objective."""
        checkpoint = get_checkpoint(self.db, tenant_id, lead_id)
        if not checkpoint:
            return None

        checkpoint.handler_mode = "ai"
        checkpoint.paused_at = None
        checkpoint.paused_by = None
        checkpoint.resume_objective = objective
        self.db.flush()

        self._log_system_event(
            tenant_id,
            lead_id,
            checkpoint.channel_type,
            f"[SYSTEM] AI resumed{f' with objective: {objective}' if objective else ''}",
        )

        return {
            "lead_id": lead_id,
            "handler_mode": "ai",
            "resume_objective": objective,
        }

    # ── Send Message ────────────────────────────────────────────────────

    def send_message(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        content: str,
        mode: str = "direct",
    ) -> dict | None:
        """Persist a direct operator message or AI instruction."""
        checkpoint = get_checkpoint(self.db, tenant_id, lead_id)

        if mode == "instruction":
            if checkpoint:
                checkpoint.resume_objective = content
                self.db.flush()

            msg_id = uuid_mod.uuid4()
            msg = MessageModel(
                id=msg_id,
                user_id=lead_id,
                tenant_id=tenant_id,
                role="system",
                content=f"[INSTRUCCION DEL OPERADOR] {content}",
                channel=checkpoint.channel_type if checkpoint else None,
                sender_source="human_instruction",
            )
            self.db.add(msg)
            self.db.flush()

            return {
                "message_id": msg_id,
                "content": content,
                "mode": "instruction",
                "sent_to_channel": False,
            }

        msg_id = uuid_mod.uuid4()
        msg = MessageModel(
            id=msg_id,
            user_id=lead_id,
            tenant_id=tenant_id,
            role="assistant",
            content=content,
            channel=checkpoint.channel_type if checkpoint else None,
            sender_source="human_direct",
        )
        self.db.add(msg)
        self.db.flush()

        return {
            "message_id": msg_id,
            "content": content,
            "mode": "direct",
            "sent_to_channel": False,  # Will be updated after channel send
        }

    # ── Reactivate frozen ───────────────────────────────────────────────

    def reactivate(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        objective: str | None = None,
    ) -> dict | None:
        """Clear the frozen flags and seed the resume objective."""
        checkpoint = get_checkpoint(self.db, tenant_id, lead_id)
        if not checkpoint:
            return None

        checkpoint.frozen_at = None
        checkpoint.frozen_reason = None
        checkpoint.frozen_diagnosis = None
        checkpoint.handler_mode = "ai"
        checkpoint.resume_objective = objective
        self.db.flush()

        self._log_system_event(
            tenant_id,
            lead_id,
            checkpoint.channel_type,
            "[SYSTEM] Conversation reactivated by owner",
        )

        return {
            "lead_id": lead_id,
            "handler_mode": "ai",
            "message_sent": False,
        }

    # ── Diagnose ────────────────────────────────────────────────────────

    async def diagnose(self, tenant_id: UUID, lead_id: UUID) -> dict | None:
        """Generate AI diagnosis for a conversation."""
        checkpoint = get_checkpoint(self.db, tenant_id, lead_id)
        if not checkpoint:
            return None

        messages = (
            self.db.execute(
                select(MessageModel)
                .where(
                    MessageModel.user_id == lead_id,
                    MessageModel.tenant_id == tenant_id,
                )
                .order_by(MessageModel.created_at.desc())
                .limit(20),
            )
            .scalars()
            .all()
        )

        msg_summary = "\n".join(f"[{m.role}] {m.content[:200]}" for m in reversed(messages))

        diagnosis = {
            "lead_score": checkpoint.lead_score,
            "funnel_stage": checkpoint.current_stage,
            "turn_count": checkpoint.turn_count,
            "last_specialist": checkpoint.last_specialist,
            "buying_signals_count": len(checkpoint.buying_signals or []),
            "objection_count": len(checkpoint.objection_history or []),
            "summary": (
                f"Conversation with {checkpoint.turn_count} turns. "
                f"Score: {checkpoint.lead_score}. Stage: {checkpoint.current_stage}. "
                f"Last specialist: {checkpoint.last_specialist or 'none'}."
            ),
            "recommendation": self._generate_recommendation(checkpoint),
            "conversation_preview": msg_summary[:500],
        }

        checkpoint.frozen_diagnosis = diagnosis
        self.db.flush()

        return {
            "lead_id": lead_id,
            "diagnosis": diagnosis,
            "generated_at": datetime.now(timezone.utc),
        }

    # ── Internals ───────────────────────────────────────────────────────

    def _log_system_event(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str | None,
        content: str,
    ) -> None:
        msg = MessageModel(
            id=uuid_mod.uuid4(),
            user_id=lead_id,
            tenant_id=tenant_id,
            role="system",
            content=content,
            channel=channel,
            sender_source="auto",
        )
        self.db.add(msg)
        self.db.flush()

    @staticmethod
    def _generate_recommendation(checkpoint: AgentStateCheckpointModel) -> str:
        score = checkpoint.lead_score
        signals = len(checkpoint.buying_signals or [])
        stage = checkpoint.current_stage

        if score >= 70 and signals >= 3:
            return "High-intent lead ready to close. Resume AI with closing objective or send payment link directly."
        if score >= 40:
            return "Warm lead with moderate interest. Consider a personalized nudge or product demo offer."
        if stage == "rapport" and (checkpoint.turn_count or 0) > 5:
            return "Stuck in rapport stage despite multiple turns. Try a direct question about their needs."
        return "Low engagement. Consider a value-first reactivation message or disqualify."


__all__ = ["ConversationCommandService"]
