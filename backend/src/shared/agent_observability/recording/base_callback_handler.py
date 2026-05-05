"""Abstract base for agent-specific LangChain callback handlers.

Template Method (GoF) — concrete subclasses live in each agent's
``observability/recording/callback_handler.py`` (e.g. copilot's
``ObservabilityCallbackHandler``, sales_agent's
``SalesAgentCallbackHandler``). The abstract methods
:meth:`_persist_llm_call_row` and :meth:`_persist_trace_event_row`
delegate row persistence to the agent-specific repos so the same
captured event can land in ``copilot_llm_call`` / ``copilot_trace_event``
or ``sales_agent_llm_call`` / ``sales_agent_trace_event`` without
duplicating the LangChain plumbing.

S0 declared the abstract surface; S1 wired up the agent-specific
subclasses; S11A lifts the shared LangChain plumbing — the 8 ``on_*``
callbacks, span dataclasses, ``_persist_llm_call`` Template Method
skeleton (sanitize → resolve pricing → calculate cost → persist),
``_safe_rollback`` and helper extractors.

Reference: ``docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md §3.1``
+ ``phases/S11-shared-lift-orchestrator-decomp.md``.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from langchain_core.callbacks import BaseCallbackHandler

from src.shared.agent_observability.cost.calculator import (
    calculate_cost,  # noqa: F401 — retained for reconciliation utility, NOT used in runtime path post-T1.
)
from src.shared.agent_observability.cost.fx_resolver import FXResolver
from src.shared.agent_observability.pricing.resolver import PricingResolver
from src.shared.agent_observability.recording.cost_recorder import pop_cost
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
class BaseAgentCallbackHandler(BaseCallbackHandler, ABC):
    """Abstract LangChain callback handler shared cross-agent.

    Subclasses must implement :meth:`_persist_llm_call_row` and
    :meth:`_persist_trace_event_row`. The 8 LangChain callbacks
    (``on_chat_model_start`` / ``on_llm_end`` / ``on_llm_error`` /
    ``on_tool_start`` / ``on_tool_end`` / ``on_tool_error`` /
    ``on_chain_start`` / ``on_chain_end``) live here and apply the
    Template Method skeleton: sanitize payloads, resolve pricing via
    ``PricingResolver``, calculate cost via ``calculate_cost``, then
    call the abstract persisters.

    Best-effort: every persistence path wraps the call in
    ``try/except`` + ``structlog.warning`` + ``_safe_rollback`` so a
    broken row never propagates out to the orchestrator (see
    ``.claude/rules/copilot-observability.md`` §"Best-effort writes").
    """

    tenant_id: UUID
    turn_id: UUID
    pricing_resolver: PricingResolver
    fx_resolver: FXResolver
    tenant_currency: str = "USD"
    role: str = "agent"

    _llm_spans: dict[UUID, _LLMSpan] = field(default_factory=dict)
    _tool_spans: dict[UUID, _ToolSpan] = field(default_factory=dict)
    _chain_spans: dict[UUID, _ChainSpan] = field(default_factory=dict)

    # ── abstract persisters ─────────────────────────────────────────────

    @abstractmethod
    def _persist_llm_call_row(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        span_id: UUID,
        provider: str,
        model_requested: str,
        model_responded: str,
        input_tokens: int,
        output_tokens: int,
        cached_read_tokens: int,
        cached_write_tokens: int,
        reasoning_tokens: int,
        pricing_version_id: UUID,
        input_unit_cost_usd: Decimal,
        output_unit_cost_usd: Decimal,
        cached_read_unit_cost_usd: Decimal,
        cost_usd: Decimal | None,
        tenant_currency: str,
        fx_rate_to_tenant: Decimal,
        fx_rate_source: str,
        cost_tenant_currency: Decimal | None,
        started_at: datetime,
        duration_ms: int,
        status: str,
        error_type: str | None,
        role: str,
        **agent_specific: Any,  # noqa: ANN401 — sales injects lead_id/channel_type, copilot conv/user
    ) -> None:
        """Persist one row to the agent-specific ``*_llm_call`` table."""
        raise NotImplementedError

    @abstractmethod
    def _persist_trace_event_row(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        span_id: UUID,
        event_type: str,
        name: str | None,
        data: dict[str, Any],
        duration_ms: int | None,
        status: str,
        **agent_specific: Any,  # noqa: ANN401 — sales injects lead_id/channel_type, copilot conv/user
    ) -> None:
        """Persist one row to the agent-specific ``*_trace_event`` table."""
        raise NotImplementedError

    # ── LangChain callbacks (chat model) ────────────────────────────────

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: Any,  # noqa: ANN401 — list[list[BaseMessage]]; we don't read it
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401 — LangChain BaseCallbackHandler signature
    ) -> None:
        """Open an LLM span keyed by ``run_id``."""
        del messages, parent_run_id, tags, kwargs
        try:
            provider, model = self._extract_provider_and_model(serialized, metadata)
            self._llm_spans[run_id] = _LLMSpan(
                started_at=datetime.now(tz=UTC),
                provider=provider,
                model_requested=model,
                monotonic_start=time.monotonic(),
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("agent_obs_on_chat_model_start_failed", error=str(exc))

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
            logger.warning("agent_obs_on_llm_end_failed", error=str(exc))
            self._safe_rollback()

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
            logger.warning("agent_obs_on_llm_error_failed", error=str(exc))
            self._safe_rollback()

    # ── LangChain callbacks (tool) ──────────────────────────────────────

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
            logger.warning("agent_obs_on_tool_start_failed", error=str(exc))

    def on_tool_end(
        self,
        output: Any,  # noqa: ANN401 — provider-specific
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
                duration_ms=self._elapsed_ms(span.monotonic_start),
                status="ok",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("agent_obs_on_tool_end_failed", error=str(exc))
            self._safe_rollback()

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
            logger.warning("agent_obs_on_tool_error_failed", error=str(exc))
            self._safe_rollback()

    # ── LangChain callbacks (chain / LangGraph nodes) ───────────────────

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
            logger.warning("agent_obs_on_chain_start_failed", error=str(exc))
            self._safe_rollback()

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
            logger.warning("agent_obs_on_chain_end_failed", error=str(exc))
            self._safe_rollback()

    # ── Template Method skeleton ────────────────────────────────────────

    def _persist_llm_call(
        self,
        *,
        span: _LLMSpan,
        response: LLMResult | None,
        status: str,
        error_type: str | None,
    ) -> None:
        """Resolve pricing + cost + fx, then call abstract persisters.

        T-1 (PI-12 S1, X2 ratificada): runtime ``cost_usd`` is consumed
        from the LiteLLM ``CustomLogger`` cache via :func:`pop_cost`,
        keyed by ``litellm_call_id``. The legacy
        :func:`calculate_cost` is retained as a reconciliation utility
        only and MUST NOT be invoked from this path.

        Cost semantics:

        * ``status == "error"`` → ``cost_usd = Decimal(0)`` (failed call,
          no charge).
        * Cache hit (LiteLLM populated ``response_cost``) → consume the
          stashed ``Decimal``.
        * Cache miss (unknown model, non-LiteLLM call, slow consumer
          past TTL) → ``cost_usd = None`` (NULL on the audit row;
          callers MUST distinguish "unknown" from "Decimal('0')").

        The ``PricingResolver`` is still queried so the audit row carries
        ``pricing_version_id`` + ``input_unit_cost_usd`` etc. for
        reconciliation lookups, but the resolved cost is NOT recomputed
        in this path.
        """
        usage = self._extract_usage(response)
        model_responded = self._extract_model_responded(response, fallback=span.model_requested)

        pricing = self.pricing_resolver.resolve(
            provider=span.provider,
            model=model_responded,
            at_ts=span.started_at,
        )
        snapshot = pricing.snapshot
        litellm_call_id = self._extract_litellm_call_id(response)
        if status == "error":
            cost_usd: Decimal | None = Decimal(0)
        elif litellm_call_id is not None:
            cost_usd = pop_cost(litellm_call_id)
            if cost_usd is None:
                logger.warning(
                    "cost_recorder.cache_miss",
                    call_id=litellm_call_id,
                    model=model_responded,
                    provider=span.provider,
                )
        else:
            cost_usd = None
            logger.warning(
                "cost_recorder.no_call_id_on_response",
                model=model_responded,
                provider=span.provider,
            )
        fx_rate, fx_source = self.fx_resolver.resolve(
            currency_code=self.tenant_currency,
            at_ts=span.started_at,
        )
        cost_tenant: Decimal | None = cost_usd * fx_rate if cost_usd is not None else None
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
        # one entry per LLM call. The aggregate cost lives in the
        # agent-specific ``*_llm_call`` table; the trace event carries
        # just the breadcrumb under event_type='llm_call'.
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
                    "cost_usd": str(cost_usd) if cost_usd is not None else None,
                    "is_estimated_pricing": pricing.is_estimated,
                    "fx_rate_source": fx_source,
                },
            ),
            duration_ms=duration_ms,
            status=status,
        )

    def _safe_rollback(self) -> None:
        """Best-effort session rollback. No-op when no ``db_session`` set.

        Subclasses that wire a SQLAlchemy session expose it as
        ``self.db_session``; the base looks the attribute up dynamically so
        recorders without a session (in-memory tests, async background
        adapters) keep working.
        """
        session = getattr(self, "db_session", None)
        if session is None:
            return
        rollback = getattr(session, "rollback", None)
        if rollback is None:
            return
        try:
            rollback()
        except Exception as exc:  # noqa: BLE001
            logger.warning("agent_obs_rollback_failed", error=str(exc))

    # ── Shared helpers ──────────────────────────────────────────────────

    @staticmethod
    def _extract_provider_and_model(
        serialized: dict[str, Any],
        metadata: dict[str, Any] | None,
    ) -> tuple[str, str]:
        """Return ``(provider, model_requested)`` from the start payload.

        T-1 (PI-12 S1 sales-agent-litellm-canonicalization, A1 ratificada):
        the ``model`` field is stored **slashed** (canonical LiteLLM format,
        e.g. ``"deepseek/deepseek-v4-flash"``). The legacy D-7 strip is
        removed — slashed models survive future provider expansion
        (``bedrock/anthropic.claude-v3``, ``vertex_ai/gemini-1.5-pro``).

        ``provider`` is derived via :func:`_canonical_provider`, which
        wraps :func:`litellm.get_llm_provider` to return the 4-tuple's
        canonical ``custom_llm_provider`` (position 1). Falls back to
        metadata hints when the SDK can't resolve the model, and to
        ``"unknown"`` as last resort.

        Order of preference for ``model``: ``metadata.ls_model_name`` /
        ``ls_provider`` (LangChain normalised tags), then
        ``serialized.kwargs.model_name`` / ``model``, then ``"unknown"``.
        """
        meta = metadata or {}
        meta_provider_hint = meta.get("ls_provider") or meta.get("provider")
        model = meta.get("ls_model_name") or meta.get("model_name") or meta.get("model")
        if not model and isinstance(serialized, dict):
            kwargs = serialized.get("kwargs") or {}
            if isinstance(kwargs, dict):
                model = kwargs.get("model_name") or kwargs.get("model")
        if not model:
            model = "unknown"
        model_str = str(model)
        provider = BaseAgentCallbackHandler._canonical_provider(model_str, hint=meta_provider_hint)
        return provider, model_str

    @staticmethod
    def _canonical_provider(model: str, *, hint: Any = None) -> str:  # noqa: ANN401
        """Return the canonical LiteLLM ``custom_llm_provider`` for ``model``.

        Wraps :func:`litellm.get_llm_provider` (position 1 of the 4-tuple).
        On miss (unknown model, SDK unavailable) falls back to the metadata
        ``hint`` if it is a non-empty string, else returns ``"unknown"``.

        Best-effort: the call NEVER raises out of the recorder hot path.
        Logs a structured warning so the operator can see which model is
        unmapped and decide whether to add a ``litellm_config.yaml`` entry.
        """
        try:
            import litellm  # local import keeps base_callback_handler test-friendly

            _stripped, provider, _key, _base = litellm.get_llm_provider(model)
            return str(provider) if provider else "unknown"
        except Exception as exc:  # noqa: BLE001 — best-effort, log and fall back
            logger.warning(
                "cost_recorder.unknown_provider",
                model=model,
                hint=str(hint) if hint else None,
                error_class=type(exc).__name__,
            )
            if isinstance(hint, str) and hint and hint != "unknown":
                return hint
            return "unknown"

    @staticmethod
    def _extract_usage(response: LLMResult | None) -> dict[str, int]:
        """Pull token counts from every shape LangChain may surface.

        OpenAI-compatible providers (Moonshot/Kimi, DeepSeek, Qwen)
        reach LangChain through ``ChatOpenAI`` with a custom ``base_url``,
        and not all of them populate ``message.usage_metadata`` — some
        leave the data only in ``message.response_metadata.token_usage``
        (raw OpenAI ``usage`` block) or in ``LLMResult.llm_output.
        token_usage`` (older adapters, gateway proxies). Drain all three
        sources before reporting zeros.
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
            message = generation.message  # type: ignore[attr-defined]
        except (AttributeError, IndexError):
            return zeros

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

        token_usage = (getattr(message, "response_metadata", None) or {}).get("token_usage") or {}
        if token_usage:
            return BaseAgentCallbackHandler._from_openai_token_usage(token_usage)

        llm_output_usage = (response.llm_output or {}).get("token_usage") if response.llm_output else None
        if llm_output_usage:
            return BaseAgentCallbackHandler._from_openai_token_usage(llm_output_usage)

        return zeros

    @staticmethod
    def _from_openai_token_usage(usage: dict[str, Any]) -> dict[str, int]:
        """Convert raw OpenAI ``usage`` shape into the canonical row dict."""
        prompt_details = usage.get("prompt_tokens_details") or {}
        completion_details = usage.get("completion_tokens_details") or {}
        return {
            "input_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "output_tokens": int(usage.get("completion_tokens", 0) or 0),
            "cached_read_tokens": int(prompt_details.get("cached_tokens", 0) or 0),
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
    def _extract_litellm_call_id(response: LLMResult | None) -> str | None:
        """Pull the ``litellm_call_id`` LangChain echoes via response metadata.

        T-1 (PI-12 S1): used to bridge the LangChain ``on_llm_end`` hook
        with the LiteLLM ``CustomLogger`` cache populated by
        :class:`~src.shared.agent_observability.recording.cost_recorder.CostRecorderCustomLogger`.
        Returns ``None`` when the response did not flow through LiteLLM
        (legacy adapters, mocked tests without metadata) — callers MUST
        treat ``None`` as "cost unknown" and persist ``cost_usd = NULL``.
        """
        if response is None:
            return None
        try:
            generation = response.generations[0][0]
            message = generation.message  # type: ignore[attr-defined]
        except (AttributeError, IndexError):
            return None
        meta = getattr(message, "response_metadata", None) or {}
        call_id = meta.get("litellm_call_id") or meta.get("id")
        if not call_id:
            llm_output = getattr(response, "llm_output", None) or {}
            if isinstance(llm_output, dict):
                call_id = llm_output.get("litellm_call_id")
        return str(call_id) if call_id else None

    @staticmethod
    def _chain_name(serialized: dict[str, Any]) -> str | None:
        """Return a node name if ``serialized`` looks like a LangGraph node."""
        if not isinstance(serialized, dict):
            return None
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


__all__ = ["BaseAgentCallbackHandler"]
