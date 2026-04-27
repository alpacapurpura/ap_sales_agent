"""Turn envelope — the single entrypoint that chat.py talks to.

The Phase 2 atomic switch reduces the orchestrator's observability
surface to two lines:

    obs = ObservabilityContext.start(...)
    async with obs.observe_turn(message=..., route=..., attachments=...):
        async for event in graph.astream_events(state, config=obs.langchain_config()):
            ...

Everything else (LLM rows, tool rows, costs, FX, mirroring to
``copilot_trace_event``) happens via the bound :class:`ObservabilityCallbackHandler`.
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
from src.modules.copilot.observability.recording.sanitization import sanitize_payload, truncate

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.modules.copilot.observability.cost.fx_resolver import FXResolver
    from src.modules.copilot.observability.pricing.resolver import PricingResolver

logger = structlog.get_logger()


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
    _turn_start_monotonic: float = field(default_factory=time.monotonic)

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
        ``copilot_llm_call`` rows under ``self.turn_id``.
        """
        self._write_turn_start(message=message, route=route, attachments=attachments or [])
        try:
            yield self
        except Exception as exc:
            self._write_turn_end(error=exc)
            raise
        else:
            self._write_turn_end(error=None)

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
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_turn_start_failed", error=str(exc))

    def _write_turn_end(self, *, error: BaseException | None) -> None:
        duration_ms = max(int((time.monotonic() - self._turn_start_monotonic) * 1000), 0)
        try:
            totals = self._aggregate_totals()
            data: dict[str, Any] = {
                "ended_at": datetime.now(tz=UTC).isoformat(),
                **totals,
            }
            if error is not None:
                data["error_type"] = type(error).__name__
                data["error_message"] = truncate(str(error))
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
                status="error" if error is not None else "ok",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_turn_end_failed", error=str(exc))

    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum the copilot_llm_call rows for this turn.

        Flushes the session first so any rows added by the callback
        handler during the turn (which only ``session.add`` without
        committing) are visible to the aggregate SELECT.
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
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_aggregate_totals_failed", error=str(exc))
            return {
                "llm_call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cached_read_tokens": 0,
                "total_cost_usd": "0",
            }


__all__ = ["ObservabilityContext"]
