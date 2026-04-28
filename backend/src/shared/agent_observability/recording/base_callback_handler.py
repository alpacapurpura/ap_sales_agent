"""Abstract base for agent-specific LangChain callback handlers.

Template Method (GoF) — concrete subclasses live in each agent's
``observability/recording/callback_handler.py`` (e.g. copilot's
``ObservabilityCallbackHandler``, sales_agent's
``SalesAgentCallbackHandler`` arriving in S1). The abstract methods
:meth:`_persist_llm_call_row` and :meth:`_persist_trace_event_row`
delegate row persistence to the agent-specific repos so the same
captured event can land in ``copilot_llm_call`` / ``copilot_trace_event``
or ``sales_agent_llm_call`` / ``sales_agent_trace_event`` without
duplicating the LangChain plumbing.

S0 declares the contract only — copilot's existing handler keeps its
self-contained shape. S1 retrofits both handlers to inherit from this
base so the Template Method skeleton (sanitize → resolve pricing →
calculate cost → persist) lives once.

Reference: ``docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md §3.1``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import BaseCallbackHandler

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal
    from uuid import UUID


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


__all__ = ["BaseAgentCallbackHandler"]
