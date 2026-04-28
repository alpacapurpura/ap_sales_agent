"""Turn envelope — the single entrypoint that chat.py talks to.

The Phase 2 atomic switch reduces the orchestrator's observability
surface to two lines:

    obs = ObservabilityContext.start(...)
    async with obs.observe_turn(message=..., route=..., attachments=...):
        async for event in graph.astream_events(state, config=obs.langchain_config()):
            ...
        obs.set_turn_summary(response_length=..., message_count=..., block_count=...)

Everything else (LLM rows, tool rows, costs, FX, mirroring to
``copilot_trace_event``) happens via the bound :class:`ObservabilityCallbackHandler`.

Best-effort: every persistence path is wrapped in ``try/except`` so an
observability failure never bubbles out of the orchestrator.
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

from src.modules.copilot.observability.persistence.llm_call_repository import LlmCallRepository
from src.modules.copilot.observability.persistence.models.llm_call_model import (
    CopilotLlmCallModel,
)
from src.modules.copilot.observability.persistence.trace_event_repository import (
    TraceEventRepository,
)
from src.modules.copilot.observability.recording.callback_handler import (
    ObservabilityCallbackHandler,
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

    The orchestrator catches stream errors inside its own except blocks
    so it can emit a user-friendly SSE message. That cleans the body
    exit — without this flag, ``turn_end`` would record ``status='ok'``
    even when the LLM run blew up (the 2026-04-27 incident).
    """

    error_kind: str
    error_message: str | None = None


