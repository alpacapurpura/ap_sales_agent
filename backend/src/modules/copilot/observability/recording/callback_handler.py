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
from langchain_core.callbacks import BaseCallbackHandler

from src.modules.copilot.observability.cost.calculator import calculate_cost
from src.modules.copilot.observability.cost.fx_resolver import FXResolver
from src.modules.copilot.observability.persistence.llm_call_repository import (
    LlmCallRepository,
)
from src.modules.copilot.observability.persistence.trace_event_repository import (
    TraceEventRepository,
)
from src.modules.copilot.observability.pricing.resolver import PricingResolver
from src.modules.copilot.observability.recording.sanitization import (
    sanitize_payload,
    truncate,
)

if TYPE_CHECKING:
    from langchain_core.messages import AIMessage
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
class ObservabilityCallbackHandler(BaseCallbackHandler):
    """Self-contained recorder. One instance per turn."""

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
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
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
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
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
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
                turn_id=self.turn_id,
                span_id=run_id,
                event_type="node_enter",
                name=name,
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
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
                turn_id=self.turn_id,
                span_id=run_id,
                event_type="node_exit",
                name=span.name,
                duration_ms=self._elapsed_ms(span.monotonic_start),
                status="ok",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("obs_on_chain_end_failed", error=str(exc))

    # ── helpers ─────────────────────────────────────────────────────────

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

        self.llm_call_repo.add(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            turn_id=self.turn_id,
            span_id=span_id,
            parent_span_id=None,
            role=self.role,
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
        )

        # Mirror in trace_event so the existing /trazas admin still shows
        # one entry per LLM call. The aggregate cost lives in
        # copilot_llm_call; the trace event carries just the breadcrumb
        # under the canonical event_type='llm_call' string the docs
        # already advertise.
        self.trace_repo.add(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            conversation_id=self.conversation_id,
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

    @staticmethod
    def _extract_provider_and_model(
        serialized: dict[str, Any],
        metadata: dict[str, Any] | None,
    ) -> tuple[str, str]:
        """Return ``(provider, model_requested)`` from the start payload.

        Order of preference: ``metadata.ls_provider`` / ``ls_model_name``
        (LangChain's normalised tags), then ``serialized.kwargs.model_name``
        / ``model``, then sensible fallbacks.
        """
        meta = metadata or {}
        provider = meta.get("ls_provider") or meta.get("provider") or "unknown"
        model = meta.get("ls_model_name") or meta.get("model_name") or meta.get("model")
        if not model and isinstance(serialized, dict):
            kwargs = serialized.get("kwargs") or {}
            if isinstance(kwargs, dict):
                model = kwargs.get("model_name") or kwargs.get("model")
        if not model:
            model = "unknown"
        return str(provider), str(model)

    @staticmethod
    def _extract_usage(response: LLMResult | None) -> dict[str, int]:
        """Pull token counts from every shape LangChain may surface.

        OpenAI-compatible providers (Moonshot/Kimi, DeepSeek, Qwen)
        reach LangChain through ``ChatOpenAI`` with a custom base_url,
        and not all of them populate ``message.usage_metadata`` — some
        leave the data only in ``message.response_metadata.token_usage``
        (raw OpenAI ``usage`` block) or in ``LLMResult.llm_output.
        token_usage`` (older adapters, gateway proxies).

        Conv 0d64c4a9 (2026-04-27) showed Kimi K2.6 turns landing in
        ``copilot_llm_call`` with zero tokens — that single source of
        truth had silently broken ``/copilot-routing`` and the cost
        cycle aggregator. The handler must drain all three sources
        before it gives up and reports zeros, otherwise trazas keep
        lying about cost.
        """
        zeros = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_read_tokens": 0,
            "cached_write_tokens": 0,
            "reasoning_tokens": 0,
        }
        if response is None:
            return zeros

        try:
            generation = response.generations[0][0]
            message: AIMessage = generation.message  # type: ignore[attr-defined]
        except (AttributeError, IndexError):
            return zeros

        # 1. LangChain native shape — populated by langchain-openai for
        #    upstream OpenAI and by LangChain's auto-sync when a provider
        #    surfaces ``token_usage`` in ``response_metadata``.
        usage = getattr(message, "usage_metadata", None) or {}
        if usage.get("input_tokens") or usage.get("output_tokens"):
            details = usage.get("input_token_details") or {}
            output_details = usage.get("output_token_details") or {}
            return {
                "input_tokens": int(usage.get("input_tokens", 0) or 0),
                "output_tokens": int(usage.get("output_tokens", 0) or 0),
                "cached_read_tokens": int(details.get("cache_read", 0) or 0),
                "cached_write_tokens": int(details.get("cache_creation", 0) or 0),
                "reasoning_tokens": int(output_details.get("reasoning", 0) or 0),
            }

        # 2. Raw OpenAI shape on the message itself. Moonshot and a few
        #    self-hosted gateways land here — the auto-sync in (1) skips
        #    when the response includes fields the parser does not
        #    recognise (``thinking_tokens``, vendor extensions).
        token_usage = (getattr(message, "response_metadata", None) or {}).get("token_usage") or {}
        if token_usage:
            return ObservabilityCallbackHandler._from_openai_token_usage(token_usage)

        # 3. LLMResult-level aggregate. Older langchain-openai versions
        #    only expose tokens here; some gateway proxies (LiteLLM, Helicone)
        #    drop them on the message but keep them in ``llm_output``.
        llm_output_usage = (response.llm_output or {}).get("token_usage") if response.llm_output else None
        if llm_output_usage:
            return ObservabilityCallbackHandler._from_openai_token_usage(llm_output_usage)

        return zeros

    @staticmethod
    def _from_openai_token_usage(usage: dict[str, Any]) -> dict[str, int]:
        """Convert the raw OpenAI ``usage`` shape into the canonical row dict."""
        prompt_details = usage.get("prompt_tokens_details") or {}
        completion_details = usage.get("completion_tokens_details") or {}
        return {
            "input_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "output_tokens": int(usage.get("completion_tokens", 0) or 0),
            "cached_read_tokens": int(prompt_details.get("cached_tokens", 0) or 0),
            # OpenAI exposes cache *write* tokens only on the dedicated
            # batch endpoints; treat absence as zero rather than guessing.
            "cached_write_tokens": int(prompt_details.get("cache_creation_tokens", 0) or 0),
            "reasoning_tokens": int(completion_details.get("reasoning_tokens", 0) or 0),
        }

    @staticmethod
    def _extract_model_responded(response: LLMResult | None, *, fallback: str) -> str:
        """Pick the actual model that responded; fall back to the requested one."""
        if response is None:
            return fallback
        try:
            generation = response.generations[0][0]
            message = generation.message  # type: ignore[attr-defined]
        except (AttributeError, IndexError):
            return fallback
        meta = getattr(message, "response_metadata", None) or {}
        return str(meta.get("model_name") or meta.get("model") or fallback)

    @staticmethod
    def _chain_name(serialized: dict[str, Any]) -> str | None:
        """Return a node name if ``serialized`` looks like a LangGraph node."""
        if not isinstance(serialized, dict):
            return None
        # LangGraph emits nodes with ``name`` set; vanilla LangChain chains
        # may not — we ignore those.
        name = serialized.get("name")
        if not isinstance(name, str) or not name:
            return None
        return name

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
