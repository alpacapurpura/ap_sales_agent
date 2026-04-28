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
subclasses; S11A lifts the shared LangChain plumbing
(``on_chat_model_*`` / ``on_tool_*`` / ``on_chain_*`` callbacks +
``_extract_usage`` / ``_from_openai_token_usage`` /
``_extract_provider_and_model`` helpers) so the Template Method
skeleton (sanitize → resolve pricing → calculate cost → persist) lives
once.

Reference: ``docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md §3.1``
+ ``phases/S11-shared-lift-orchestrator-decomp.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import BaseCallbackHandler

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal
    from uuid import UUID

    from langchain_core.outputs import LLMResult


class BaseAgentCallbackHandler(BaseCallbackHandler, ABC):
    """Abstract LangChain callback handler shared cross-agent.

    Subclasses must implement :meth:`_persist_llm_call_row` and
    :meth:`_persist_trace_event_row`. Concrete handlers wire the
    LangChain ``on_chat_model_*`` / ``on_tool_*`` / ``on_chain_*``
    methods using the same skeleton — sanitize payloads, resolve pricing
    via ``pricing.resolver.PricingResolver``, calculate cost via
    ``cost.calculator.calculate_cost``, then call the abstract persisters.

    Best-effort: every persistence path must wrap the call in
    ``try/except`` + ``structlog.warning`` so a broken row never
    propagates out to the orchestrator (see
    ``.claude/rules/copilot-observability.md`` §"Best-effort writes").
    """

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
        cost_usd: Decimal,
        tenant_currency: str,
        fx_rate_to_tenant: Decimal,
        fx_rate_source: str,
        cost_tenant_currency: Decimal,
        started_at: datetime,
        duration_ms: int,
        status: str,
        error_type: str | None,
        role: str,
        **agent_specific: Any,  # noqa: ANN401 — sales_agent injects lead_id/channel_type
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
        **agent_specific: Any,  # noqa: ANN401 — sales_agent injects lead_id/channel_type
    ) -> None:
        """Persist one row to the agent-specific ``*_trace_event`` table."""
        raise NotImplementedError

    # ── Shared helpers (S11A lift) ──────────────────────────────────────

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
    def _chain_name(serialized: dict[str, Any]) -> str | None:
        """Return a node name if ``serialized`` looks like a LangGraph node."""
        if not isinstance(serialized, dict):
            return None
        name = serialized.get("name")
        if not isinstance(name, str) or not name:
            return None
        return name


__all__ = ["BaseAgentCallbackHandler"]
