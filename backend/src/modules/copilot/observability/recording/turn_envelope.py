"""Copilot concrete observability context — subclass of shared base.

Anti-duplication LIFT (PR-2 PI-1.1, 2026-05-01): the lifecycle that
used to live monolithically here is now in
``src/shared/agent_observability/recording/turn_envelope.py``
(:class:`BaseObservabilityContext`). This module keeps the copilot-
specific concrete subclass plus a public alias for back-compat:

    from src.modules.copilot.observability import ObservabilityContext

continues to work — 4260 conversation import sites untouched.

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
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from luana_core_copilot.observability.persistence.models.llm_call_model import (
    CopilotLlmCallModel,
)
from luana_core_copilot.observability.recording.callback_handler import (
    ObservabilityCallbackHandler,
)
from luana_core_observability.recording.turn_envelope import (
    BaseObservabilityContext,
    _empty_totals,
)
from sqlalchemy import func, select

if TYPE_CHECKING:
    from luana_core_copilot.observability.persistence.llm_call_repository import LlmCallRepository
    from luana_core_copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )
    from luana_core_observability.cost.fx_resolver import FXResolver
    from luana_core_observability.pricing.resolver import PricingResolver

logger = structlog.get_logger()


@dataclass
class CopilotObservabilityContext(BaseObservabilityContext):
    """Concrete copilot context. Owns the callback handler + turn lifecycle.

    Inherits the entire lifecycle (``observe_turn``, ``_write_turn_*``,
    ``set_turn_*``, ``langchain_config``, ``_commit_session``) from
    :class:`BaseObservabilityContext`. Implements the three abstract
    hooks:

    * :meth:`_add_trace_event` — passes ``conversation_id`` + ``user_id``
      kwargs to ``TraceEventRepository.add``.
    * :meth:`_aggregate_totals` — sums :class:`CopilotLlmCallModel`
      rows for the turn.
    * :meth:`_legacy_compat_keys_or_empty` — returns the JSONB legacy
      shape Streamlit ``/trazas`` + ``/copilot-routing`` consume.
    """

    conversation_id: UUID | None = None
    user_id: UUID | None = None
    # ``trace_repo`` / ``llm_call_repo`` are inherited but typed loosely; the
    # copilot subclass narrows their concrete types for clarity. Mypy treats
    # them as a redeclaration; runtime is unaffected (dataclass inheritance
    # respects field order).
    # NOTE: we don't redeclare here to avoid dataclass field-ordering
    # warnings — base owns the fields, subclass uses them.

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
    ) -> CopilotObservabilityContext:
        """Build a fresh copilot context. Turn id is allocated if not provided."""
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
            turn_id=tid,
            callback_handler=handler,
            trace_repo=trace_repo,
            llm_call_repo=llm_call_repo,
            conversation_id=conversation_id,
            user_id=user_id,
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
                user_id=self.user_id,
                conversation_id=self.conversation_id,
                turn_id=self.turn_id,
                span_id=span_id or uuid4(),
                event_type=event_type,
                name=name,
                data=data,
                duration_ms=duration_ms,
                status=status,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("obs_add_trace_event_failed", event_type=event_type, error=str(exc))

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
        except Exception as exc:  # noqa: BLE001 — best-effort
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
        except Exception:  # noqa: BLE001 — best-effort
            return ""

    def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
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


# ── Back-compat aliases ────────────────────────────────────────────────

# 4260 conversation import sites depend on this name. The
# ``observability/__init__.py`` re-export at line 43 reads this module-
# level alias. Refactor preserves the public surface verbatim.
ObservabilityContext = CopilotObservabilityContext


__all__ = ["CopilotObservabilityContext", "ObservabilityContext"]
