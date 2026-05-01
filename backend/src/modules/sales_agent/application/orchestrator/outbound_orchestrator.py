"""OutboundOrchestrator — outbound campaign dispatch via sales_agent.

Static class paralelo a :class:`ChatOrchestrator` (S11B). Reusa
:class:`ConversationPipeline` helpers (fetch_tenant_config /
load_checkpoint / build_agent_identity / build_brand_voice /
build_initial_state / save_checkpoint / sanitize_text) + ``agent_app``
LangGraph + slot system v2 (compose.py with slot 7 CAMPAIGN_CONTEXT) +
voice SSoT (PersonalityProfile.system_instruction).

Boundary: invoked by ``SalesAgentAdapter`` (campaigns/infrastructure/
external/), which is invoked by ``execution_task.py`` ARQ worker for
campaign steps with ``step_type=CALL_SUBAGENT_BRIEF``. NO webhook
entry — outbound is cron-driven.

Continuity invariant: if a checkpoint is already active for
``(tenant, lead)``, REUSE it via ``ConversationPipeline.load_checkpoint``
— do NOT create a parallel session (avoids dual-conversation drift).

Best-effort observability: every audit / WS / persist write is wrapped
in ``contextlib.suppress(Exception)`` + structlog warning so a downstream
infra failure (Closer Studio WS down, audit DB locked, etc.) cannot
abort the user-visible send. The graph invocation itself is the only
surface where a failure aborts the turn (returns
``error_code='graph_invocation_failed'``).

# [SALES-AGENT-OUTBOUND-PR7] -> docs/pm-nico/pis/active/PI-1-campaigns-module/
#                                sprints/S3-mvp-telegram/prs/PR-7-outbound-orchestrator/CONTRACT.md
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.sales_agent.application.orchestrator.audit_emitter import AuditEmitter
from src.modules.sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)
from src.modules.sales_agent.application.orchestrator.graph import agent_app
from src.modules.sales_agent.observability.recording.factory import (
    build_sales_agent_observability_context,
)
from src.shared.domain.messages import IncomingMessage

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.shared.billing.application.budget_guard import BudgetGuard
    from src.shared.infrastructure.channels.base import BaseChannel

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OutboundResult:
    """Result of an outbound campaign send.

    Returned to ``SalesAgentAdapter``, which translates it to a
    ``ChannelSendResult`` for the ARQ worker.
    """

    success: bool
    tenant_id: UUID
    lead_id: UUID
    campaign_id: UUID
    session_id: str
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    voice_fidelity_score: float | None = None  # populated by Sub-I golden test path


class OutboundOrchestrator:
    """Static class — single async entrypoint :meth:`send_outbound`."""

    @staticmethod
    async def _invoke_graph_with_envelope(
        *,
        observability_ctx: object | None,
        initial_state: dict,
        campaign_id: UUID,
        tenant_uuid: UUID,
        lead_id: UUID,
    ) -> tuple[dict, str | None]:
        """Run ``agent_app.ainvoke`` inside the observability envelope.

        Returns ``(result, error_message)``. ``error_message`` is non-None
        only when the graph invocation raised — the caller maps that to
        ``OutboundResult(error_code='graph_invocation_failed')``.

        Without ``observability_ctx`` (tenant/lead missing) we run a raw
        ``ainvoke`` — the legacy degraded path.
        """
        from src.modules.sales_agent.observability.recording.turn_envelope import (
            SalesAgentObservabilityContext,
        )

        if not isinstance(observability_ctx, SalesAgentObservabilityContext):
            try:
                result = await agent_app.ainvoke(initial_state, config={})
            except Exception as exc:
                logger.exception(
                    "outbound_orchestrator_graph_failed",
                    tenant_id=str(tenant_uuid),
                    lead_id=str(lead_id),
                    campaign_id=str(campaign_id),
                )
                return {}, str(exc)
            return result, None

        # Envelope present — bracket the invocation so trace rows commit.
        async with observability_ctx.observe_turn(
            message="[OUTBOUND_TRIGGER]",
            route="outbound",
            attachments=[],
        ):
            try:
                result = await agent_app.ainvoke(
                    initial_state,
                    config=observability_ctx.langchain_config(),
                )
            except Exception as exc:
                observability_ctx.set_turn_error(
                    error_kind="graph_invocation_failed",
                    error_message=str(exc),
                )
                logger.exception(
                    "outbound_orchestrator_graph_failed",
                    tenant_id=str(tenant_uuid),
                    lead_id=str(lead_id),
                    campaign_id=str(campaign_id),
                )
                # Return so the envelope's ``__aexit__`` can finalize the
                # turn_end row with status='error'. The caller's check on
                # ``graph_error`` short-circuits to the OutboundResult.
                return {}, str(exc)

            # Stash stream-shape totals BEFORE the envelope's ``__aexit__``
            # writes ``turn_end``, so the row carries actual values
            # instead of zeros (PR-1 hotfix Bug #2 iter 2 — F2).
            # Best-effort: any error here is logged + swallowed; the
            # envelope still finalizes turn_end cleanly via the
            # ``async with`` exit.
            try:
                messages = result.get("messages", []) if isinstance(result, dict) else []
                last_msg = messages[-1] if messages else {}
                last_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
                observability_ctx.set_turn_summary(
                    response_length=len(last_text or ""),
                    message_count=len(messages),
                    block_count=0,
                )
            except Exception as exc:  # noqa: BLE001 — best-effort
                logger.warning(
                    "outbound_obs_set_turn_summary_failed",
                    error=str(exc),
                )
        return result, None

    @staticmethod
    async def send_outbound(
        *,
        db: Session,
        tenant_id: UUID,
        lead_id: UUID,
        campaign_id: UUID,
        campaign_instructions: str,
        channel_type: str,
        channel_adapter: BaseChannel,
        budget_guard: BudgetGuard | None = None,
        idempotency_key: str | None = None,  # noqa: ARG004 — reserved for adapter caller
    ) -> OutboundResult:
        """Run one outbound turn through the sales_agent LangGraph.

        Steps (mirrors ChatOrchestrator inbound pattern):

        1. Resolve tenant config + UUID via ``fetch_tenant_config``.
        2. Resolve ``LeadModel`` row tenant-scoped.
        3. Load checkpoint — if active, REUSE (continuity invariant).
        4. Build agent_identity (slot 4) + brand_voice (slot 5).
        5. Build initial AgentState with ``outbound_mode=True`` +
           ``campaign_id`` + ``campaign_instructions`` (slot 7).
        6. Build callback handler (best-effort observability).
        7. ``await agent_app.ainvoke(state, config={callbacks: [...]})``.
        8. Save checkpoint.
        9. Deliver via ``OutputManager.process_response``.
        10. Emit Closer Studio WS audit event.

        Returns:
            ``OutboundResult`` with ``success`` flag + structured error
            codes for failure modes (``tenant_not_found``,
            ``lead_not_found``, ``graph_invocation_failed``,
            ``empty_response``, ``channel_send_failed``).
        """
        from sqlalchemy import select

        from src.modules.sales_agent.infrastructure.db.repositories.business_repository import (
            BusinessRepository,
        )
        from src.modules.sales_agent.infrastructure.memory.audit_repository import (
            AuditRepository,
        )
        from src.modules.sales_agent.infrastructure.repositories.state_repository import (
            StateRepository,
        )
        from src.shared.infrastructure.models.crm import LeadModel

        # --- Step 1: tenant config ---
        tenant_uuid, tenant_config = ConversationPipeline.fetch_tenant_config(db, str(tenant_id))
        if tenant_uuid is None:
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_id,
                campaign_id=campaign_id,
                session_id="",
                error_code="tenant_not_found",
            )

        # --- Step 2: lead lookup (tenant-scoped) ---
        lead_row = (
            db.execute(
                select(LeadModel).where(
                    LeadModel.id == lead_id,
                    LeadModel.tenant_id == tenant_uuid,
                ),
            )
            .scalars()
            .first()
        )
        if lead_row is None:
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_id,
                campaign_id=campaign_id,
                session_id="",
                error_code="lead_not_found",
            )

        # --- Repos (same instances ChatOrchestrator uses) ---
        audit_repo = AuditRepository(db)
        state_repo = StateRepository(db)
        biz_repo = BusinessRepository(db)
        customer = lead_row.customer  # may be None — biz_repo handles

        # --- Step 3: checkpoint continuity ---
        checkpoint = ConversationPipeline.load_checkpoint(db, state_repo, tenant_uuid, lead_row.id)

        # --- Step 4: identity + voice (slots 4-5) ---
        agent_identity = ConversationPipeline.build_agent_identity(db, tenant_uuid)
        brand_voice = ConversationPipeline.build_brand_voice(db, tenant_uuid)

        # --- Session state: outbound first turn = always 'new' (no last_msg) ---
        session_state = {
            "session_active": True,
            "last_intent": None,
            "session_gap_hours": None,
            "is_returning_user": checkpoint is not None,
        }

        # --- Step 5: synthetic IncomingMessage (no real webhook) ---
        synthetic_incoming = IncomingMessage(
            user_id=str(lead_row.id),
            text="",
            channel_type=channel_type,
            metadata={},
        )

        # --- Build initial AgentState with outbound flags ---
        initial_state, last_session_summary = ConversationPipeline.build_initial_state(
            db=db,
            biz_repo=biz_repo,
            audit_repo=audit_repo,
            user=lead_row,
            customer=customer,
            tenant_id=str(tenant_uuid),
            tenant_uuid=tenant_uuid,
            tenant_config=tenant_config,
            incoming=synthetic_incoming,
            session_state=session_state,
            agent_identity=agent_identity,
            brand_voice=brand_voice,
            checkpoint=checkpoint,
            state_repo=state_repo,
            budget_guard=budget_guard,
            # PR-7: outbound additive
            campaign_id=campaign_id,
            campaign_instructions=campaign_instructions,
            outbound_mode=True,
        )

        # First-turn outbound: no user message — supervisor + closer compose
        # opener directly. Inject synthetic system trigger so the graph has
        # a starting message envelope.
        initial_state["messages"] = [
            {
                "role": "system",
                "content": "[OUTBOUND_TRIGGER] Apertura outbound — el usuario aún no respondió.",
            },
        ]

        # --- Step 6: observability envelope (PR-1 hotfix Bug #2) ---
        # Bracket the turn so ``turn_start`` / ``turn_end`` rows are
        # committed to ``sales_agent_trace_event`` and every callback row
        # added during ``ainvoke`` is flushed. Without the envelope the
        # callback ``session.add(...)`` calls pile up uncommitted in the
        # orchestrator session and get discarded when ``db`` closes (see
        # ``IMPL-LOG-agentic.md`` RCA).
        observability_ctx = build_sales_agent_observability_context(
            db=db,
            tenant_id=tenant_uuid,
            lead_id=lead_row.id,
            channel_type=channel_type,
            role="agent",
        )

        # --- Step 7: dispatch via LangGraph (inside envelope) ---
        result, graph_error = await OutboundOrchestrator._invoke_graph_with_envelope(
            observability_ctx=observability_ctx,
            initial_state=initial_state,
            campaign_id=campaign_id,
            tenant_uuid=tenant_uuid,
            lead_id=lead_row.id,
        )
        if graph_error is not None:
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_row.id,
                campaign_id=campaign_id,
                session_id=initial_state.get("session_id", ""),
                error_code="graph_invocation_failed",
                error_message=graph_error,
            )

        # --- Step 8: persist checkpoint ---
        try:
            ConversationPipeline.save_checkpoint(
                db,
                state_repo,
                tenant_uuid,
                lead_row,
                customer,
                channel_type,
                initial_state,
                result,
                last_session_summary,
            )
        except Exception:
            logger.exception(
                "outbound_orchestrator_checkpoint_save_failed",
                tenant_id=str(tenant_uuid),
                lead_id=str(lead_row.id),
            )

        # --- Step 9: extract bot text + sanitize + deliver ---
        last_msg = result["messages"][-1] if result.get("messages") else {}
        bot_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
        bot_text = await ConversationPipeline.sanitize_text(bot_text, "bot_output")

        if not bot_text.strip():
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_row.id,
                campaign_id=campaign_id,
                session_id=initial_state.get("session_id", ""),
                error_code="empty_response",
            )

        # Audit message log (best-effort)
        with contextlib.suppress(Exception):
            audit_repo.log_message(
                user_id=lead_row.id,
                role="assistant",
                content=bot_text,
                channel=channel_type,
                tenant_id=tenant_uuid,
            )

        # Channel send (errors abort turn — user must see send failure)
        from src.modules.sales_agent.infrastructure.external.output_manager import (
            OutputManager,
        )

        try:
            external_id = await OutputManager.process_response(
                lead_row.telegram_id or "",
                bot_text,
                channel_adapter,
                channel_type=channel_type,
            )
        except Exception as exc:
            logger.exception(
                "outbound_orchestrator_channel_send_failed",
                tenant_id=str(tenant_uuid),
                lead_id=str(lead_row.id),
                campaign_id=str(campaign_id),
            )
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_row.id,
                campaign_id=campaign_id,
                session_id=initial_state.get("session_id", ""),
                error_code="channel_send_failed",
                error_message=str(exc),
            )

        # --- Step 10: Closer Studio WS audit (best-effort) ---
        with contextlib.suppress(Exception):
            await AuditEmitter.emit_assistant_message(tenant_uuid, lead_row, bot_text, result)

        external_message_id = external_id if isinstance(external_id, str) else None

        return OutboundResult(
            success=True,
            tenant_id=tenant_id,
            lead_id=lead_row.id,
            campaign_id=campaign_id,
            session_id=initial_state.get("session_id", ""),
            external_message_id=external_message_id,
        )


__all__ = ["OutboundOrchestrator", "OutboundResult"]
