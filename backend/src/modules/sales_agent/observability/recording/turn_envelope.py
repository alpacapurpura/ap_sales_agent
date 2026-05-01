"""Turn envelope for sales_agent — single entrypoint the orchestrators talk to.

Mirror of :mod:`src.modules.copilot.observability.recording.turn_envelope`
adapted to sales_agent's row shape (``lead_id`` + ``channel_type`` instead
of ``conversation_id`` + ``user_id``). Lifting both into ``shared/`` is a
deferred refactor (DRY threshold = 2 consumers, but the copilot envelope
also folds copilot-specific legacy compat keys + routing log writes —
the abstract surface is non-trivial).

Why this exists
---------------

Bug #2 PR-1 RCA (see ``docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/
sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/IMPL-LOG-agentic.md``):

* Sales_agent had **0 rows globally** in ``sales_agent_trace_event`` /
  ``sales_agent_llm_call`` despite real Telegram traffic. Two gaps acted
  jointly:

  1. **No turn envelope.** The orchestrator never wrote
     ``turn_start`` / ``turn_end`` rows and never explicitly committed
     the trace-event session. Every LLM-call row added by the callback
     handler stayed pending in the session and got discarded.
  2. **Async/sync handler dispatch.** ``BaseAgentCallbackHandler`` is a
     sync ``BaseCallbackHandler``; LangChain's ``AsyncCallbackManager``
     dispatches sync handlers via ``run_in_executor`` (foreign thread).
     Without an envelope ``flush + commit`` from the main thread, those
     worker-thread ``session.add`` calls never reached Postgres.

This module fixes both: ``observe_turn`` brackets the turn, writes
``turn_start`` on enter and ``turn_end`` on exit, and explicitly commits
the trace-event session on each write — picking up whatever rows the
callback handler queued in between.

Public contract (what the orchestrators call)
---------------------------------------------

::

    obs = SalesAgentObservabilityContext.start(...)
    async with obs.observe_turn(message=..., route=..., attachments=...):
        result = await agent_app.ainvoke(state, config=obs.langchain_config())
    # turn_start + turn_end already persisted, no caller action needed.

Best-effort
-----------

Every persistence path is wrapped in ``try/except`` + ``structlog.warning``
+ ``_safe_rollback`` so an observability failure never bubbles out of the
orchestrator. This matches ``.claude/rules/copilot-observability.md``
§"Best-effort writes".
"""

from __future__ import annotations

import contextlib
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select

from src.modules.sales_agent.observability.persistence.llm_call_repository import (
    SalesAgentLlmCallRepository,
)
from src.modules.sales_agent.observability.persistence.models.llm_call_model import (
    SalesAgentLlmCallModel,
)
from src.modules.sales_agent.observability.persistence.trace_event_repository import (
    SalesAgentTraceEventRepository,
)
from src.modules.sales_agent.observability.recording.callback_handler import (
    SalesAgentCallbackHandler,
)
from src.shared.agent_observability.recording.sanitization import sanitize_payload, truncate

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.shared.agent_observability.cost.fx_resolver import FXResolver
    from src.shared.agent_observability.pricing.resolver import PricingResolver

logger = structlog.get_logger()


@dataclass
class _TurnSummary:
    """Stream-shape totals supplied by the orchestrator before turn close."""

    response_length: int = 0
    message_count: int = 0
    block_count: int = 0


@dataclass
class _TurnErrorFlag:
    """Out-of-band error flag set by the orchestrator.

    The orchestrator catches stream errors inside its own ``except`` blocks
    so it can emit a user-friendly fallback (chat orchestrator) or a
    structured ``OutboundResult`` (outbound orchestrator). That cleans the
    body exit — without this flag, ``turn_end`` would record
    ``status='ok'`` even when the LLM run blew up.
    """

    error_kind: str
    error_message: str | None = None


