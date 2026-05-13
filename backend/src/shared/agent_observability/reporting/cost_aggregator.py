"""Cost aggregator — agnostic over which agent's ``*_llm_call`` it reads.

Constructor takes the SQLAlchemy model class so the same aggregator
backs both ``copilot`` and ``sales_agent`` dashboards. The MV
``mv_daily_llm_cost_per_tenant`` (per-agent, copilot) and
``mv_daily_llm_cost_per_tenant_v2`` (cross-agent, S2) are Postgres-side
performance boosters; the aggregator falls back to scanning the table
directly so SQLite tests work too.

Single tenant scope is enforced by callers; this layer accepts
``tenant_id`` directly but never *omits* the filter when one is required.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import case, func, select

if TYPE_CHECKING:
    from luana_core_platform.domain.base_entity import Base
    from sqlalchemy.orm import Session


# ── DTOs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TenantCostRow:
    """Per-tenant cost summary row for the Comando Central table."""

    tenant_id: UUID
    call_count: int
    turn_count: int
    conversation_count: int
    cost_usd: Decimal
    cost_tenant_currency: Decimal | None
    tenant_currency: str | None
    error_count: int


@dataclass(frozen=True)
class ModelCostRow:
    """Per-model breakdown inside a tenant detail view."""

    model: str
    provider: str
    role: str
    call_count: int
    cost_usd: Decimal
    avg_input_tokens: int
    avg_output_tokens: int


@dataclass(frozen=True)
class TenantDetailRow:
    """Detail view for a single tenant in a single window."""

    tenant_id: UUID
    call_count: int
    turn_count: int
    conversation_count: int
    cost_usd: Decimal
    cost_tenant_currency: Decimal | None
    tenant_currency: str | None
    error_count: int
    by_model: list[ModelCostRow] = field(default_factory=list)


@dataclass(frozen=True)
class ConversationCostRow:
    """Top-N conversations by cost for the drill-down view (copilot)."""

    conversation_id: UUID
    call_count: int
    turn_count: int
    cost_usd: Decimal
    last_seen: dt.datetime | None


@dataclass(frozen=True)
class LeadCostRow:
    """Top-N leads by cost for the drill-down view (sales_agent)."""

    lead_id: UUID
    call_count: int
    turn_count: int
    cost_usd: Decimal
    last_seen: dt.datetime | None


@dataclass(frozen=True)
class DailyCostPoint:
    """One day in the daily-series chart."""

    day: dt.date
    cost_usd: Decimal
    call_count: int


# ── Helpers ─────────────────────────────────────────────────────────────


def _start_dt(start: dt.date) -> dt.datetime:
    return dt.datetime(start.year, start.month, start.day, tzinfo=dt.UTC)


def _end_dt(end: dt.date) -> dt.datetime:
    return dt.datetime(end.year, end.month, end.day, tzinfo=dt.UTC)


def _to_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _coerce_date(value: object) -> dt.date:
    """Postgres returns ``date``; SQLite returns ``str`` — normalise both."""
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, str):
        return dt.date.fromisoformat(value)
    msg = f"Cannot coerce {value!r} to date"
    raise TypeError(msg)


# ── Aggregator ──────────────────────────────────────────────────────────


class CostAggregator:
    """Aggregate LLM cost rows for the reporting layer.

    Bound to one ``*_llm_call`` model. For cross-agent queries use
    :class:`CrossAgentCostAggregator`.
    """

    def __init__(self, db: Session, llm_call_model: type[Base]) -> None:
        """Bind the aggregator to a session + model class."""
        self.db = db
        self.model = llm_call_model
        # Cache attribute lookups so the per-call hot path stays cheap.
        self._has_conversation_id = hasattr(self.model, "conversation_id")
        self._has_lead_id = hasattr(self.model, "lead_id")

    def tenants_summary(
        self,
        *,
        start: dt.date,
        end: dt.date,
    ) -> list[TenantCostRow]:
        """Return one row per tenant active in ``[start, end_exclusive)``."""
        m = self.model
        if self._has_conversation_id:
            conv_count_expr = func.count(func.distinct(m.conversation_id))
        else:
            conv_count_expr = func.count(func.distinct(m.turn_id))
        stmt = (
            select(
                m.tenant_id.label("tenant_id"),
                func.count().label("call_count"),
                func.count(func.distinct(m.turn_id)).label("turn_count"),
                conv_count_expr.label("conversation_count"),
                func.coalesce(func.sum(m.cost_usd), 0).label("cost_usd"),
                func.coalesce(
                    func.sum(m.cost_tenant_currency),
                    0,
                ).label("cost_tenant_currency"),
                func.max(m.tenant_currency).label("tenant_currency"),
                func.coalesce(
                    func.sum(case((m.status == "error", 1), else_=0)),
                    0,
                ).label("error_count"),
            )
            .where(
                m.started_at >= _start_dt(start),
                m.started_at < _end_dt(end),
            )
            .group_by(m.tenant_id)
            .order_by(func.sum(m.cost_usd).desc())
        )
        rows = self.db.execute(stmt).all()
        return [
            TenantCostRow(
                tenant_id=row.tenant_id,
                call_count=int(row.call_count),
                turn_count=int(row.turn_count),
                conversation_count=int(row.conversation_count),
                cost_usd=_to_decimal(row.cost_usd),
                cost_tenant_currency=_to_decimal(row.cost_tenant_currency),
                tenant_currency=row.tenant_currency,
                error_count=int(row.error_count),
            )
            for row in rows
        ]

    def tenant_detail(
        self,
        *,
        tenant_id: UUID,
        start: dt.date,
        end: dt.date,
    ) -> TenantDetailRow:
        """Return full per-tenant detail with per-model breakdown."""
        m = self.model
        if self._has_conversation_id:
            conv_count_expr = func.count(func.distinct(m.conversation_id))
        else:
            conv_count_expr = func.count(func.distinct(m.turn_id))
        totals_stmt = select(
            func.count().label("call_count"),
            func.count(func.distinct(m.turn_id)).label("turn_count"),
            conv_count_expr.label("conversation_count"),
            func.coalesce(func.sum(m.cost_usd), 0).label("cost_usd"),
            func.coalesce(
                func.sum(m.cost_tenant_currency),
                0,
            ).label("cost_tenant_currency"),
            func.max(m.tenant_currency).label("tenant_currency"),
            func.coalesce(
                func.sum(case((m.status == "error", 1), else_=0)),
                0,
            ).label("error_count"),
        ).where(
            m.tenant_id == tenant_id,
            m.started_at >= _start_dt(start),
            m.started_at < _end_dt(end),
        )
        totals = self.db.execute(totals_stmt).one()

        per_model_stmt = (
            select(
                m.model_responded.label("model"),
                m.provider.label("provider"),
                m.role.label("role"),
                func.count().label("call_count"),
                func.coalesce(func.sum(m.cost_usd), 0).label("cost_usd"),
                func.coalesce(
                    func.avg(m.input_tokens),
                    0,
                ).label("avg_input_tokens"),
                func.coalesce(
                    func.avg(m.output_tokens),
                    0,
                ).label("avg_output_tokens"),
            )
            .where(
                m.tenant_id == tenant_id,
                m.started_at >= _start_dt(start),
                m.started_at < _end_dt(end),
            )
            .group_by(
                m.model_responded,
                m.provider,
                m.role,
            )
            .order_by(func.sum(m.cost_usd).desc())
        )
        per_model_rows = self.db.execute(per_model_stmt).all()

        return TenantDetailRow(
            tenant_id=tenant_id,
            call_count=int(totals.call_count or 0),
            turn_count=int(totals.turn_count or 0),
            conversation_count=int(totals.conversation_count or 0),
            cost_usd=_to_decimal(totals.cost_usd),
            cost_tenant_currency=_to_decimal(totals.cost_tenant_currency),
            tenant_currency=totals.tenant_currency,
            error_count=int(totals.error_count or 0),
            by_model=[
                ModelCostRow(
                    model=row.model,
                    provider=row.provider,
                    role=row.role,
                    call_count=int(row.call_count),
                    cost_usd=_to_decimal(row.cost_usd),
                    avg_input_tokens=int(row.avg_input_tokens or 0),
                    avg_output_tokens=int(row.avg_output_tokens or 0),
                )
                for row in per_model_rows
            ],
        )

    def top_conversations_by_cost(
        self,
        *,
        tenant_id: UUID,
        start: dt.date,
        end: dt.date,
        limit: int = 20,
    ) -> list[ConversationCostRow]:
        """Return top-``limit`` conversations ordered by cost desc.

        Only valid for agents whose model exposes ``conversation_id``
        (copilot). Raises ``AttributeError`` for agents without it —
        sales callers should use :meth:`top_leads_by_cost` instead.
        """
        if not self._has_conversation_id:
            msg = f"{self.model.__name__} has no conversation_id column. Use top_leads_by_cost."
            raise AttributeError(msg)
        m = self.model
        stmt = (
            select(
                m.conversation_id.label("conversation_id"),
                func.count().label("call_count"),
                func.count(func.distinct(m.turn_id)).label("turn_count"),
                func.coalesce(func.sum(m.cost_usd), 0).label("cost_usd"),
                func.max(m.started_at).label("last_seen"),
            )
            .where(
                m.tenant_id == tenant_id,
                m.started_at >= _start_dt(start),
                m.started_at < _end_dt(end),
                m.conversation_id.is_not(None),
            )
            .group_by(m.conversation_id)
            .order_by(func.sum(m.cost_usd).desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        return [
            ConversationCostRow(
                conversation_id=row.conversation_id,
                call_count=int(row.call_count),
                turn_count=int(row.turn_count),
                cost_usd=_to_decimal(row.cost_usd),
                last_seen=row.last_seen,
            )
            for row in rows
        ]

    def top_leads_by_cost(
        self,
        *,
        tenant_id: UUID,
        start: dt.date,
        end: dt.date,
        limit: int = 20,
    ) -> list[LeadCostRow]:
        """Return top-``limit`` leads ordered by cost desc.

        Only valid for agents whose model exposes ``lead_id``
        (sales_agent). Raises ``AttributeError`` otherwise.
        """
        if not self._has_lead_id:
            msg = f"{self.model.__name__} has no lead_id column. Use top_conversations_by_cost."
            raise AttributeError(msg)
        m = self.model
        stmt = (
            select(
                m.lead_id.label("lead_id"),
                func.count().label("call_count"),
                func.count(func.distinct(m.turn_id)).label("turn_count"),
                func.coalesce(func.sum(m.cost_usd), 0).label("cost_usd"),
                func.max(m.started_at).label("last_seen"),
            )
            .where(
                m.tenant_id == tenant_id,
                m.started_at >= _start_dt(start),
                m.started_at < _end_dt(end),
            )
            .group_by(m.lead_id)
            .order_by(func.sum(m.cost_usd).desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        return [
            LeadCostRow(
                lead_id=row.lead_id,
                call_count=int(row.call_count),
                turn_count=int(row.turn_count),
                cost_usd=_to_decimal(row.cost_usd),
                last_seen=row.last_seen,
            )
            for row in rows
        ]

    def daily_series(
        self,
        *,
        tenant_id: UUID,
        start: dt.date,
        end: dt.date,
    ) -> list[DailyCostPoint]:
        """Return per-day cost points for the line chart."""
        m = self.model
        day_expr = func.date(m.started_at).label("day")
        stmt = (
            select(
                day_expr,
                func.coalesce(func.sum(m.cost_usd), 0).label("cost_usd"),
                func.count().label("call_count"),
            )
            .where(
                m.tenant_id == tenant_id,
                m.started_at >= _start_dt(start),
                m.started_at < _end_dt(end),
            )
            .group_by(day_expr)
            .order_by(day_expr)
        )
        rows = self.db.execute(stmt).all()
        return [
            DailyCostPoint(
                day=_coerce_date(row.day),
                cost_usd=_to_decimal(row.cost_usd),
                call_count=int(row.call_count),
            )
            for row in rows
        ]


# ── Cross-agent aggregator ──────────────────────────────────────────────


@dataclass(frozen=True)
class AgentBreakdown:
    """Per-agent cost slice for cross-agent reporting."""

    agent_kind: str
    cost_usd: Decimal
    call_count: int
    turn_count: int


@dataclass(frozen=True)
class CrossAgentTenantCost:
    """Cross-agent total + breakdown for a single tenant in a window."""

    tenant_id: UUID
    cost_usd: Decimal
    call_count: int
    turn_count: int
    by_agent: list[AgentBreakdown] = field(default_factory=list)


class CrossAgentCostAggregator:
    """Compose per-agent :class:`CostAggregator` instances.

    Pulls from :func:`agent_observability_registry` so adding a new
    agent automatically lights up cross-agent reporting without
    touching this class.
    """

    def __init__(self, db: Session) -> None:
        """Bind to a session and instantiate one aggregator per agent."""
        from luana_core_observability.registry import (
            agent_observability_registry,
        )

        self.db = db
        self._aggregators: dict[str, CostAggregator] = {
            spec.agent_kind: CostAggregator(db, spec.llm_call_model) for spec in agent_observability_registry()
        }

    def aggregators_by_kind(self) -> dict[str, CostAggregator]:
        """Return the per-agent aggregator map (read-only intent)."""
        return dict(self._aggregators)

    def tenant_breakdown(
        self,
        *,
        tenant_id: UUID,
        start: dt.date,
        end: dt.date,
    ) -> CrossAgentTenantCost:
        """Sum the per-agent details for one tenant + window."""
        breakdowns: list[AgentBreakdown] = []
        total_cost = Decimal(0)
        total_calls = 0
        total_turns = 0
        for kind, agg in self._aggregators.items():
            detail = agg.tenant_detail(tenant_id=tenant_id, start=start, end=end)
            breakdowns.append(
                AgentBreakdown(
                    agent_kind=kind,
                    cost_usd=detail.cost_usd,
                    call_count=detail.call_count,
                    turn_count=detail.turn_count,
                ),
            )
            total_cost += detail.cost_usd
            total_calls += detail.call_count
            total_turns += detail.turn_count
        return CrossAgentTenantCost(
            tenant_id=tenant_id,
            cost_usd=total_cost,
            call_count=total_calls,
            turn_count=total_turns,
            by_agent=breakdowns,
        )

    def tenants_summary_by_agent(
        self,
        *,
        start: dt.date,
        end: dt.date,
    ) -> dict[str, list[TenantCostRow]]:
        """Return ``tenants_summary`` per agent_kind."""
        return {kind: agg.tenants_summary(start=start, end=end) for kind, agg in self._aggregators.items()}


__all__ = [
    "AgentBreakdown",
    "ConversationCostRow",
    "CostAggregator",
    "CrossAgentCostAggregator",
    "CrossAgentTenantCost",
    "DailyCostPoint",
    "LeadCostRow",
    "ModelCostRow",
    "TenantCostRow",
    "TenantDetailRow",
]
