"""Business logic for the Closer Studio feature."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func, select, case, literal_column
from sqlalchemy.orm import Session, joinedload

from src.modules.crm.infrastructure.models.lead_model import LeadModel
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel

logger = structlog.get_logger()


class CloserStudioService:
    """Orchestrates Closer Studio queries and actions."""

    def __init__(self, db: Session):
        self.db = db

    # ── List conversations ──────────────────────────────────────────────

    def list_conversations(
        self,
        tenant_id: UUID,
        *,
        temperature: Optional[str] = None,
        handler_mode: Optional[str] = None,
        channel: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Return active conversations with last message preview."""

        # Subquery: last message per lead
        last_msg_sq = (
            select(
                MessageModel.user_id.label("lead_id"),
                func.max(MessageModel.created_at).label("last_msg_at"),
            )
            .where(MessageModel.tenant_id == tenant_id)
            .group_by(MessageModel.user_id)
            .subquery("last_msg")
        )

        # Main query: leads with active checkpoints
        stmt = (
            select(
                LeadModel,
                AgentStateCheckpointModel,
                last_msg_sq.c.last_msg_at,
            )
            .outerjoin(
                AgentStateCheckpointModel,
                (AgentStateCheckpointModel.lead_id == LeadModel.id)
                & (AgentStateCheckpointModel.tenant_id == tenant_id)
                & (AgentStateCheckpointModel.is_active.is_(True))
                & (AgentStateCheckpointModel.deleted_at.is_(None)),
            )
            .outerjoin(
                last_msg_sq,
                last_msg_sq.c.lead_id == LeadModel.id,
            )
            .where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.is_blacklisted.is_(False),
            )
        )

        # Filters
        if temperature:
            stmt = stmt.where(func.lower(LeadModel.temperature) == temperature.lower())
        if handler_mode:
            stmt = stmt.where(AgentStateCheckpointModel.handler_mode == handler_mode)
        if channel:
            stmt = stmt.where(AgentStateCheckpointModel.channel_type == channel)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.outerjoin(
                CustomerProfileModel,
                CustomerProfileModel.id == LeadModel.customer_id,
            ).where(
                CustomerProfileModel.full_name.ilike(search_pattern)
                | LeadModel.telegram_id.ilike(search_pattern)
                | LeadModel.whatsapp_id.ilike(search_pattern)
                | LeadModel.instagram_id.ilike(search_pattern)
            )

        # Count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        # Order: frozen last, then by last message desc
        stmt = stmt.order_by(
            # Escalated / human-handled first
            case(
                (AgentStateCheckpointModel.handler_mode == "human", literal_column("0")),
                else_=literal_column("1"),
            ),
            last_msg_sq.c.last_msg_at.desc().nullslast(),
        ).offset(offset).limit(limit)

        rows = self.db.execute(stmt).all()

        conversations = []
        for lead, checkpoint, last_msg_at in rows:
            # Get last message preview
            preview = self._get_last_message_preview(lead.id, tenant_id)
            display_name = self._resolve_display_name(lead)

            conversations.append({
                "lead_id": lead.id,
                "customer_profile_id": lead.customer_id,
                "display_name": display_name,
                "channel": checkpoint.channel_type if checkpoint else None,
                "temperature": lead.temperature,
                "lead_score": checkpoint.lead_score if checkpoint else (lead.intent_score or 0),
                "handler_mode": checkpoint.handler_mode if checkpoint else "ai",
                "funnel_stage": checkpoint.current_stage if checkpoint else "rapport",
                "pipeline_stage": self._lifecycle_stage(lead),
                "last_message_preview": preview,
                "last_message_at": last_msg_at,
                "unread_count": checkpoint.unread_count if checkpoint else 0,
                "avatar_url": self._resolve_avatar(lead),
                "is_frozen": bool(checkpoint and checkpoint.frozen_at),
            })

        return conversations, total

    # ── Detail ──────────────────────────────────────────────────────────

    def get_conversation_detail(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        *,
        message_limit: int = 50,
        before: Optional[datetime] = None,
    ) -> Optional[dict]:
        """Full conversation detail with paginated messages."""

        lead = (
            self.db.execute(
                select(LeadModel)
                .options(joinedload(LeadModel.customer))
                .where(LeadModel.id == lead_id, LeadModel.tenant_id == tenant_id)
            )
            .unique()
            .scalar_one_or_none()
        )
        if not lead:
            return None

        checkpoint = self.db.execute(
            select(AgentStateCheckpointModel).where(
                AgentStateCheckpointModel.lead_id == lead_id,
                AgentStateCheckpointModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.is_active.is_(True),
                AgentStateCheckpointModel.deleted_at.is_(None),
            ).order_by(AgentStateCheckpointModel.updated_at.desc())
        ).scalar_one_or_none()

        # Messages (paginated)
        msg_stmt = (
            select(MessageModel)
            .where(
                MessageModel.user_id == lead_id,
                MessageModel.tenant_id == tenant_id,
            )
        )
        if before:
            msg_stmt = msg_stmt.where(MessageModel.created_at < before)

        msg_stmt = msg_stmt.order_by(MessageModel.created_at.desc()).limit(message_limit)
        messages_raw = self.db.execute(msg_stmt).scalars().all()

        # Total count
        total_msgs = self.db.execute(
            select(func.count()).where(
                MessageModel.user_id == lead_id,
                MessageModel.tenant_id == tenant_id,
            )
        ).scalar() or 0

        messages = [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sender_source": m.sender_source,
                "channel": m.channel,
                "created_at": m.created_at,
                "metadata": m.metadata_log,
            }
            for m in reversed(messages_raw)  # chronological order
        ]

        # Reset unread
        if checkpoint and checkpoint.unread_count > 0:
            checkpoint.unread_count = 0
            self.db.flush()

        return {
            "lead_id": lead.id,
            "display_name": self._resolve_display_name(lead),
            "channel": checkpoint.channel_type if checkpoint else None,
            "temperature": lead.temperature,
            "lead_score": checkpoint.lead_score if checkpoint else 0,
            "handler_mode": checkpoint.handler_mode if checkpoint else "ai",
            "funnel_stage": checkpoint.current_stage if checkpoint else "rapport",
            "pipeline_stage": self._lifecycle_stage(lead),
            "paused_at": checkpoint.paused_at if checkpoint else None,
            "unread_count": 0,
            "qualification_answers": checkpoint.qualification_answers if checkpoint else None,
            "buying_signals": checkpoint.buying_signals if checkpoint else [],
            "lead_data": checkpoint.lead_data if checkpoint else None,
            "customer_profile_id": lead.customer_id,
            "avatar_url": self._resolve_avatar(lead),
            "messages": messages,
            "total_messages": total_msgs,
        }

    # ── STOP ────────────────────────────────────────────────────────────

    def stop_ai(self, tenant_id: UUID, lead_id: UUID, user_id: UUID) -> Optional[dict]:
        checkpoint = self._get_checkpoint(tenant_id, lead_id)
        if not checkpoint:
            return None

        checkpoint.handler_mode = "human"
        checkpoint.paused_at = datetime.now(timezone.utc)
        checkpoint.paused_by = user_id
        self.db.flush()

        # Log system event
        self._log_system_event(
            tenant_id, lead_id, checkpoint.channel_type,
            "[SYSTEM] Owner took control of the conversation",
        )

        return {
            "lead_id": lead_id,
            "handler_mode": "human",
            "paused_at": checkpoint.paused_at,
        }

    # ── RESUME ──────────────────────────────────────────────────────────

    def resume_ai(
        self, tenant_id: UUID, lead_id: UUID, objective: Optional[str] = None
    ) -> Optional[dict]:
        checkpoint = self._get_checkpoint(tenant_id, lead_id)
        if not checkpoint:
            return None

        checkpoint.handler_mode = "ai"
        checkpoint.paused_at = None
        checkpoint.paused_by = None
        checkpoint.resume_objective = objective
        self.db.flush()

        self._log_system_event(
            tenant_id, lead_id, checkpoint.channel_type,
            f"[SYSTEM] AI resumed{f' with objective: {objective}' if objective else ''}",
        )

        return {
            "lead_id": lead_id,
            "handler_mode": "ai",
            "resume_objective": objective,
        }

    # ── Send Message ────────────────────────────────────────────────────

    def send_message(
        self, tenant_id: UUID, lead_id: UUID, content: str, mode: str = "direct"
    ) -> Optional[dict]:
        """Send a direct message or AI instruction."""
        import uuid as uuid_mod

        checkpoint = self._get_checkpoint(tenant_id, lead_id)

        if mode == "instruction":
            # Store as resume_objective for next AI turn
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

        # Direct message — save to DB (channel sending handled by caller/channel_resolver)
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

    # ── Reactivate Frozen ───────────────────────────────────────────────

    def reactivate(
        self, tenant_id: UUID, lead_id: UUID, objective: Optional[str] = None
    ) -> Optional[dict]:
        checkpoint = self._get_checkpoint(tenant_id, lead_id)
        if not checkpoint:
            return None

        checkpoint.frozen_at = None
        checkpoint.frozen_reason = None
        checkpoint.frozen_diagnosis = None
        checkpoint.handler_mode = "ai"
        checkpoint.resume_objective = objective
        self.db.flush()

        self._log_system_event(
            tenant_id, lead_id, checkpoint.channel_type,
            "[SYSTEM] Conversation reactivated by owner",
        )

        return {
            "lead_id": lead_id,
            "handler_mode": "ai",
            "message_sent": False,
        }

    # ── Diagnose ────────────────────────────────────────────────────────

    async def diagnose(self, tenant_id: UUID, lead_id: UUID) -> Optional[dict]:
        """Generate AI diagnosis for a conversation."""
        checkpoint = self._get_checkpoint(tenant_id, lead_id)
        if not checkpoint:
            return None

        # Gather context
        messages = self.db.execute(
            select(MessageModel)
            .where(
                MessageModel.user_id == lead_id,
                MessageModel.tenant_id == tenant_id,
            )
            .order_by(MessageModel.created_at.desc())
            .limit(20)
        ).scalars().all()

        msg_summary = "\n".join(
            f"[{m.role}] {m.content[:200]}" for m in reversed(messages)
        )

        diagnosis = {
            "lead_score": checkpoint.lead_score,
            "funnel_stage": checkpoint.current_stage,
            "turn_count": checkpoint.turn_count,
            "last_specialist": checkpoint.last_specialist,
            "buying_signals_count": len(checkpoint.buying_signals or []),
            "objection_count": len(checkpoint.objection_history or []),
            "summary": f"Conversation with {checkpoint.turn_count} turns. "
                       f"Score: {checkpoint.lead_score}. Stage: {checkpoint.current_stage}. "
                       f"Last specialist: {checkpoint.last_specialist or 'none'}.",
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

    # ── Frozen List ─────────────────────────────────────────────────────

    def list_frozen(self, tenant_id: UUID) -> list[dict]:
        stmt = (
            select(LeadModel, AgentStateCheckpointModel)
            .join(
                AgentStateCheckpointModel,
                (AgentStateCheckpointModel.lead_id == LeadModel.id)
                & (AgentStateCheckpointModel.tenant_id == tenant_id)
                & (AgentStateCheckpointModel.is_active.is_(True)),
            )
            .where(
                LeadModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.frozen_at.isnot(None),
            )
            .order_by(AgentStateCheckpointModel.frozen_at.desc())
        )

        rows = self.db.execute(stmt).all()
        result = []
        for lead, checkpoint in rows:
            preview = self._get_last_message_preview(lead.id, tenant_id)
            result.append({
                "lead_id": lead.id,
                "display_name": self._resolve_display_name(lead),
                "channel": checkpoint.channel_type,
                "temperature": lead.temperature,
                "lead_score": checkpoint.lead_score,
                "funnel_stage": checkpoint.current_stage,
                "frozen_at": checkpoint.frozen_at,
                "frozen_reason": checkpoint.frozen_reason,
                "frozen_diagnosis": checkpoint.frozen_diagnosis,
                "last_message_at": None,
                "last_message_preview": preview,
                "avatar_url": self._resolve_avatar(lead),
            })
        return result

    # ── KPIs ────────────────────────────────────────────────────────────

    def get_kpis(self, tenant_id: UUID) -> dict:
        base = (
            select(
                func.count().label("total"),
                func.sum(case((AgentStateCheckpointModel.handler_mode == "ai", 1), else_=0)).label("ai"),
                func.sum(case((AgentStateCheckpointModel.handler_mode == "human", 1), else_=0)).label("human"),
                func.sum(case((AgentStateCheckpointModel.frozen_at.isnot(None), 1), else_=0)).label("frozen"),
                func.avg(AgentStateCheckpointModel.lead_score).label("avg_score"),
                func.sum(AgentStateCheckpointModel.unread_count).label("unread"),
            )
            .where(
                AgentStateCheckpointModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.is_active.is_(True),
                AgentStateCheckpointModel.deleted_at.is_(None),
            )
        )
        row = self.db.execute(base).one()

        # Temperature counts from leads
        temp_counts = self.db.execute(
            select(
                func.lower(LeadModel.temperature).label("temp"),
                func.count().label("cnt"),
            )
            .where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.is_blacklisted.is_(False),
            )
            .group_by(func.lower(LeadModel.temperature))
        ).all()
        temp_map = {t.temp: t.cnt for t in temp_counts if t.temp}

        return {
            "total_active": row.total or 0,
            "handled_by_ai": row.ai or 0,
            "handled_by_human": row.human or 0,
            "frozen_count": row.frozen or 0,
            "hot_count": temp_map.get("hot", 0),
            "warm_count": temp_map.get("warm", 0),
            "cold_count": temp_map.get("cold", 0),
            "avg_lead_score": round(float(row.avg_score or 0), 1),
            "unread_total": row.unread or 0,
        }

    # ── Private helpers ─────────────────────────────────────────────────

    def _get_checkpoint(
        self, tenant_id: UUID, lead_id: UUID
    ) -> Optional[AgentStateCheckpointModel]:
        return self.db.execute(
            select(AgentStateCheckpointModel).where(
                AgentStateCheckpointModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.lead_id == lead_id,
                AgentStateCheckpointModel.is_active.is_(True),
                AgentStateCheckpointModel.deleted_at.is_(None),
            ).order_by(AgentStateCheckpointModel.updated_at.desc())
        ).scalar_one_or_none()

    def _get_last_message_preview(self, lead_id: UUID, tenant_id: UUID) -> Optional[str]:
        msg = self.db.execute(
            select(MessageModel.content)
            .where(
                MessageModel.user_id == lead_id,
                MessageModel.tenant_id == tenant_id,
                MessageModel.role.in_(["user", "assistant"]),
            )
            .order_by(MessageModel.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if msg:
            return msg[:120] + ("..." if len(msg) > 120 else "")
        return None

    def _resolve_display_name(self, lead: LeadModel) -> str:
        if lead.customer and lead.customer.full_name:
            return lead.customer.full_name
        if lead.profile_data and isinstance(lead.profile_data, dict):
            first = lead.profile_data.get("first_name", "")
            last = lead.profile_data.get("last_name", "")
            name = f"{first} {last}".strip()
            if name:
                return name
        return lead.instagram_id or lead.telegram_id or lead.whatsapp_id or str(lead.id)[:8]

    def _resolve_avatar(self, lead: LeadModel) -> Optional[str]:
        if lead.customer and lead.customer.traits:
            return lead.customer.traits.get("profile_pic_url")
        return None

    def _lifecycle_stage(self, lead: LeadModel) -> Optional[str]:
        if lead.customer:
            return lead.customer.lifecycle_stage
        return None

    def _log_system_event(
        self, tenant_id: UUID, lead_id: UUID, channel: Optional[str], content: str
    ) -> None:
        import uuid as uuid_mod

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

    def _generate_recommendation(self, checkpoint: AgentStateCheckpointModel) -> str:
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
