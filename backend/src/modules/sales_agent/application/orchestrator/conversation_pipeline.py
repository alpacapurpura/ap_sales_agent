"""ConversationPipeline — state machine + dispatch for one chat turn.

Carved out of :class:`ChatOrchestrator` (S11B Strangler Fig step 3). Owns
every step between "lead identity resolved" and "agent reply sent":
fetching tenant config, loading the checkpoint, deciding session state,
composing the initial AgentState, sanitizing input, dispatching to the
LangGraph subgraph, persisting the checkpoint, and delivering the
response.

Boundary: this class talks to ``audit_repo`` / ``state_repo`` /
``biz_repo`` / ``LLMFactory`` / :data:`agent_app` / ``OutputManager``.
It does NOT know about IG enrichment, journey events, or domain event
publishing — that's :class:`IdentityResolver` + :class:`AuditEmitter`.
For the WS notification on the assistant turn it asks
:class:`AuditEmitter`. For the WS notification on a human-mode skip it
also asks :class:`AuditEmitter`.

Cross-module crm/iam models stay opaque (``Any``) so the
``sales_agent -> crm`` arch ratchet count remains frozen.

# [SALES-AGENT-CONVERSATION-PIPELINE-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select

from src.modules.sales_agent.application.orchestrator.audit_emitter import AuditEmitter
from src.modules.sales_agent.application.orchestrator.graph import agent_app
from src.modules.sales_agent.application.orchestrator.state import create_initial_state
from src.modules.sales_agent.application.services.knowledge_builder import (
    TenantKnowledgeBuilder,
)
from src.modules.sales_agent.application.services.semantic_router import SemanticRouter
from src.modules.sales_agent.domain.model_tier import LLM_ROLE_BY_SITE
from src.modules.sales_agent.domain.tuning import (
    MESSAGE_HISTORY_LIMIT,
    SESSION_TIMEOUT_HOURS,
)
from src.modules.sales_agent.infrastructure.external.output_manager import OutputManager
from src.shared.billing.application.llm_guards import BudgetGuardingLLMService
from src.shared.infrastructure.llm.factory import LLMFactory

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.sales_agent.infrastructure.memory.audit_repository import (
        AuditRepository,
    )
    from src.modules.sales_agent.infrastructure.repositories.state_repository import (
        StateRepository,
    )
    from src.shared.billing.application.budget_guard import BudgetGuard
    from src.shared.domain.messages import IncomingMessage
    from src.shared.infrastructure.channels.base import BaseChannel

# Cross-module facades stay opaque (see audit_emitter.py rationale).
_Customer = Any
_Lead = Any
_Tenant = Any
_BizRepo = Any
_Checkpoint = Any

logger = structlog.get_logger()


class ConversationPipeline:
    """State machine + dispatch for one chat turn. Stateless static class."""

    # ── Tenant + checkpoint ──────────────────────────────────────────

    @staticmethod
    def fetch_tenant_config(db: Session, tenant_id: str) -> tuple[UUID | None, dict]:
        """Resolve tenant UUID + config dict. Returns ``(uuid, config)`` or ``(None, {})``."""
        if not tenant_id:
            return None, {}
        try:
            from uuid import UUID as _UUID

            from src.modules.iam.infrastructure.models.tenant_model import TenantModel

            tenant_uuid = _UUID(tenant_id)
            tenant_obj = db.execute(select(TenantModel).where(TenantModel.id == tenant_uuid)).scalars().first()
            if tenant_obj:
                return tenant_uuid, tenant_obj.config_json or {}
        except Exception:
            logger.exception("Error fetching tenant config")
            return None, {}

        return tenant_uuid, {}

    @staticmethod
    def load_checkpoint(
        db: Session,
        state_repo: StateRepository,
        tenant_uuid: UUID | None,
        user_id: UUID,
    ) -> _Checkpoint | None:
        """Load the active checkpoint for a lead, rolling back on failure."""
        if not tenant_uuid:
            return None
        try:
            return state_repo.get_active_checkpoint(tenant_uuid, user_id)
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("checkpoint_load_failed", error=str(e))
            with contextlib.suppress(Exception):
                db.rollback()
            return None

    @staticmethod
    async def handle_human_mode(
        db: Session,
        checkpoint: _Checkpoint | None,
        user: _Lead,
        tenant_uuid: UUID | None,
        tenant_id: str | None,
        incoming: IncomingMessage,
    ) -> bool:
        """Handle ``handler_mode='human'``: increment unread, emit WS, skip AI."""
        if not (checkpoint and checkpoint.handler_mode == "human"):
            return False

        logger.info(
            "handler_mode_human_skip",
            lead_id=str(user.id),
            tenant_id=tenant_id,
        )
        checkpoint.unread_count = (checkpoint.unread_count or 0) + 1
        checkpoint.last_human_message_at = datetime.now(timezone.utc)
        db.commit()

        await AuditEmitter.emit_human_mode_message(tenant_uuid, user, incoming)
        return True

    # ── Session state ────────────────────────────────────────────────

    @staticmethod
    def determine_session_state(audit_repo: AuditRepository, user: _Lead) -> dict:
        """Compute ``session_active`` / ``last_intent`` / gap / returning flags."""
        last_msg = audit_repo.get_last_message(user.id)
        result = {
            "session_active": True,
            "last_intent": None,
            "session_gap_hours": None,
            "is_returning_user": False,
        }

        if not (last_msg and last_msg.created_at):
            return result

        msg_time = last_msg.created_at
        if msg_time.tzinfo is None:
            msg_time = msg_time.replace(tzinfo=timezone.utc)
        time_diff = datetime.now(timezone.utc) - msg_time
        result["session_gap_hours"] = time_diff.total_seconds() / 3600
        result["is_returning_user"] = True
        if time_diff > timedelta(hours=SESSION_TIMEOUT_HOURS):
            result["session_active"] = False

        if last_msg.metadata_log and isinstance(last_msg.metadata_log, dict):
            result["last_intent"] = last_msg.metadata_log.get("intent")

        return result

    @staticmethod
    def build_checkpoint_data(
        checkpoint: _Checkpoint | None,
        session_active: bool,
        history: list,
        base_profile: dict,
        state_repo: StateRepository,
        tenant_uuid: UUID | None,
        user: _Lead,
    ) -> tuple[dict, str | None]:
        """Project the active checkpoint (or last summary) into AgentState fields."""
        checkpoint_data: dict = {}
        last_session_summary = None

        if checkpoint and session_active:
            checkpoint_data = {
                "current_state": checkpoint.current_stage,
                "lead_score": checkpoint.lead_score,
                "lead_data": checkpoint.lead_data or {},
                "buying_signals": checkpoint.buying_signals or [],
                "objection_history": checkpoint.objection_history or [],
                "qualification_answers": checkpoint.qualification_answers or {},
                "turn_count": checkpoint.turn_count or 0,
                "close_strategy": checkpoint.close_strategy,
                "consecutive_questions": checkpoint.consecutive_questions or 0,
                "follow_up_cadence": checkpoint.follow_up_cadence,
            }
            last_session_summary = (checkpoint.lead_data or {}).get("session_summary")
        elif checkpoint and not session_active:
            if checkpoint.lead_data is not None:
                last_session_summary = (checkpoint.lead_data or {}).get("session_summary")
                if not last_session_summary and history:
                    try:
                        from src.modules.sales_agent.infrastructure.prompts.base import (
                            prompt_loader,
                        )

                        summary_prompt = prompt_loader.render(
                            "summary_generator",
                            messages=history[-10:],
                            user_profile=base_profile,
                        )
                        summary = LLMFactory.get_service().generate_response(
                            messages=[],
                            system_prompt=summary_prompt,
                            model_type=LLM_ROLE_BY_SITE["summary"],
                            temperature=0.0,
                            max_output_tokens=100,
                            metadata={"prompt_template": "summary_generator"},
                        )
                        last_session_summary = summary.strip()
                    except Exception as e:  # noqa: BLE001 — orchestrator resilience
                        logger.warning("session_summary_generation_failed", error=str(e))
            state_repo.deactivate(tenant_uuid, user.id)

        return checkpoint_data, last_session_summary

    @staticmethod
    def build_user_profile(user: _Lead) -> dict:
        """Compose the AgentState user_profile dict from lead + style fields."""
        if user and user.profile_data:
            base_profile = (
                user.profile_data.model_dump() if hasattr(user.profile_data, "model_dump") else dict(user.profile_data)
            )
        else:
            base_profile = {}

        if getattr(user, "custom_system_instruction", None):
            base_profile["custom_instruction"] = user.custom_system_instruction
        if getattr(user, "style_profile", None):
            base_profile["style_profile"] = user.style_profile

        return base_profile

    # ── Identity strings (slot 4 + slot 5) ──────────────────────────

    @staticmethod
    def build_agent_identity(db: Session, tenant_uuid: UUID | None) -> str | None:
        """Build slot 4 AGENT_IDENTITY string. Best-effort."""
        if not tenant_uuid:
            return None
        try:
            knowledge_builder = TenantKnowledgeBuilder(db)
            return knowledge_builder.build_identity(tenant_uuid)
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("Could not build agent identity", error=str(e))
            with contextlib.suppress(Exception):
                db.rollback()
            return None

    @staticmethod
    def build_brand_voice(db: Session, tenant_uuid: UUID | None) -> str | None:
        """Build slot 5 BRAND_VOICE string from PersonalityProfile. Best-effort.

        See ``.claude/rules/sales-agent-brand-voice.md``.
        """
        if not tenant_uuid:
            return None
        try:
            knowledge_builder = TenantKnowledgeBuilder(db)
            return knowledge_builder.build_brand_voice(tenant_uuid)
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("Could not build brand voice", error=str(e))
            with contextlib.suppress(Exception):
                db.rollback()
            return None

    # ── Sanitization ────────────────────────────────────────────────

    @staticmethod
    async def sanitize_text(text: str, direction: str = "input") -> str:
        """Run input/output through the safety layer. Returns original on failure."""
        try:
            from src.modules.sales_agent.infrastructure.external.safety_service import (
                SafetyLayerService,
            )

            safety = SafetyLayerService()
            sanitized, was_modified = await safety.sanitize_content(text)
            if was_modified:
                logger.warning("content_sanitized", direction=direction, original_preview=text[:50])
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("safety_sanitization_failed", direction=direction, error=str(e))
            return text

        return sanitized

    # ── Initial state composition ───────────────────────────────────

    @staticmethod
    def build_initial_state(
        *,
        db: Session,
        biz_repo: _BizRepo,
        audit_repo: AuditRepository,
        user: _Lead,
        customer: _Customer,
        tenant_id: str | None,
        tenant_uuid: UUID | None,
        tenant_config: dict,
        incoming: IncomingMessage,
        session_state: dict,
        agent_identity: str | None,
        brand_voice: str | None,
        checkpoint: _Checkpoint | None,
        state_repo: StateRepository,
        budget_guard: BudgetGuard | None = None,  # PR-6: BudgetGuard injected here
        # PR-7: outbound additive (defaults preserve inbound behavior)
        campaign_id: UUID | None = None,
        campaign_instructions: str | None = None,
        outbound_mode: bool = False,
    ) -> tuple[dict, str | None]:
        """Build the AgentState dict consumed by ``agent_app.ainvoke``."""
        active_product, launch_stage = biz_repo.get_current_launch_product()
        active_enrollment = None
        active_product_dict = None
        if active_product:
            active_enrollment = biz_repo.get_enrollment(user.id, active_product.id)
            active_product_dict = {
                "id": str(active_product.id),
                "name": getattr(active_product, "name", None),
                "status": getattr(active_product, "status", None),
                "price": getattr(active_product, "price", None),
            }

        raw_history = audit_repo.get_chat_history(user.id, limit=MESSAGE_HISTORY_LIMIT)
        history = [{"role": msg.role, "content": msg.content} for msg in raw_history if msg.content]

        base_profile = ConversationPipeline.build_user_profile(user)
        checkpoint_data, last_session_summary = ConversationPipeline.build_checkpoint_data(
            checkpoint,
            session_state["session_active"],
            history,
            base_profile,
            state_repo,
            tenant_uuid,
            user,
        )

        # PR-6: build guarded LLM service when budget_guard is wired.
        # BudgetGuardingLLMService wraps LLMFactory.get_service() so every
        # specialist node (supervisor / qualifier / product_expert / closer)
        # gates via BudgetGuard.check() without per-callsite changes.
        guarded_llm_service = None
        if budget_guard is not None and tenant_uuid is not None:
            guarded_llm_service = BudgetGuardingLLMService(
                inner=LLMFactory.get_service(),
                budget_guard=budget_guard,
                tenant_id=tenant_uuid,
                agent_kind="sales_agent",
            )

        initial_state = create_initial_state(
            user_id=str(user.id),
            tenant_id=str(tenant_id) if tenant_id else str(uuid.uuid4()),
            tenant_config=tenant_config,
            history=history,
            user_profile={**base_profile, **incoming.metadata},
            session_active=session_state["session_active"],
            active_enrollment=active_enrollment,
            active_product=active_product_dict,
            last_intent=session_state["last_intent"],
            agent_identity=agent_identity,
            brand_voice=brand_voice,
            customer_profile_id=customer.id,
            channel_type=incoming.channel_type,
            session_gap_hours=session_state["session_gap_hours"],
            last_session_summary=last_session_summary,
            is_returning_user=session_state["is_returning_user"],
            _llm_service=guarded_llm_service,
            # PR-7: outbound additive pass-through
            campaign_id=campaign_id,
            campaign_instructions=campaign_instructions,
            outbound_mode=outbound_mode,
            **checkpoint_data,
        )

        if launch_stage:
            initial_state["launch_stage"] = launch_stage

        # Clear follow-up cadence when user re-engages (Fase 4)
        if checkpoint and checkpoint.follow_up_cadence:
            checkpoint.follow_up_cadence = None
            db.flush()
            initial_state["follow_up_cadence"] = None

        return initial_state, last_session_summary

    @staticmethod
    async def prepare_messages_and_intent(
        incoming: IncomingMessage,
        initial_state: dict,
        checkpoint: _Checkpoint | None,
        db: Session,
        tenant_uuid: UUID | None,
    ) -> None:
        """Sanitize input, inject into messages, detect intent, apply resume_objective."""
        sanitized_text = await ConversationPipeline.sanitize_text(incoming.text, "user_input")
        initial_state["messages"] = [{"role": "user", "content": sanitized_text}]

        if checkpoint and checkpoint.resume_objective:
            initial_state["messages"].insert(
                0,
                {
                    "role": "system",
                    "content": f"[INSTRUCCION DEL OPERADOR] {checkpoint.resume_objective}",
                },
            )
            checkpoint.resume_objective = None
            db.flush()

        try:
            detected_intent, intent_score, updated_signals = SemanticRouter.detect_and_accumulate(
                incoming.text,
                existing_signals=initial_state.get("buying_signals", []),
                tenant_id=tenant_uuid,
            )
            if detected_intent:
                initial_state["detected_intent"] = detected_intent
                initial_state["buying_signals"] = updated_signals
                logger.debug(
                    "semantic_intent_detected",
                    intent=detected_intent,
                    score=round(intent_score, 2),
                )
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("Semantic router failed, continuing without intent", error=str(e))

    # ── Dispatch ────────────────────────────────────────────────────

    @staticmethod
    async def invoke_agent_with_typing(
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        initial_state: dict,
        observability_handler: object | None = None,
    ) -> dict:
        """Run the LangGraph subgraph while sending periodic typing indicators."""

        async def _keep_typing() -> None:
            while True:
                await asyncio.sleep(3)
                with contextlib.suppress(Exception):
                    await channel_adapter.set_typing_status(incoming.user_id)

        typing_task = asyncio.create_task(_keep_typing())
        try:
            config = {"callbacks": [observability_handler]} if observability_handler is not None else {}
            return await agent_app.ainvoke(initial_state, config=config)
        finally:
            typing_task.cancel()

    @staticmethod
    def save_checkpoint(
        db: Session,
        state_repo: StateRepository,
        tenant_uuid: UUID,
        user: _Lead,
        customer: _Customer,
        channel_type: str,
        initial_state: dict,
        result: dict,
        last_session_summary: str | None,
    ) -> None:
        """Persist the agent state checkpoint after graph execution."""
        try:
            result_lead_data = result.get("lead_data", {}) or {}
            if last_session_summary:
                result_lead_data["session_summary"] = last_session_summary

            state_repo.save_checkpoint(
                tenant_id=tenant_uuid,
                lead_id=user.id,
                session_id=initial_state.get("session_id", ""),
                customer_profile_id=customer.id,
                channel_type=channel_type,
                current_stage=result.get("current_state", "rapport"),
                lead_score=result.get("lead_score", 0),
                lead_data=result_lead_data,
                buying_signals=result.get("buying_signals", []),
                objection_history=result.get("objection_history", []),
                qualification_answers=result.get("qualification_answers", {}),
                turn_count=result.get("turn_count", 0),
                last_specialist=result.get("next_node"),
                close_strategy=result.get("close_strategy"),
                consecutive_questions=result.get("consecutive_questions", 0),
                follow_up_cadence=result.get("follow_up_cadence"),
            )
            db.commit()
        except Exception as e:
            logger.exception("checkpoint_save_failed", error=str(e))
            with contextlib.suppress(Exception):
                db.rollback()

    @staticmethod
    async def deliver_response(
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        result: dict,
        audit_repo: AuditRepository,
        user: _Lead,
        channel_type: str,
        tenant_uuid: UUID | None,
    ) -> None:
        """Sanitize, log, send the agent response, and emit Closer Studio WS."""
        last_msg = result["messages"][-1]
        bot_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
        bot_text = await ConversationPipeline.sanitize_text(bot_text, "bot_output")

        audit_repo.log_message(
            user_id=user.id,
            role="assistant",
            content=bot_text,
            channel=channel_type,
            tenant_id=tenant_uuid,
        )

        await OutputManager.process_response(
            incoming.user_id,
            bot_text,
            channel_adapter,
            channel_type=channel_type,
        )

        if tenant_uuid:
            await AuditEmitter.emit_assistant_message(tenant_uuid, user, bot_text, result)


__all__ = ["ConversationPipeline"]
