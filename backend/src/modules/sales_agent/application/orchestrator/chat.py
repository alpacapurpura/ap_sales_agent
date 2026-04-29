"""Chat application module."""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Self
from uuid import UUID

import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from fastapi import BackgroundTasks
    from sqlalchemy.orm import Session

    from src.modules.crm.application.services.identity_service import IdentityService
    from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
    from src.modules.crm.infrastructure.models.lead_model import LeadModel
    from src.modules.crm.infrastructure.repositories.lead_metrics_repository import LeadRepository
    from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
        AgentStateCheckpointModel,
    )
    from src.shared.infrastructure.channels.base import BaseChannel

from src.core.context import set_tenant_id
from src.core.database import SessionLocal
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
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
from src.modules.sales_agent.infrastructure.db.repositories.business_repository import (
    BusinessRepository,
)
from src.modules.sales_agent.infrastructure.external.buffer_service import (
    SmartBufferService,
)
from src.modules.sales_agent.infrastructure.external.output_manager import OutputManager
from src.modules.sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)
from src.modules.sales_agent.infrastructure.prompts.semantic import check_is_complete
from src.modules.sales_agent.infrastructure.repositories.state_repository import (
    StateRepository,
)
from src.shared.domain.enums import ChannelType, IdentityType
from src.shared.domain.events import CHANNEL_TYPE_TO_CAPTURE_SLUG
from src.shared.domain.messages import IncomingMessage, OutgoingMessage
from src.shared.infrastructure.llm.factory import LLMFactory
from src.shared.links.ports.crm_repos import get_identity_service, get_lead_metrics_repository

logger = structlog.get_logger()


def merge_history_with_current(
    history: list[dict],
    sanitized_text: str,
    raw_text: str,
) -> list[dict]:
    """Combine persisted chat history with the current user turn.

    If the last history entry is a user message whose content matches either
    ``sanitized_text`` or ``raw_text``, it gets deduped (prevents double-logging
    when the current message was already persisted before this code runs).

    The input ``history`` list is never mutated.
    """
    merged = list(history)  # defensive copy — never mutate caller's list

    if merged and merged[-1].get("role") == "user":
        last_content = merged[-1].get("content", "")
        if last_content in (sanitized_text, raw_text):
            merged = merged[:-1]

    merged.append({"role": "user", "content": sanitized_text})
    return merged


