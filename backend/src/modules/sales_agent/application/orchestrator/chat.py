"""Chat application module."""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
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
from src.modules.sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)
from src.modules.sales_agent.application.orchestrator.identity_resolver import (
    IdentityResolver,
)
from src.modules.sales_agent.infrastructure.db.repositories.business_repository import (
    BusinessRepository,
)
from src.modules.sales_agent.infrastructure.external.buffer_service import (
    SmartBufferService,
)
from src.modules.sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)
from src.modules.sales_agent.infrastructure.prompts.semantic import check_is_complete
from src.modules.sales_agent.infrastructure.repositories.state_repository import (
    StateRepository,
)
from src.shared.domain.enums import ChannelType
from src.shared.domain.messages import IncomingMessage, OutgoingMessage
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
        """Delegate to ConversationPipeline (S11B)."""
        return ConversationPipeline.fetch_tenant_config(db, tenant_id)

    @staticmethod
    def _resolve_customer(
        _db: Session,
        identity_service: IdentityService,
        incoming: IncomingMessage,
        tenant_uuid: UUID | None,
    ) -> tuple:
        """Delegate to IdentityResolver (S11B)."""
        return IdentityResolver.resolve_customer(identity_service, incoming, tenant_uuid)

    @staticmethod
    async def _enrich_instagram_profile(
        db: Session,
        tenant_uuid: UUID,
        user_id_str: str,
        customer: CustomerProfileModel,
        was_created: bool,
    ) -> None:
        """Delegate to IdentityResolver (S11B)."""
        await IdentityResolver.enrich_instagram_profile(
            db,
            tenant_uuid,
            user_id_str,
            customer,
            was_created,
        )

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
        """Delegate to IdentityResolver (S11B)."""
        IdentityResolver.update_customer_traits(db, customer, incoming)

    @staticmethod
    async def _handle_human_mode(
        db: Session,
        checkpoint: AgentStateCheckpointModel | None,
        user: LeadModel,
        tenant_uuid: UUID | None,
        tenant_id: str | None,
        incoming: IncomingMessage,
    ) -> bool:
        """Delegate to ConversationPipeline (S11B)."""
        return await ConversationPipeline.handle_human_mode(
            db,
            checkpoint,
            user,
            tenant_uuid,
            tenant_id,
            incoming,
        )

    @staticmethod
    def _determine_session_state(audit_repo: AuditRepository, user: LeadModel) -> dict:
        """Delegate to ConversationPipeline (S11B)."""
        return ConversationPipeline.determine_session_state(audit_repo, user)

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
        """Delegate to ConversationPipeline (S11B)."""
        return ConversationPipeline.build_checkpoint_data(
            checkpoint,
            session_active,
            history,
            base_profile,
            state_repo,
            tenant_uuid,
            user,
        )

    @staticmethod
    def _build_user_profile(user: LeadModel) -> dict:
        """Delegate to ConversationPipeline (S11B)."""
        return ConversationPipeline.build_user_profile(user)

    @staticmethod
    async def _sanitize_text(text: str, direction: str = "input") -> str:
        """Delegate to ConversationPipeline (S11B)."""
        return await ConversationPipeline.sanitize_text(text, direction)

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
        """Delegate to ConversationPipeline (S11B)."""
        ConversationPipeline.save_checkpoint(
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
        """Delegate to IdentityResolver (S11B)."""
        return await IdentityResolver.process_customer_lifecycle(
            db,
            identity_service,
            incoming,
            tenant_uuid,
        )

    @staticmethod
    def _build_agent_identity(db: Session, tenant_uuid: UUID | None) -> str | None:
        """Delegate to ConversationPipeline (S11B)."""
        return ConversationPipeline.build_agent_identity(db, tenant_uuid)

    @staticmethod
    def _build_brand_voice(db: Session, tenant_uuid: UUID | None) -> str | None:
        """Delegate to ConversationPipeline (S11B). See ``.claude/rules/sales-agent-brand-voice.md``."""
        return ConversationPipeline.build_brand_voice(db, tenant_uuid)

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
        """Delegate to ConversationPipeline (S11B)."""
        return ConversationPipeline.build_initial_state(
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

    async def _prepare_messages_and_intent(
        self,
        incoming: IncomingMessage,
        initial_state: dict,
        checkpoint: AgentStateCheckpointModel | None,
        db: Session,
        tenant_uuid: UUID | None,
    ) -> None:
        """Delegate to ConversationPipeline (S11B)."""
        await ConversationPipeline.prepare_messages_and_intent(
            incoming,
            initial_state,
            checkpoint,
            db,
            tenant_uuid,
        )

    async def _invoke_agent_with_typing(
        self,
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        initial_state: dict,
        observability_handler: object | None = None,
    ) -> dict:
        """Delegate to ConversationPipeline (S11B)."""
        return await ConversationPipeline.invoke_agent_with_typing(
            channel_adapter,
            incoming,
            initial_state,
            observability_handler,
        )

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
        """Delegate to ConversationPipeline (S11B)."""
        await ConversationPipeline.deliver_response(
            channel_adapter,
            incoming,
            result,
            audit_repo,
            user,
            channel_type,
            tenant_uuid,
        )

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
        """Delegate to IdentityResolver (S11B)."""
        return IdentityResolver.resolve_lead(lead_repo, customer_id, channel_type, user_id_str)

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
