"""Sales-agent concrete observability context — subclass of shared base.

Anti-duplication NEW (PR-2 PI-1.1, 2026-05-01): the lifecycle lives in
``src/shared/agent_observability/recording/turn_envelope.py``
(:class:`BaseObservabilityContext`). This module adds the
sales-agent-specific concrete subclass — distinct from
:class:`CopilotObservabilityContext` (different fields, different
aggregator target, no legacy JSONB shape).

Bug #2 fix (PR-2): wiring this envelope around ``agent_app.ainvoke``
in the orchestrator landed the missing ``turn_start`` + ``turn_end``
rows. Pre-PR-2 sales_agent shipped only the callback handler — when a
turn ran without LLM call (rare but real) zero rows were persisted.

Field overrides:

* ``lead_id: UUID`` — sales_agent always writes per-lead audit trail.
* ``channel_type: str`` — captured from the inbound webhook adapter.

Aggregation hits :class:`SalesAgentLlmCallModel` (not
``CopilotLlmCallModel``). ``_legacy_compat_keys_or_empty`` returns
``{}`` — sales_agent observability went straight to columnar reporting,
no JSONB consumer documented.

Best-effort: every persistence path wraps ``try/except`` + structlog
warning per ``copilot-expert`` skill rule.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from luana_core_observability.recording.turn_envelope import (
    BaseObservabilityContext,
    _empty_totals,
)
from luana_core_sales_agent.observability.persistence.models.llm_call_model import (
    SalesAgentLlmCallModel,
)
from luana_core_sales_agent.observability.recording.callback_handler import (
    SalesAgentCallbackHandler,
)
from sqlalchemy import func, select

if TYPE_CHECKING:
    from luana_core_observability.cost.fx_resolver import FXResolver
    from luana_core_observability.pricing.resolver import PricingResolver
    from luana_core_sales_agent.observability.persistence.llm_call_repository import (
        SalesAgentLlmCallRepository,
    )
    from luana_core_sales_agent.observability.persistence.trace_event_repository import (
        SalesAgentTraceEventRepository,
    )
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


@dataclass
class SalesAgentObservabilityContext(BaseObservabilityContext):
    """Concrete sales-agent context. Owns the callback handler + turn lifecycle.

    Inherits the entire lifecycle (``observe_turn``, ``_write_turn_*``,
    ``set_turn_*``, ``langchain_config``, ``_commit_session``) from
    :class:`BaseObservabilityContext`. Implements the three abstract
    hooks:

    * :meth:`_add_trace_event` — passes ``lead_id`` + ``channel_type``
      kwargs to ``SalesAgentTraceEventRepository.add``.
    * :meth:`_aggregate_totals` — sums :class:`SalesAgentLlmCallModel`
      rows for the turn.
    * :meth:`_legacy_compat_keys_or_empty` — returns ``{}`` (no JSONB
      consumer in sales_agent).
    """

    lead_id: UUID | None = None
    channel_type: str = ""

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
        db_session: Session,
        tenant_currency: str = "USD",
        role: str = "agent",
        turn_id: UUID | None = None,
    ) -> SalesAgentObservabilityContext:
        """Build a fresh sales-agent context. Turn id is allocated if not provided.

        ``db_session`` is forwarded to :class:`SalesAgentCallbackHandler`
        for ``_safe_rollback``. Repos are shared with the orchestrator
        so the envelope's ``_commit_session`` covers the same UoW.
        """
        tid = turn_id or uuid4()
        handler = SalesAgentCallbackHandler(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type=channel_type,
            turn_id=tid,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            db_session=db_session,
            tenant_currency=tenant_currency,
            role=role,
        )
        return cls(
            tenant_id=tenant_id,
            turn_id=tid,
            callback_handler=handler,
            trace_repo=trace_repo,
            llm_call_repo=llm_call_repo,
            lead_id=lead_id,
            channel_type=channel_type,
        )

    # ── Abstract hook impls ────────────────────────────────────────────

    def _add_trace_event(
        self,
        *,
        event_type: str,
        name: str,
        data: dict[str, Any],
        duration_ms: int | None = None,
        status: str = "ok",
        span_id: UUID | None = None,
    ) -> None:
        try:
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                lead_id=self.lead_id,
                channel_type=self.channel_type,
                turn_id=self.turn_id,
                span_id=span_id or uuid4(),
                event_type=event_type,
                name=name,
                data=data,
                duration_ms=duration_ms,
                status=status,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "sales_obs_add_trace_event_failed",
                event_type=event_type,
                error=str(exc),
            )

    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum the sales_agent_llm_call rows for this turn."""
        try:
            session = self.llm_call_repo.db
            with contextlib.suppress(Exception):
                session.flush()
            stmt = select(
                func.count().label("count"),
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
                "llm_call_count": int(row.count),
                "total_input_tokens": int(row.input_tokens),
                "total_output_tokens": int(row.output_tokens),
                "total_cached_read_tokens": int(row.cached_read_tokens),
                "total_cost_usd": str(Decimal(row.cost_usd)),
                "model_responded": self._most_used_model(session),
            }
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("sales_obs_aggregate_totals_failed", error=str(exc))
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

    def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
        """Sales_agent has no legacy JSONB consumer — return empty dict.

        Callback handler already writes columnar rows with all the
        agent-specific fields. Streamlit sales reports read those
        columns directly (per ``sales-agent-expert`` skill).
        """
        del totals  # interface contract — kept for future symmetry with copilot subclass
        return {}


__all__ = ["SalesAgentObservabilityContext"]