@dataclass
class SalesAgentObservabilityContext:
    """One instance per turn. Owns the callback handler + turn lifecycle.

    Mirrors copilot's :class:`ObservabilityContext` with the sales-agent
    column shape. Lifting to ``shared/`` is a deferred refactor — the
    cross-agent abstract surface is non-trivial because copilot also
    folds legacy compat keys and routing-log writes.
    """

    tenant_id: UUID
    lead_id: UUID
    channel_type: str
    turn_id: UUID
    callback_handler: SalesAgentCallbackHandler
    llm_call_repo: SalesAgentLlmCallRepository
    trace_repo: SalesAgentTraceEventRepository
    _summary: _TurnSummary = field(default_factory=_TurnSummary)
    _turn_start_monotonic: float = field(default_factory=time.monotonic)
    _error_flag: _TurnErrorFlag | None = None

    @classmethod
    def start(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel_type: str,
        llm_call_repo: SalesAgentLlmCallRepository,
        trace_repo: SalesAgentTraceEventRepository,
        pricing_resolver: PricingResolver,
        fx_resolver: FXResolver,
        tenant_currency: str = "USD",
        role: str = "agent",
        turn_id: UUID | None = None,
    ) -> SalesAgentObservabilityContext:
        """Build a fresh context. Turn id is allocated if not provided."""
        tid = turn_id or uuid4()
        # The handler shares the same SQLAlchemy session as the trace_repo
        # so a flush/commit on the envelope picks up whatever rows the
        # callback wrote. ``db_session`` lets the base ``_safe_rollback``
        # keep the session usable on persistence errors.
        handler = SalesAgentCallbackHandler(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type=channel_type,
            turn_id=tid,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            tenant_currency=tenant_currency,
            role=role,
            db_session=getattr(trace_repo, "db", None),
        )
        return cls(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type=channel_type,
            turn_id=tid,
            callback_handler=handler,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
        )

    def langchain_config(self) -> dict[str, Any]:
        """Return a ``RunnableConfig``-shaped dict with the callback wired in."""
        return {"callbacks": [self.callback_handler]}

    def set_turn_summary(
        self,
        *,
        response_length: int,
        message_count: int,
        block_count: int,
    ) -> None:
        """Stash stream-shape totals so ``turn_end`` can include them."""
        self._summary = _TurnSummary(
            response_length=int(response_length),
            message_count=int(message_count),
            block_count=int(block_count),
        )

    def set_turn_error(
        self,
        *,
        error_kind: str,
        error_message: str | None = None,
    ) -> None:
        """Flag the current turn as errored without raising.

        The chat orchestrator catches LLM / graph errors so it can send a
        Spanish-neutral fallback to the user; the outbound orchestrator
        wraps the same in an ``OutboundResult.error_code``. Both paths
        leave the ``observe_turn`` body returning normally — without this
        flag, ``turn_end`` would record ``status='ok'`` and the voice
        fidelity grader / weekly quality eval would lose visibility on
        the failure.
        """
        self._error_flag = _TurnErrorFlag(
            error_kind=error_kind,
            error_message=error_message,
        )

    @asynccontextmanager
    async def observe_turn(
        self,
        *,
        message: str,
        route: str,
        attachments: list[Any] | None = None,
    ) -> AsyncIterator[SalesAgentObservabilityContext]:
        """Bracket the turn — write turn_start on enter, turn_end on exit.

        The body MUST run the orchestrator graph with
        ``config=self.langchain_config()`` so the callback handler sees
        every LLM/tool/chain event. ``turn_end`` aggregates counts from
        ``sales_agent_llm_call`` rows under ``self.turn_id``.
        """
        self._write_turn_start(message=message, route=route, attachments=attachments or [])
        error_for_end: BaseException | None = None
        try:
            yield self
        except BaseException as exc:
            error_for_end = exc
            raise
        finally:
            # ``finally`` so a client disconnect (asyncio.CancelledError —
            # BaseException, not Exception) still leaves a turn_end row.
            self._write_turn_end(
                error=error_for_end if isinstance(error_for_end, Exception) else None,
            )

    # ── internals ───────────────────────────────────────────────────────

    def _write_turn_start(
        self,
        *,
        message: str,
        route: str,
        attachments: list[Any],
    ) -> None:
        try:
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                lead_id=self.lead_id,
                channel_type=self.channel_type,
                turn_id=self.turn_id,
                span_id=self.turn_id,
                event_type="turn_start",
                name=route,
                data=sanitize_payload(
                    {
                        "message_preview": truncate(message),
                        "route": route,
                        "attachments": len(attachments),
                    },
                ),
                status="ok",
            )
            self._commit_session()
        except Exception as exc:  # noqa: BLE001 — best-effort observability
            logger.warning(
                "sales_agent_obs_turn_start_failed",
                error=str(exc),
                tenant_id=str(self.tenant_id),
                lead_id=str(self.lead_id),
            )
            self._safe_rollback()

    def _write_turn_end(self, *, error: BaseException | None) -> None:
        duration_ms = max(int((time.monotonic() - self._turn_start_monotonic) * 1000), 0)
        try:
            totals = self._aggregate_totals()
            data: dict[str, Any] = {
                "ended_at": datetime.now(tz=UTC).isoformat(),
                **totals,
                "response_length": self._summary.response_length,
                "message_count": self._summary.message_count,
                "block_count": self._summary.block_count,
            }
            if error is not None:
                data["error_type"] = type(error).__name__
                data["error_message"] = truncate(str(error))
            # Out-of-band error flag wins over a clean exit: orchestrator
            # caught the exception itself but the turn was still a failure.
            if self._error_flag is not None:
                data["error_kind"] = self._error_flag.error_kind
                if self._error_flag.error_message is not None:
                    data["error_message"] = truncate(self._error_flag.error_message)
            is_error = error is not None or self._error_flag is not None
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                lead_id=self.lead_id,
                channel_type=self.channel_type,
                turn_id=self.turn_id,
                span_id=uuid4(),
                event_type="turn_end",
                name="turn_end",
                data=sanitize_payload(data),
                duration_ms=duration_ms,
                status="error" if is_error else "ok",
            )
            self._commit_session()
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "sales_agent_obs_turn_end_failed",
                error=str(exc),
                tenant_id=str(self.tenant_id),
                lead_id=str(self.lead_id),
            )
            self._safe_rollback()

    def _commit_session(self) -> None:
        """Commit the trace-event session.

        ``observe_turn`` writes turn_start at the very start of the turn
        and turn_end at the very end. Sales_agent's orchestrator commits
        the audit-message + checkpoint sessions, but not the trace
        session — without this commit, the rows stay in the SA identity
        map and disappear when the orchestrator session closes.

        Best-effort: a failed commit is logged but never propagated.
        Note: this also flushes any pending rows added by the callback
        handler from worker threads (LangChain ``AsyncCallbackManager``
        dispatches sync ``on_*`` via ``run_in_executor``). That is
        precisely why the previous implementation lost every event.
        """
        session = getattr(self.trace_repo, "db", None)
        if session is None:
            return
        commit = getattr(session, "commit", None)
        if commit is None:
            return
        try:
            commit()
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "sales_agent_obs_commit_failed",
                error=str(exc),
                tenant_id=str(self.tenant_id),
            )
            self._safe_rollback()

    def _safe_rollback(self) -> None:
        session = getattr(self.trace_repo, "db", None)
        if session is None:
            return
        rollback = getattr(session, "rollback", None)
        if rollback is None:
            return
        with contextlib.suppress(Exception):
            rollback()

    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum the ``sales_agent_llm_call`` rows for this turn.

        Flushes the session first so rows added by the callback handler
        during the turn (which only ``session.add`` without committing)
        are visible to the aggregate SELECT.
        """
        try:
            session = self.llm_call_repo.db
            with contextlib.suppress(Exception):
                session.flush()
            stmt = select(
                func.count().label("call_count"),
                func.coalesce(func.sum(SalesAgentLlmCallModel.input_tokens), 0).label(
                    "input_tokens",
                ),
                func.coalesce(func.sum(SalesAgentLlmCallModel.output_tokens), 0).label(
                    "output_tokens",
                ),
                func.coalesce(func.sum(SalesAgentLlmCallModel.cached_read_tokens), 0).label(
                    "cached_read_tokens",
                ),
                func.coalesce(func.sum(SalesAgentLlmCallModel.cost_usd), 0).label("cost_usd"),
            ).where(
                SalesAgentLlmCallModel.tenant_id == self.tenant_id,
                SalesAgentLlmCallModel.turn_id == self.turn_id,
            )
            row = session.execute(stmt).one()
            return {
                "llm_call_count": int(row.call_count),
                "total_input_tokens": int(row.input_tokens),
                "total_output_tokens": int(row.output_tokens),
                "total_cached_read_tokens": int(row.cached_read_tokens),
                "total_cost_usd": str(Decimal(row.cost_usd)),
                "model_responded": self._most_used_model(session),
            }
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "sales_agent_obs_aggregate_totals_failed",
                error=str(exc),
                tenant_id=str(self.tenant_id),
            )
            return _empty_totals()

    def _most_used_model(self, session: Any) -> str:  # noqa: ANN401 — Session
        """Pick the model with the most LLM calls for this turn."""
        try:
            stmt = (
                select(
                    SalesAgentLlmCallModel.model_responded,
                    func.count().label("c"),
                )
                .where(
                    SalesAgentLlmCallModel.tenant_id == self.tenant_id,
                    SalesAgentLlmCallModel.turn_id == self.turn_id,
                )
                .group_by(SalesAgentLlmCallModel.model_responded)
                .order_by(func.count().desc())
                .limit(1)
            )
            row = session.execute(stmt).first()
            return str(row.model_responded) if row is not None else ""
        except Exception:  # noqa: BLE001 — best-effort
            return ""


def _empty_totals() -> dict[str, Any]:
    return {
        "llm_call_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cached_read_tokens": 0,
        "total_cost_usd": "0",
        "model_responded": "",
    }


__all__ = ["SalesAgentObservabilityContext"]
