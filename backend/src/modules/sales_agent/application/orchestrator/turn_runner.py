"""Turn runner — observability-bracketed turn execution for inbound chat.

Carved out of :class:`ChatOrchestrator` (PR-1 hotfix Bug #2 iter 2) so the
facade stays under the LOC ratchet (S11B DoD §8 — ceiling 400). The
runner owns the per-turn observability lifecycle: it brackets the
``ConversationPipeline.invoke_agent_with_typing`` call inside
:meth:`SalesAgentObservabilityContext.observe_turn` so ``turn_start`` /
``turn_end`` rows get written + committed, and forwards the envelope's
``langchain_config`` to the LangGraph invocation so the bound callback
handler captures every ``llm_call`` / ``tool_call`` / ``node_*`` event.

When the envelope is ``None`` (tenant or lead missing — cannot persist),
the runner falls back to the legacy degraded path: invoke + checkpoint
+ deliver without observability.

Honest error path
-----------------

When the graph raises inside the envelope body, the runner flags the
turn via :meth:`SalesAgentObservabilityContext.set_turn_error` so the
envelope's ``__aexit__`` records ``status='error'`` even though the
caller (``ChatOrchestrator.process_chat_flow``) catches the exception
itself to send a Spanish-neutral fallback to the user.

# [SALES-AGENT-TURN-RUNNER-PR1-HOTFIX] -> docs/pm-nico/pis/active/
# PI-1.1-pi1-post-mortem/sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/
# IMPL-LOG-agentic.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.modules.sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.sales_agent.infrastructure.memory.audit_repository import (
        AuditRepository,
    )
    from src.modules.sales_agent.infrastructure.repositories.state_repository import (
        StateRepository,
    )
    from src.shared.domain.messages import IncomingMessage
    from src.shared.infrastructure.channels.base import BaseChannel

logger = structlog.get_logger()


class TurnRunner:
    """Observability-bracketed turn execution.

    Single responsibility: run one inbound chat turn with the
    observability envelope wired in. Extracted from
    :class:`ChatOrchestrator` so the facade stays a thin composition
    layer (S11B Strangler Fig pattern).
    """

    @staticmethod
    async def run(
        *,
        observability_ctx: object | None,
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        initial_state: dict,
        db: Session,
        state_repo: StateRepository,
        tenant_uuid: UUID | None,
        user: object | None,
        customer: object | None,
        channel_type: str,
        last_session_summary: str | None,
        audit_repo: AuditRepository,
    ) -> None:
        """Drive ``ainvoke`` + checkpoint + delivery inside the envelope.

        When ``observability_ctx`` is present (the common path) the body
        runs inside ``observe_turn`` so ``turn_start`` is committed on
        enter, ``turn_end`` on exit, and any exception is recorded via
        ``set_turn_error`` before being re-raised. The envelope's
        ``_commit_session`` flush picks up every ``llm_call`` /
        ``tool_call`` / ``node_*`` row that the bound callback handler
        queued during ``ainvoke``.

        When ``observability_ctx`` is ``None`` (tenant/lead missing —
        cannot persist) we run the turn without observability — exactly
        the legacy degraded path.
        """
        from src.modules.sales_agent.observability.recording.turn_envelope import (
            SalesAgentObservabilityContext,
        )

        # Best-effort: route is the entry specialist. Sales_agent has no
        # explicit "current_route" in state, so we tag ``inbound`` for
        # chat-flow turns; the body may set a more precise label via
        # ``ctx.set_turn_summary`` once it knows the final ``next_node``.
        route_label = "inbound"
        if not isinstance(observability_ctx, SalesAgentObservabilityContext):
            # No envelope — run the turn unobserved (degraded mode).
            result = await ConversationPipeline.invoke_agent_with_typing(
                channel_adapter,
                incoming,
                initial_state,
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
            return

        # Envelope present — bracket the turn so trace rows actually commit.
        async with observability_ctx.observe_turn(
            message=incoming.text or "",
            route=route_label,
            attachments=[],
        ):
            try:
                result = await ConversationPipeline.invoke_agent_with_typing(
                    channel_adapter,
                    incoming,
                    initial_state,
                    langchain_config=observability_ctx.langchain_config(),
                )
            except Exception as exc:
                # Flag the turn as errored so ``turn_end`` records
                # ``status='error'`` even though the orchestrator's outer
                # ``except`` will swallow the exception to send the
                # user-friendly fallback message.
                observability_ctx.set_turn_error(
                    error_kind="graph_invocation_failed",
                    error_message=str(exc),
                )
                raise

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

            # Stash stream-shape totals so ``turn_end`` carries them. Best-effort.
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
                    "sales_agent_obs_set_turn_summary_failed",
                    error=str(exc),
                )


__all__ = ["TurnRunner"]
