"""LangChain callback handler — the SOTA, self-contained ingress.

Subclass of ``langchain_core.callbacks.BaseCallbackHandler`` wired into
the orchestrator via ``RunnableConfig(callbacks=[handler])`` (Phase 2).
One handler instance per turn — created by ``ObservabilityContext`` —
because the per-call state (open spans keyed by ``run_id``) is naturally
turn-scoped.

What it captures (mapped to columns / event types):

* ``on_chat_model_start`` — opens a span (in-memory). Captures provider,
  model_requested, started_at, run_id.
* ``on_llm_end``           — closes the open chat span. Pulls
  ``usage_metadata`` from ``response.generations[0][0].message`` (an
  :class:`~langchain_core.messages.AIMessage`), runs the cost calculator,
  resolves FX, persists one row in ``copilot_llm_call`` and a mirror row
  in ``copilot_trace_event`` (event_type='llm_call').
* ``on_llm_error``         — same close, with status='error' and zero
  cost.
* ``on_tool_start`` / ``on_tool_end`` / ``on_tool_error`` — persist one
  row in ``copilot_trace_event`` (event_type='tool_call') with
  duration_ms.
* ``on_chain_start`` / ``on_chain_end`` — node_enter/node_exit rows.

**Best-effort.** Any exception during persistence (DB down, mapper
config error, pricing resolver bug) is swallowed and logged — never
propagated. Pattern mirrors ``application/observability/trace_recorder.py``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog

from src.modules.copilot.observability.persistence.llm_call_repository import (
    LlmCallRepository,
)
from src.modules.copilot.observability.persistence.trace_event_repository import (
    TraceEventRepository,
)
from src.shared.agent_observability.cost.calculator import calculate_cost
from src.shared.agent_observability.cost.fx_resolver import FXResolver
from src.shared.agent_observability.pricing.resolver import PricingResolver
from src.shared.agent_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)
from src.shared.agent_observability.recording.sanitization import (
    sanitize_payload,
    truncate,
)

if TYPE_CHECKING:
    from langchain_core.outputs import LLMResult

logger = structlog.get_logger()


@dataclass(slots=True)
class _LLMSpan:
    """In-memory state opened by ``on_chat_model_start``."""

    started_at: datetime
    provider: str
    model_requested: str
    monotonic_start: float


@dataclass(slots=True)
class _ToolSpan:
    """In-memory state opened by ``on_tool_start``."""

    name: str
    args_preview: str
    started_at: datetime
    monotonic_start: float


@dataclass(slots=True)
class _ChainSpan:
    """In-memory state opened by ``on_chain_start`` for LangGraph nodes."""

    name: str
    started_at: datetime
    monotonic_start: float


@dataclass
class ObservabilityCallbackHandler(BaseAgentCallbackHandler):
    """Self-contained recorder. One instance per turn.

    Subclass of :class:`BaseAgentCallbackHandler` (S11A retrofit). Helpers
    (``_extract_usage``, ``_extract_provider_and_model``, etc.) live on
    the base; this class overrides only the abstract persisters and
    keeps the LangChain plumbing for now (commit 4 lifts the 6 ``on_*``
    callbacks too).
    """

    tenant_id: UUID
    conversation_id: UUID | None
    user_id: UUID | None
    turn_id: UUID
    llm_call_repo: LlmCallRepository
    trace_repo: TraceEventRepository
    pricing_resolver: PricingResolver
    fx_resolver: FXResolver
    tenant_currency: str = "USD"
    role: str = "agent"

    # In-memory open-span tables. Kept small — turns rarely exceed a few
    # parallel runs.
    _llm_spans: dict[UUID, _LLMSpan] = field(default_factory=dict)
    _tool_spans: dict[UUID, _ToolSpan] = field(default_factory=dict)
    _chain_spans: dict[UUID, _ChainSpan] = field(default_factory=dict)

    # ── chat model ──────────────────────────────────────────────────────

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: Any,  # noqa: ANN401 — list[list[BaseMessage]] in LangChain; we don't read it
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401 — required by LangChain BaseCallbackHandler signature
    ) -> None:
        """Open an LLM span keyed by ``run_id``."""
        del messages, parent_run_id, tags, kwargs  # signature parity
        try:
            provider, model = self._extract_provider_and_model(serialized, metadata)
            self._llm_spans[run_id] = _LLMSpan(
                started_at=datetime.now(tz=UTC),
                provider=provider,
                model_requested=model,
                monotonic_start=time.monotonic(),
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("obs_on_chat_model_start_failed", error=str(exc))

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain signature
    ) -> None:
        """Close the open chat span — persist one llm_call row + trace event."""
        del parent_run_id, tags, kwargs
        span = self._llm_spans.pop(run_id, None)
        if span is None:
            return
        try:
            self._persist_llm_call(span=span, response=response, status="ok", error_type=None)
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_llm_end_failed", error=str(exc))

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain signature
    ) -> None:
        """Close the open chat span with ``status='error'``."""
        del parent_run_id, tags, kwargs
        span = self._llm_spans.pop(run_id, None)
        if span is None:
            return
        try:
            self._persist_llm_call(
                span=span,
                response=None,
                status="error",
                error_type=type(error).__name__,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_llm_error_failed", error=str(exc))

    # ── tool ────────────────────────────────────────────────────────────

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain signature
    ) -> None:
        """Open a tool span keyed by ``run_id``."""
        del parent_run_id, tags, metadata, kwargs
        try:
            name = serialized.get("name", "tool") if isinstance(serialized, dict) else "tool"
            self._tool_spans[run_id] = _ToolSpan(
                name=name,
                args_preview=truncate(input_str or ""),
                started_at=datetime.now(tz=UTC),
                monotonic_start=time.monotonic(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_tool_start_failed", error=str(exc))

    def on_tool_end(
        self,
        output: Any,  # noqa: ANN401 — tool output type is provider-specific
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain signature
    ) -> None:
        """Close the tool span and persist a ``tool_call`` trace event."""
        del parent_run_id, tags, kwargs
        span = self._tool_spans.pop(run_id, None)
        if span is None:
            return
        try:
            duration_ms = self._elapsed_ms(span.monotonic_start)
            self._persist_trace_event_row(
                tenant_id=self.tenant_id,
                turn_id=self.turn_id,
                span_id=run_id,
                event_type="tool_call",
                name=span.name,
                data=sanitize_payload(
                    {
                        "args": span.args_preview,
                        "output_preview": truncate(self._stringify(output)),
                    },
                ),
                duration_ms=duration_ms,
                status="ok",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_tool_end_failed", error=str(exc))

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain signature
    ) -> None:
        """Close the tool span with ``status='error'``."""
        del parent_run_id, tags, kwargs
        span = self._tool_spans.pop(run_id, None)
        if span is None:
            return
        try:
            self._persist_trace_event_row(
                tenant_id=self.tenant_id,
                turn_id=self.turn_id,
                span_id=run_id,
                event_type="tool_call",
                name=span.name,
                data=sanitize_payload(
                    {
                        "args": span.args_preview,
                        "error_type": type(error).__name__,
                        "error_message": truncate(str(error)),
                    },
                ),
                duration_ms=self._elapsed_ms(span.monotonic_start),
                status="error",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_tool_error_failed", error=str(exc))

    # ── chain (LangGraph nodes) ─────────────────────────────────────────

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain signature
    ) -> None:
        """Open a chain span — only persisted if it looks like a LangGraph node."""
        del inputs, parent_run_id, tags, metadata, kwargs
        try:
            name = self._chain_name(serialized)
            if name is None:
                return
            self._chain_spans[run_id] = _ChainSpan(
                name=name,
                started_at=datetime.now(tz=UTC),
                monotonic_start=time.monotonic(),
            )
            self._persist_trace_event_row(
                tenant_id=self.tenant_id,
                turn_id=self.turn_id,
                span_id=run_id,
                event_type="node_enter",
                name=name,
                data={},
                duration_ms=None,
                status="ok",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_chain_start_failed", error=str(exc))

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain signature
    ) -> None:
        """Persist a ``node_exit`` row if we have a matching open chain span."""
        del outputs, parent_run_id, tags, kwargs
        span = self._chain_spans.pop(run_id, None)
        if span is None:
            return
        try:
            self._persist_trace_event_row(
                tenant_id=self.tenant_id,
                turn_id=self.turn_id,
                span_id=run_id,
                event_type="node_exit",
                name=span.name,
                data={},
                duration_ms=self._elapsed_ms(span.monotonic_start),
                status="ok",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_chain_end_failed", error=str(exc))

    # ── private helpers ─────────────────────────────────────────────────

    def _persist_llm_call(
        self,
        *,
        span: _LLMSpan,
        response: LLMResult | None,
        status: str,
        error_type: str | None,
    ) -> None:
        """Persist one row to ``copilot_llm_call`` + mirror to ``copilot_trace_event``."""
        usage = self._extract_usage(response)
        model_responded = self._extract_model_responded(response, fallback=span.model_requested)

        pricing = self.pricing_resolver.resolve(
            provider=span.provider,
            model=model_responded,
            at_ts=span.started_at,
        )
        snapshot = pricing.snapshot
        cost_usd = (
            Decimal(0)
            if status == "error"
            else calculate_cost(
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                cached_read_tokens=usage["cached_read_tokens"],
                cached_write_tokens=usage["cached_write_tokens"],
                pricing=snapshot,
            )
        )
        fx_rate, fx_source = self.fx_resolver.resolve(
            currency_code=self.tenant_currency,
            at_ts=span.started_at,
        )
        cost_tenant = cost_usd * fx_rate
        duration_ms = self._elapsed_ms(span.monotonic_start)
        span_id = uuid4()

        self._persist_llm_call_row(
            tenant_id=self.tenant_id,
            turn_id=self.turn_id,
            span_id=span_id,
            provider=span.provider,
            model_requested=span.model_requested,
            model_responded=model_responded,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            cached_read_tokens=usage["cached_read_tokens"],
            cached_write_tokens=usage["cached_write_tokens"],
            reasoning_tokens=usage["reasoning_tokens"],
            pricing_version_id=getattr(snapshot, "id", None) or uuid4(),
            input_unit_cost_usd=snapshot.input_cost_per_token,
            output_unit_cost_usd=snapshot.output_cost_per_token,
            cached_read_unit_cost_usd=snapshot.cache_read_cost_per_token or Decimal(0),
            cost_usd=cost_usd,
            tenant_currency=self.tenant_currency,
            fx_rate_to_tenant=fx_rate,
            fx_rate_source=fx_source,
            cost_tenant_currency=cost_tenant,
            started_at=span.started_at,
            duration_ms=duration_ms,
            status=status,
            error_type=error_type,
            role=self.role,
        )

        # Mirror in trace_event so the existing /trazas admin still shows
        # one entry per LLM call. The aggregate cost lives in
        # copilot_llm_call; the trace event carries just the breadcrumb
        # under the canonical event_type='llm_call' string the docs
        # already advertise.
        self._persist_trace_event_row(
            tenant_id=self.tenant_id,
            turn_id=self.turn_id,
            span_id=span_id,
            event_type="llm_call",
            name=f"{span.provider}.{model_responded}",
            data=sanitize_payload(
                {
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "cached_read_tokens": usage["cached_read_tokens"],
                    "cost_usd": str(cost_usd),
                    "is_estimated_pricing": pricing.is_estimated,
                    "fx_rate_source": fx_source,
                },
            ),
            duration_ms=duration_ms,
            status=status,
        )

    # ── abstract method overrides (Template Method) ──────────────────────

    def _persist_llm_call_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to ``copilot_llm_call``.

        Injects ``conversation_id`` / ``user_id`` / ``parent_span_id`` so
        the shared Template Method skeleton stays agent-agnostic.
        """
        self.llm_call_repo.add(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            parent_span_id=None,
            **kwargs,
        )

    def _persist_trace_event_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to ``copilot_trace_event``."""
        self.trace_repo.add(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            **kwargs,
        )

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _elapsed_ms(monotonic_start: float) -> int:
        return max(int((time.monotonic() - monotonic_start) * 1000), 0)

    @staticmethod
    def _stringify(output: Any) -> str:  # noqa: ANN401 — caller-provided output is polymorphic
        try:
            return str(output)
        except Exception:  # noqa: BLE001
            return "<unstringifiable>"


__all__ = ["ObservabilityCallbackHandler"]