class ChatOrchestrator:
    """Chat Orchestrator."""

    _instance = None

    def __new__(cls) -> Self:
        """Implement __new__."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize instance."""
        if self._initialized:
            return
        self.buffer_service = SmartBufferService()
        self._initialized = True

    async def handle_telegram_webhook(
        self,
        payload: dict,
        background_tasks: BackgroundTasks,
        tenant_id: str | None = None,
        db: Session = None,
    ) -> None:
        """Handle Telegram Webhook with Multi-Tenant support."""
        from src.shared.links.ports.calendar import get_channel_credentials
        from src.shared.links.ports.channel_adapter import create_telegram_adapter

        token = None
        if tenant_id and db:
            try:
                creds = get_channel_credentials(db, UUID(tenant_id), ChannelType.TELEGRAM.value)
                if creds:
                    token = creds.get("token")
            except Exception as e:
                logger.exception(
                    "error_resolving_telegram_connection",
                    error=str(e),
                    tenant_id=tenant_id,
                )

        # Instantiate adapter (with specific token or fallback to global env)
        adapter = create_telegram_adapter(token=token)
        await self.handle_incoming_webhook(
            adapter,
            payload,
            background_tasks,
            tenant_id,
        )

    async def handle_whatsapp_webhook(
        self,
        payload: dict,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Handle whatsapp webhook."""
        # WhatsApp logic is now handled via direct router-to-service calls or unified webhook handler.
        # This method is kept for backward compatibility but should be deprecated.

    async def handle_incoming_webhook(
        self,
        channel_adapter: BaseChannel,
        payload: dict,
        background_tasks: BackgroundTasks,
        tenant_id: str | None = None,
    ) -> None:
        """Normalize incoming webhook payload and buffer for smart debounce."""
        incoming = channel_adapter.normalize_payload(payload)
        if not incoming:
            return

        # Composite key for buffer to prevent collisions between tenants
        # If tenant_id is present, we store as "tenant_id:user_id"
        # We also inject tenant info into metadata for later recovery
        buffer_key = incoming.user_id
        if tenant_id:
            buffer_key = f"{tenant_id}:{incoming.user_id}"
            incoming.metadata["tenant_id"] = str(tenant_id)
            incoming.metadata["real_user_id"] = incoming.user_id

        # Add to buffer
        self.buffer_service.add_message(
            buffer_key,
            incoming.text,
            incoming.channel_type,
            incoming.metadata,
        )

        # Launch Smart Debounce Task
        background_tasks.add_task(self.smart_debounce_task, buffer_key, channel_adapter)

    async def smart_debounce_task(self, buffer_key: str, channel_adapter: BaseChannel) -> None:
        """Orchestrates the Dynamic Debounce logic."""
        try:
            # 1. Initial Buffer (Wait for fast interruptions)
            await asyncio.sleep(0.5)

            # 2. Check if new message arrived (Reset Logic)
            last_ts = self.buffer_service.get_last_timestamp(buffer_key)
            if time.time() - last_ts < 0.4:  # Tolerance
                # New message arrived recently, abort this task (let the new one handle it)
                return

            # Recover Metadata to get real user_id (for typing status)
            meta = self.buffer_service.get_metadata(buffer_key)
            real_user_id = meta.get("real_user_id", buffer_key)
            tenant_id = meta.get("tenant_id")

            # 3. Typing Indicator
            await channel_adapter.set_typing_status(real_user_id)

            # 3.5. Fetch tenant object for LLM service resolution
            tenant_obj = None
            if tenant_id:
                db_tmp = None
                try:
                    db_tmp = SessionLocal()
                    tenant_obj = (
                        db_tmp.execute(
                            select(TenantModel).where(
                                TenantModel.id == UUID(tenant_id),
                            ),
                        )
                        .scalars()
                        .first()
                    )
                except Exception as e:  # noqa: BLE001 — orchestrator resilience
                    logger.warning("Could not fetch tenant for semantic check", error=str(e))
                finally:
                    if db_tmp:
                        db_tmp.close()

            # 4. Semantic Check (LLM)
            # Peek buffer to check completeness
            messages = self.buffer_service.peek_buffer(buffer_key)
            if not messages:
                return

            full_text = " ".join(messages)

            # Only check semantic if it's substantial enough
            is_complete = False
            if len(full_text) > 5:
                is_complete = await check_is_complete(full_text, tenant=tenant_obj)

            # 5. Dynamic Wait (short if complete, long otherwise)
            wait_time = 4.0 if is_complete else 6.0

            await asyncio.sleep(wait_time)

            # 6. Final Reset Check & Lock
            # If a new message came during the semantic wait, we abort.
            last_ts = self.buffer_service.get_last_timestamp(buffer_key)
            # Using a small buffer for timing discrepancies
            if time.time() - last_ts < (wait_time + 0.3):
                return

            # Try Acquire Lock
            if not self.buffer_service.acquire_lock(buffer_key):
                return  # Already being processed

            try:
                # 7. Process
                msgs = self.buffer_service.get_and_clear_buffer(buffer_key)
                if not msgs:
                    return

                final_text = " ".join(msgs)
                # Re-fetch metadata just in case
                meta = self.buffer_service.get_metadata(buffer_key)
                channel_type = self.buffer_service.get_channel_type(buffer_key) or "unknown"

                # Reconstruct IncomingMessage with REAL user_id
                incoming = IncomingMessage(
                    user_id=real_user_id,
                    text=final_text,
                    channel_type=channel_type,
                    metadata=meta,
                )

                await self.process_chat_flow(channel_adapter, incoming, tenant_id)

            finally:
                self.buffer_service.release_lock(buffer_key)

        except Exception as e:
            logger.exception("Error in smart debounce task", error=str(e))

    # ── Helpers for process_chat_flow ──────────────────────────────────────

    @staticmethod
    def _fetch_tenant_config(db: Session, tenant_id: str) -> tuple[UUID | None, dict]:
        """Resolve tenant UUID and config dict from tenant_id string."""
        if not tenant_id:
            return None, {}
        try:
            tenant_uuid = UUID(tenant_id)
            tenant_obj = db.execute(select(TenantModel).where(TenantModel.id == tenant_uuid)).scalars().first()
            if tenant_obj:
                return tenant_uuid, tenant_obj.config_json or {}
        except Exception:
            logger.exception("Error fetching tenant config")
            return None, {}

        else:
            return tenant_uuid, {}

    @staticmethod
    def _resolve_customer(
        _db: Session,
        identity_service: IdentityService,
        incoming: IncomingMessage,
        tenant_uuid: UUID | None,
    ) -> tuple:
        """Resolve or create customer profile from incoming message.

        Returns (customer, was_created, capture_slug, channel_type, identity_type).
        """
        channel_type = incoming.channel_type
        try:
            identity_type = IdentityType(channel_type)
        except ValueError:
            identity_type = IdentityType.EXTERNAL_ID

        profile_data = {
            "first_name": incoming.metadata.get("first_name"),
            "last_name": incoming.metadata.get("last_name"),
            "traits": incoming.metadata,
        }

        capture_slug = CHANNEL_TYPE_TO_CAPTURE_SLUG.get(channel_type, channel_type)
        customer, was_created = identity_service.get_or_create_customer(
            tenant_id=tenant_uuid,
            identity_type=identity_type,
            identity_value=incoming.user_id,
            profile_data=profile_data,
            lead_source=capture_slug,
            lead_source_detail=channel_type,
        )
        return customer, was_created, capture_slug, channel_type, identity_type

    @staticmethod
    async def _enrich_instagram_profile(
        db: Session,
        tenant_uuid: UUID,
        user_id_str: str,
        customer: CustomerProfileModel,
        was_created: bool,
    ) -> None:
        """Enrich Instagram profile with name/username/pic from User Profile API."""
        if not (was_created or not (customer.traits or {}).get("instagram_username")):
            return
        try:
            from src.shared.links.ports.channel_adapter import create_connection_port
            from src.shared.links.ports.crm_repos import get_ig_profile_enricher

            connection_port = create_connection_port(db)
            creds = await connection_port.get_credentials(tenant_uuid, "meta")
            enricher = get_ig_profile_enricher(db)
            await enricher.enrich(
                tenant_id=tenant_uuid,
                igsid=user_id_str,
                customer_profile_id=customer.id,
                access_token=creds.credentials.get("access_token", ""),
            )
        except Exception:  # noqa: BLE001 — orchestrator resilience
            logger.warning("ig_profile_enrichment_failed", exc_info=True)

    @staticmethod
    def _track_message_event(
        db: Session,
        tenant_uuid: UUID,
        customer: CustomerProfileModel,
        capture_slug: str,
        channel_type: str,
        incoming: IncomingMessage,
    ) -> None:
        """Track ``message_received`` journey event. Delegates to AuditEmitter (S11B)."""
        AuditEmitter.track_message_received(
            db,
            tenant_uuid,
            customer,
            capture_slug,
            channel_type,
            incoming,
        )

    @staticmethod
    def _update_customer_traits(
        db: Session,
        customer: CustomerProfileModel,
        incoming: IncomingMessage,
    ) -> None:
        """Update customer profile traits from incoming message metadata."""
        if not incoming.metadata:
            return
        current_traits = dict(customer.traits) if customer.traits else {}
        needs_update = False
        for k, v in incoming.metadata.items():
            if k not in current_traits or current_traits[k] != v:
                current_traits[k] = v
                needs_update = True

        if not needs_update:
            return

        from src.shared.infrastructure.models.crm import CustomerProfileModel

        profile_model = (
            db.execute(
                select(CustomerProfileModel).where(
                    CustomerProfileModel.id == customer.id,
                ),
            )
            .scalars()
            .first()
        )
        if profile_model:
            profile_model.traits = current_traits
            if "first_name" in incoming.metadata:
                profile_model.full_name = (
                    f"{incoming.metadata.get('first_name', '')} {incoming.metadata.get('last_name', '')}".strip()
                )
            db.commit()

    @staticmethod
    async def _handle_human_mode(
        db: Session,
        checkpoint: AgentStateCheckpointModel | None,
        user: LeadModel,
        tenant_uuid: UUID | None,
        tenant_id: str | None,
        incoming: IncomingMessage,
    ) -> bool:
        """Handle human handler_mode: increment unread, emit WS, return True to skip AI."""
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

    @staticmethod
    def _determine_session_state(audit_repo: AuditRepository, user: LeadModel) -> dict:
        """Determine session state from last message. Returns dict with state fields."""
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
    def _build_checkpoint_data(
        checkpoint: AgentStateCheckpointModel | None,
        session_active: bool,
        history: list,
        base_profile: dict,
        state_repo: StateRepository,
        tenant_uuid: UUID | None,
        user: LeadModel,
    ) -> tuple[dict, str | None]:
        """Build checkpoint_data dict and last_session_summary from checkpoint state."""
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
                last_session_summary = (checkpoint.lead_data or {}).get(
                    "session_summary",
                )
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
                        logger.warning(
                            "session_summary_generation_failed",
                            error=str(e),
                        )
            state_repo.deactivate(tenant_uuid, user.id)

        return checkpoint_data, last_session_summary

    @staticmethod
    def _build_user_profile(user: LeadModel) -> dict:
        """Build base profile dict from user's profile_data + style fields."""
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

    @staticmethod
    async def _sanitize_text(text: str, direction: str = "input") -> str:
        """Sanitize text through SafetyLayerService. Returns original on failure."""
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

        else:
            return sanitized

    @staticmethod
    def _save_checkpoint(
        db: Session,
        state_repo: StateRepository,
        tenant_uuid: UUID,
        user: LeadModel,
        customer: CustomerProfileModel,
        channel_type: str,
        initial_state: dict,
        result: dict,
        last_session_summary: str | None,
    ) -> None:
        """Persist agent state checkpoint after graph execution."""
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
    async def _emit_assistant_ws_event(
        tenant_uuid: UUID,
        user: LeadModel,
        bot_text: str,
        result: dict,
    ) -> None:
        """Emit WS event for Closer Studio. Delegates to AuditEmitter (S11B)."""
        await AuditEmitter.emit_assistant_message(tenant_uuid, user, bot_text, result)

    # ── Additional helpers for process_chat_flow ─────────────────────────

    async def _process_customer_lifecycle(
        self,
        db: Session,
        identity_service: IdentityService,
        incoming: IncomingMessage,
        tenant_uuid: UUID | None,
    ) -> tuple:
        """Handle customer resolution, enrichment, events, and trait updates.

        Returns (customer, was_created, capture_slug, channel_type, user_id_str).
        """
        customer, was_created, capture_slug, channel_type, _ = self._resolve_customer(
            db,
            identity_service,
            incoming,
            tenant_uuid,
        )

        if channel_type == "instagram" and tenant_uuid:
            await self._enrich_instagram_profile(
                db,
                tenant_uuid,
                incoming.user_id,
                customer,
                was_created,
            )

        if tenant_uuid:
            self._track_message_event(
                db,
                tenant_uuid,
                customer,
                capture_slug,
                channel_type,
                incoming,
            )
        if was_created and tenant_uuid:
            AuditEmitter.publish_lead_captured(
                db,
                tenant_uuid,
                customer,
                capture_slug,
                channel_type,
            )

        self._update_customer_traits(db, customer, incoming)
        return customer, was_created, capture_slug, channel_type

    @staticmethod
    def _build_agent_identity(db: Session, tenant_uuid: UUID | None) -> str | None:
        """Build agent identity string, rolling back on failure."""
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
    def _build_brand_voice(db: Session, tenant_uuid: UUID | None) -> str | None:
        """Build slot 5 BRAND_VOICE block (S7) for this tenant.

        Loads the active PersonalityProfile.system_instruction (compiled by
        Brand Studio "Estilo Comunicacional") with legacy voice_tone fallback.
        Returns None when neither configured. Best-effort: never crashes the
        request. See ``.claude/rules/sales-agent-brand-voice.md``.
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

    def _build_initial_state(
        self,
        *,
        db: Session,
        biz_repo: BusinessRepository,
        audit_repo: AuditRepository,
        user: LeadModel,
        customer: CustomerProfileModel,
        tenant_id: str | None,
        tenant_uuid: UUID | None,
        tenant_config: dict,
        incoming: IncomingMessage,
        session_state: dict,
        agent_identity: str | None,
        brand_voice: str | None,
        checkpoint: AgentStateCheckpointModel | None,
        state_repo: StateRepository,
    ) -> tuple[dict, str | None]:
        """Prepare the initial agent state dict. Returns (initial_state, last_session_summary)."""
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

        base_profile = self._build_user_profile(user)
        checkpoint_data, last_session_summary = self._build_checkpoint_data(
            checkpoint,
            session_state["session_active"],
            history,
            base_profile,
            state_repo,
            tenant_uuid,
            user,
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

    async def _prepare_messages_and_intent(
        self,
        incoming: IncomingMessage,
        initial_state: dict,
        checkpoint: AgentStateCheckpointModel | None,
        db: Session,
        tenant_uuid: UUID | None,
    ) -> None:
        """Sanitize input, inject messages, detect intent, and apply resume_objective."""
        sanitized_text = await self._sanitize_text(incoming.text, "user_input")
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

    async def _invoke_agent_with_typing(
        self,
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        initial_state: dict,
        observability_handler: object | None = None,
    ) -> dict:
        """Invoke the agent graph while sending periodic typing indicators.

        ``observability_handler`` is forwarded as a LangChain callback so
        every node + LLM + tool invocation is captured into
        ``sales_agent_llm_call`` / ``sales_agent_trace_event``. Best-effort —
        if ``None`` the graph still runs (legacy ``@trace_node`` keeps
        writing during the dual-write window).
        """

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

    async def _deliver_response(
        self,
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        result: dict,
        audit_repo: AuditRepository,
        user: LeadModel,
        channel_type: str,
        tenant_uuid: UUID | None,
    ) -> None:
        """Extract, sanitize, log, and send the agent response."""
        last_msg = result["messages"][-1]
        bot_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
        bot_text = await self._sanitize_text(bot_text, "bot_output")

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
            await self._emit_assistant_ws_event(tenant_uuid, user, bot_text, result)

    # ── Main flow ──────────────────────────────────────────────────────────

    @staticmethod
    def _init_repos(db: Session) -> tuple:
        """Initialize all repositories needed for chat flow.

        Returns (lead_repo, identity_service, audit_repo, biz_repo).
        """
        lead_repo = get_lead_metrics_repository(db)
        identity_service = get_identity_service(db)
        audit_repo = AuditRepository(db)
        biz_repo = BusinessRepository(db)
        return lead_repo, identity_service, audit_repo, biz_repo

    @staticmethod
    def _load_checkpoint(
        db: Session,
        state_repo: StateRepository,
        tenant_uuid: UUID | None,
        user_id: UUID,
    ) -> AgentStateCheckpointModel | None:
        """Load active checkpoint, rolling back on failure."""
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
    def _resolve_lead(lead_repo: LeadRepository, customer_id: UUID, channel_type: str, user_id_str: str) -> LeadModel:
        """Get or create active lead for customer."""
        user = lead_repo.get_active_lead(customer_id)
        if not user:
            user = lead_repo.create_lead(
                customer_id=customer_id,
                channel=channel_type,
                channel_user_id=user_id_str,
            )
        return user

    async def process_chat_flow(
        self,
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        tenant_id: str | None = None,
    ) -> None:
        """Core Logic: Ejecuta el agente con un mensaje YA CONSTRUIDO (y debounced)."""
        if tenant_id:
            try:
                set_tenant_id(UUID(tenant_id))
            except Exception:
                logger.exception("Invalid tenant_id format", tenant_id=tenant_id)

        try:
            await channel_adapter.set_typing_status(incoming.user_id)
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("Could not set typing status in flow", error=str(e))

        db = SessionLocal()
        lead_repo, identity_service, audit_repo, biz_repo = self._init_repos(db)

        try:
            tenant_uuid, tenant_config = self._fetch_tenant_config(db, tenant_id)
            (
                customer,
                _,
                _capture_slug,
                channel_type,
            ) = await self._process_customer_lifecycle(
                db,
                identity_service,
                incoming,
                tenant_uuid,
            )

            user = self._resolve_lead(
                lead_repo,
                customer.id,
                channel_type,
                incoming.user_id,
            )
            audit_repo.log_message(
                user_id=user.id,
                role="user",
                content=incoming.text,
                channel=channel_type,
                tenant_id=tenant_uuid,
            )

            state_repo = StateRepository(db)
            checkpoint = self._load_checkpoint(db, state_repo, tenant_uuid, user.id)

            if await self._handle_human_mode(
                db,
                checkpoint,
                user,
                tenant_uuid,
                tenant_id,
                incoming,
            ):
                return

            session_state = self._determine_session_state(audit_repo, user)
            agent_identity = self._build_agent_identity(db, tenant_uuid)
            brand_voice = self._build_brand_voice(db, tenant_uuid)

            initial_state, last_session_summary = self._build_initial_state(
                db=db,
                biz_repo=biz_repo,
                audit_repo=audit_repo,
                user=user,
                customer=customer,
                tenant_id=tenant_id,
                tenant_uuid=tenant_uuid,
                tenant_config=tenant_config,
                incoming=incoming,
                session_state=session_state,
                agent_identity=agent_identity,
                brand_voice=brand_voice,
                checkpoint=checkpoint,
                state_repo=state_repo,
            )

            await self._prepare_messages_and_intent(
                incoming,
                initial_state,
                checkpoint,
                db,
                tenant_uuid,
            )

            # Build per-turn observability handler (S1). Best-effort —
            # ``None`` when tenant/lead is missing; legacy ``@trace_node``
            # still writes during the dual-write window.
            from src.modules.sales_agent.application.orchestrator.tool_call_dedup import (
                ToolCallDedupTracker,
            )
            from src.modules.sales_agent.observability.recording.factory import (
                build_sales_agent_callback_handler,
            )

            observability_handler = build_sales_agent_callback_handler(
                db=db,
                tenant_id=tenant_uuid,
                lead_id=user.id if user else None,
                channel_type=channel_type,
                turn_id=uuid.uuid4(),
            )

            # Seed the tool-call dedup tracker for this turn.
            # ``node_tool_executor`` reads it from state via the standard
            # AgentState dict — LangGraph propagates the seeded value
            # alongside the normal state mutations.
            initial_state["_tool_dedup_tracker"] = ToolCallDedupTracker()

            result = await self._invoke_agent_with_typing(
                channel_adapter,
                incoming,
                initial_state,
                observability_handler=observability_handler,
            )

            if tenant_uuid and user:
                self._save_checkpoint(
                    db,
                    state_repo,
                    tenant_uuid,
                    user,
                    customer,
                    channel_type,
                    initial_state,
                    result,
                    last_session_summary,
                )

            await self._deliver_response(
                channel_adapter,
                incoming,
                result,
                audit_repo,
                user,
                channel_type,
                tenant_uuid,
            )

        except Exception as e:
            logger.exception("Error processing message", error=str(e))
            try:
                if incoming and incoming.user_id:
                    error_msg = OutgoingMessage(
                        user_id=incoming.user_id,
                        text="Lo siento, ocurrio un error tecnico interno.",
                    )
                    await channel_adapter.send_message(error_msg)
            except Exception:
                logger.exception("Could not send fallback error message")

        finally:
            lead_repo.close()
            audit_repo.close()
            biz_repo.close()