@dataclass
class ObservabilityContext:
    """One instance per turn. Owns the callback handler + turn lifecycle."""

    tenant_id: UUID
    conversation_id: UUID | None
    user_id: UUID | None
    turn_id: UUID
    callback_handler: ObservabilityCallbackHandler
    llm_call_repo: LlmCallRepository
    trace_repo: TraceEventRepository
    _summary: _TurnSummary = field(default_factory=_TurnSummary)
    _turn_start_monotonic: float = field(default_factory=time.monotonic)
    _error_flag: _TurnErrorFlag | None = None

    @classmethod
    def start(
        cls,
        *,
        tenant_id: UUID,
        conversation_id: UUID | None,
        user_id: UUID | None,
        llm_call_repo: LlmCallRepository,
        trace_repo: TraceEventRepository,
        pricing_resolver: PricingResolver,
        fx_resolver: FXResolver,
        tenant_currency: str = "USD",
        role: str = "agent",
        turn_id: UUID | None = None,
    ) -> ObservabilityContext:
        """Build a fresh context. Turn id is allocated if not provided."""
        tid = turn_id or uuid4()
        handler = ObservabilityCallbackHandler(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            user_id=user_id,
            turn_id=tid,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            tenant_currency=tenant_currency,
            role=role,
        )
        return cls(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            user_id=user_id,
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
        """Stash the stream-shape totals so ``turn_end`` can include them.

        Called by the orchestrator right before the ``observe_turn``
        context manager exits.
        """
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

        The orchestrator catches stream errors (TimeoutError,
        ToolCallLoopDetected, generic Exception) so it can emit a
        user-facing SSE error and persist partial state. Those catches
        used to leave the turn marked ``status='ok'`` — observability
        lied. Calling this from the except block ensures ``turn_end``
        records the truth (``status='error'`` + ``error_kind`` +
        truncated message).
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
    ) -> AsyncIterator[ObservabilityContext]:
        """Bracket the turn — write turn_start on enter, turn_end on exit.

        The body MUST run the orchestrator graph with
        ``config=self.langchain_config()`` so the callback handler sees
        every LLM/tool/chain event. ``turn_end`` aggregates counts from
        ``copilot_llm_call`` rows under ``self.turn_id`` and folds in the
        legacy stream-shape keys (``model``/``prompt_tokens``/...) that
        the existing Streamlit pages still consume.
        """
        self._write_turn_start(message=message, route=route, attachments=attachments or [])
        error_for_end: BaseException | None = None
        try:
            yield self
        except BaseException as exc:  # we MUST land turn_end even on CancelledError when FE drops the SSE
            error_for_end = exc
            raise
        finally:
            # ``finally`` so a client disconnect (asyncio.CancelledError —
            # BaseException, not Exception) still leaves a turn_end row.
            # Without this, dropped SSEs leak open turns.
            self._write_turn_end(error=error_for_end if isinstance(error_for_end, Exception) else None)

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
                user_id=self.user_id,
                conversation_id=self.conversation_id,
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
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_turn_start_failed", error=str(exc))

    def _write_turn_end(self, *, error: BaseException | None) -> None:
        duration_ms = max(int((time.monotonic() - self._turn_start_monotonic) * 1000), 0)
        try:
            totals = self._aggregate_totals()
            data: dict[str, Any] = {
                "ended_at": datetime.now(tz=UTC).isoformat(),
                **totals,
                **self._legacy_compat_keys(totals),
            }
            if error is not None:
                data["error_type"] = type(error).__name__
                data["error_message"] = truncate(str(error))
            # Out-of-band error flag wins over a clean exit: the
            # orchestrator caught the exception itself so the body
            # returned normally, but the turn was still a failure.
            if self._error_flag is not None:
                data["error_kind"] = self._error_flag.error_kind
                if self._error_flag.error_message is not None:
                    data["error_message"] = truncate(self._error_flag.error_message)
            is_error = error is not None or self._error_flag is not None
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
                turn_id=self.turn_id,
                span_id=uuid4(),
                event_type="turn_end",
                name="turn_end",
                data=sanitize_payload(data),
                duration_ms=duration_ms,
                status="error" if is_error else "ok",
            )
            self._commit_session()
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_turn_end_failed", error=str(exc))

    def _commit_session(self) -> None:
        """Commit the trace_repo session.

        ``observe_turn`` writes turn_start at the very start of the turn
        and turn_end at the very end — there's no other orchestrator
        commit covering them, so the rows would be discarded when the
        FastAPI request session closes. Best-effort: a failed commit is
        logged but never propagated.
        """
        session = getattr(self.trace_repo, "db", None)
        if session is None:
            return
        with contextlib.suppress(Exception):
            session.commit()

    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum the copilot_llm_call rows for this turn.

        Flushes the session first so rows added by the callback handler
        during the turn (which only ``session.add`` without committing)
        are visible to the aggregate SELECT.
        """
        try:
            session = self.llm_call_repo.db
            with contextlib.suppress(Exception):
                session.flush()
            stmt = select(
                func.count().label("count"),
                func.coalesce(func.sum(CopilotLlmCallModel.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(CopilotLlmCallModel.output_tokens), 0).label(
                    "output_tokens",
                ),
                func.coalesce(func.sum(CopilotLlmCallModel.cached_read_tokens), 0).label(
                    "cached_read_tokens",
                ),
                func.coalesce(func.sum(CopilotLlmCallModel.cost_usd), 0).label("cost_usd"),
            ).where(
                CopilotLlmCallModel.tenant_id == self.tenant_id,
                CopilotLlmCallModel.turn_id == self.turn_id,
            )
            row = session.execute(stmt).one()
            return {
                "llm_call_count": int(row.count),
                "total_input_tokens": int(row.input_tokens),
                "total_output_tokens": int(row.output_tokens),
                "total_cached_read_tokens": int(row.cached_read_tokens),
                "total_cost_usd": str(Decimal(row.cost_usd)),
                "model_responded": self._most_used_model(session),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_aggregate_totals_failed", error=str(exc))
            return _empty_totals()

    def _most_used_model(self, session: Any) -> str:  # noqa: ANN401 — Session
        """Pick the model with the most LLM calls for this turn."""
        try:
            stmt = (
                select(
                    CopilotLlmCallModel.model_responded,
                    func.count().label("c"),
                )
                .where(
                    CopilotLlmCallModel.tenant_id == self.tenant_id,
                    CopilotLlmCallModel.turn_id == self.turn_id,
                )
                .group_by(CopilotLlmCallModel.model_responded)
                .order_by(func.count().desc())
                .limit(1)
            )
            row = session.execute(stmt).first()
            return str(row.model_responded) if row is not None else ""
        except Exception:  # noqa: BLE001
            return ""

    def _legacy_compat_keys(self, totals: dict[str, Any]) -> dict[str, Any]:
        """Fold aggregated totals + stream summary into the legacy JSONB shape.

        Keeps Streamlit ``/trazas`` and ``/copilot-routing`` working
        through the soak window. Phase 3 migrates those pages to read
        ``copilot_llm_call`` directly and this projection is dropped.
        """
        prompt_tokens = int(totals.get("total_input_tokens", 0))
        completion_tokens = int(totals.get("total_output_tokens", 0))
        cached = int(totals.get("total_cached_read_tokens", 0))
        cost_usd_str = str(totals.get("total_cost_usd", "0"))
        try:
            cost_usd = float(cost_usd_str)
        except (TypeError, ValueError):
            cost_usd = 0.0
        cache_hit_rate = round(cached / prompt_tokens, 4) if prompt_tokens else 0.0
        return {
            "model": totals.get("model_responded") or "",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cached_input_tokens": cached,
            "cache_hit_rate": cache_hit_rate,
            "cost_usd": round(cost_usd, 8),
            "response_length": self._summary.response_length,
            "message_count": self._summary.message_count,
            "block_count": self._summary.block_count,
        }


def _empty_totals() -> dict[str, Any]:
    return {
        "llm_call_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cached_read_tokens": 0,
        "total_cost_usd": "0",
        "model_responded": "",
    }


__all__ = ["ObservabilityContext"]
