"""Chat application module."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Self
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from fastapi import BackgroundTasks
    from luana_core_platform.infrastructure.channels.base import BaseChannel
    from sqlalchemy.orm import Session

from luana_core_platform.core.context import set_tenant_id
from luana_core_platform.core.database import SessionLocal
from luana_core_platform.domain.enums import ChannelType
from luana_core_platform.domain.messages import IncomingMessage, OutgoingMessage
from luana_core_platform.links.ports.crm_repos import get_identity_service, get_lead_metrics_repository
from luana_core_sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)
from luana_core_sales_agent.application.orchestrator.identity_resolver import (
    IdentityResolver,
)
from luana_core_sales_agent.application.orchestrator.smart_debounce_runner import (
    run_smart_debounce,
)
from luana_core_sales_agent.infrastructure.db.repositories.business_repository import (
    BusinessRepository,
)
from luana_core_sales_agent.infrastructure.external.buffer_service import (
    SmartBufferService,
)
from luana_core_sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)
from luana_core_sales_agent.infrastructure.repositories.state_repository import (
    StateRepository,
)

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
        from luana_core_platform.links.ports.calendar import get_channel_credentials
        from luana_core_platform.links.ports.channel_adapter import create_telegram_adapter

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
        """Run the §3-protected debounce loop. Delegates to ``run_smart_debounce``."""
        await run_smart_debounce(
            buffer_service=self.buffer_service,
            buffer_key=buffer_key,
            channel_adapter=channel_adapter,
            on_complete=self.process_chat_flow,
        )

    # ── Main flow ──────────────────────────────────────────────────────────

    @staticmethod
    def _init_repos(db: Session) -> tuple:
        """Build the four repositories used by ``process_chat_flow``.

        Returns ``(lead_repo, identity_service, audit_repo, biz_repo)``.
        """
        lead_repo = get_lead_metrics_repository(db)
        identity_service = get_identity_service(db)
        audit_repo = AuditRepository(db)
        biz_repo = BusinessRepository(db)
        return lead_repo, identity_service, audit_repo, biz_repo

    async def process_chat_flow(  # noqa: PLR0915 — orchestrator composition (S11B carve-out + PR-8 inbound recognition)
        self,
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        tenant_id: str | None = None,
    ) -> None:
        """Run one chat turn: resolve identity, build state, dispatch, deliver.

        Composes :class:`IdentityResolver` (S11B step 2),
        :class:`ConversationPipeline` (S11B step 3) and the per-turn
        observability handler. The orchestrator owns nothing but the
        composition order + the SessionLocal lifecycle.
        """
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
            tenant_uuid, tenant_config = ConversationPipeline.fetch_tenant_config(db, tenant_id)
            customer, _, _capture_slug, channel_type = await IdentityResolver.process_customer_lifecycle(
                db,
                identity_service,
                incoming,
                tenant_uuid,
            )

            user = IdentityResolver.resolve_lead(
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

            # PR-8: reconocimiento inbound de campaña (best-effort, fail-open).
            # Busca la campaign_task SENT más reciente para este lead dentro de la ventana.
            # En hit: inyecta campaign_id en initial_state (outbound_mode=False — slot 7 ausente).
            inbound_campaign_id: UUID | None = None
            try:
                from luana_core_platform.core.config import settings as _cfg
                from luana_core_platform.core.database import get_async_session_factory
                from luana_core_platform.links.ports.campaigns import create_campaigns_lookup_port

                _port = create_campaigns_lookup_port()
                async with get_async_session_factory()() as _a_session:
                    _hit = await _port.find_recent_campaign_task_for_lead(
                        tenant_id=tenant_uuid,
                        lead_id=user.id,
                        window_hours=_cfg.CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS,
                        session=_a_session,
                    )
                if _hit is not None:
                    inbound_campaign_id = _hit.campaign_id
                    logger.info(
                        "inbound_campaign_recognized",
                        tenant_id=str(tenant_uuid),
                        lead_id=str(user.id),
                        campaign_id=str(_hit.campaign_id),
                        sent_at=_hit.sent_at.isoformat(),
                    )
            except Exception as _exc:  # noqa: BLE001 — agent resilience pattern (chat.py:208)
                logger.warning(
                    "inbound_campaign_lookup_failed",
                    tenant_id=str(tenant_uuid) if tenant_uuid else None,
                    lead_id=str(user.id) if user else None,
                    error=str(_exc),
                )

            state_repo = StateRepository(db)
            checkpoint = ConversationPipeline.load_checkpoint(db, state_repo, tenant_uuid, user.id)

            if await ConversationPipeline.handle_human_mode(
                db,
                checkpoint,
                user,
                tenant_uuid,
                tenant_id,
                incoming,
            ):
                return

            session_state = ConversationPipeline.determine_session_state(audit_repo, user)
            agent_identity = ConversationPipeline.build_agent_identity(db, tenant_uuid)
            brand_voice = ConversationPipeline.build_brand_voice(db, tenant_uuid)

            initial_state, last_session_summary = ConversationPipeline.build_initial_state(
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
                # PR-8: inbound recognition — campaign_id inyectado, outbound_mode=False
                # (slot 7 CAMPAIGN_CONTEXT permanece ausente — compose.py guarda outbound_mode).
                campaign_id=inbound_campaign_id,
                outbound_mode=False,
            )

            await ConversationPipeline.prepare_messages_and_intent(
                incoming,
                initial_state,
                checkpoint,
                db,
                tenant_uuid,
            )

            # Per-turn observability context (S1 + PR-2 Bug #2 fix). Best-effort —
            # ``None`` when tenant/lead is missing; legacy ``@trace_node`` still
            # writes during the dual-write window.
            #
            # PR-2 PI-1.1: the envelope wraps ``ainvoke`` in
            # ``async with observe_turn(...)`` so ``turn_start`` +
            # ``turn_end`` rows persist on ``sales_agent_trace_event``.
            # Pre-PR-2 only the callback handler ran, so turns without
            # an LLM call (rare but real) wrote zero rows.
            from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
                ToolCallDedupTracker,
            )
            from luana_core_sales_agent.observability.recording.factory import (
                build_sales_agent_observability_context,
            )

            observability_context = build_sales_agent_observability_context(
                db=db,
                tenant_id=tenant_uuid,
                lead_id=user.id if user else None,
                channel_type=channel_type,
                turn_id=uuid.uuid4(),
            )

            # Seed the tool-call dedup tracker for this turn — ``node_tool_executor``
            # reads it from state and LangGraph propagates the seeded value.
            initial_state["_tool_dedup_tracker"] = ToolCallDedupTracker()

            result = await ConversationPipeline.invoke_agent_with_typing(
                channel_adapter,
                incoming,
                initial_state,
                observability_context=observability_context,
            )

            if tenant_uuid and user:
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

            await ConversationPipeline.deliver_response(
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
