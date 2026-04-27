"""Cost aggregator — feeds the costo-copilot Streamlit dashboard.

Reads ``copilot_llm_call`` directly so the same query path works against
SQLite (tests) and Postgres (prod). The materialised view
``mv_daily_llm_cost_per_tenant`` is a Postgres-side performance booster
the aggregator does **not** depend on for correctness — when present it
covers the same shape, but the aggregator falls back to scanning the
table.

Single tenant scope is enforced by callers (``BillingCycleService``);
this layer accepts ``tenant_id`` directly but never *omits* the filter
when one is required.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import case, func, select

from src.modules.copilot.observability.persistence.models.llm_call_model import (
    CopilotLlmCallModel,
)

if TYPE_CHECKING:
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
    """Top-N conversations by cost for the drill-down view."""

    conversation_id: UUID
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


# ── Aggregator ──────────────────────────────────────────────────────────


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


class CostAggregator:
    """Aggregate LLM cost rows for the reporting layer."""

    def __init__(self, db: Session) -> None:
        """Bind the aggregator to a session."""
        self.db = db

    def tenants_summary(
        self,
        *,
        start: dt.date,
        end: dt.date,
    ) -> list[TenantCostRow]:
        """Return one row per tenant active in ``[start, end_exclusive)``."""
        stmt = (
            select(
                CopilotLlmCallModel.tenant_id.label("tenant_id"),
                func.count().label("call_count"),
                func.count(func.distinct(CopilotLlmCallModel.turn_id)).label("turn_count"),
                func.count(func.distinct(CopilotLlmCallModel.conversation_id)).label(
                    "conversation_count",
                ),
                func.coalesce(func.sum(CopilotLlmCallModel.cost_usd), 0).label("cost_usd"),
                func.coalesce(
                    func.sum(CopilotLlmCallModel.cost_tenant_currency),
                    0,
                ).label("cost_tenant_currency"),
                func.max(CopilotLlmCallModel.tenant_currency).label("tenant_currency"),
                func.coalesce(
                    func.sum(case((CopilotLlmCallModel.status == "error", 1), else_=0)),
                    0,
                ).label("error_count"),
            )
            .where(
                CopilotLlmCallModel.started_at >= _start_dt(start),
                CopilotLlmCallModel.started_at < _end_dt(end),
            )
            .group_by(CopilotLlmCallModel.tenant_id)
            .order_by(func.sum(CopilotLlmCallModel.cost_usd).desc())
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
        totals_stmt = select(
            func.count().label("call_count"),
            func.count(func.distinct(CopilotLlmCallModel.turn_id)).label("turn_count"),
            func.count(func.distinct(CopilotLlmCallModel.conversation_id)).label(
                "conversation_count",
            ),
            func.coalesce(func.sum(CopilotLlmCallModel.cost_usd), 0).label("cost_usd"),
            func.coalesce(
                func.sum(CopilotLlmCallModel.cost_tenant_currency),
                0,
            ).label("cost_tenant_currency"),
            func.max(CopilotLlmCallModel.tenant_currency).label("tenant_currency"),
            func.coalesce(
                func.sum(case((CopilotLlmCallModel.status == "error", 1), else_=0)),
                0,
            ).label("error_count"),
        ).where(
            CopilotLlmCallModel.tenant_id == tenant_id,
            CopilotLlmCallModel.started_at >= _start_dt(start),
            CopilotLlmCallModel.started_at < _end_dt(end),
        )
        totals = self.db.execute(totals_stmt).one()

        per_model_stmt = (
            select(
                CopilotLlmCallModel.model_responded.label("model"),
                CopilotLlmCallModel.provider.label("provider"),
                CopilotLlmCallModel.role.label("role"),
                func.count().label("call_count"),
                func.coalesce(func.sum(CopilotLlmCallModel.cost_usd), 0).label("cost_usd"),
                func.coalesce(
                    func.avg(CopilotLlmCallModel.input_tokens),
                    0,
                ).label("avg_input_tokens"),
                func.coalesce(
                    func.avg(CopilotLlmCallModel.output_tokens),
                    0,
                ).label("avg_output_tokens"),
            )
            .where(
                CopilotLlmCallModel.tenant_id == tenant_id,
                CopilotLlmCallModel.started_at >= _start_dt(start),
                CopilotLlmCallModel.started_at < _end_dt(end),
            )
            .group_by(
                CopilotLlmCallModel.model_responded,
                CopilotLlmCallModel.provider,
                CopilotLlmCallModel.role,
            )
            .order_by(func.sum(CopilotLlmCallModel.cost_usd).desc())
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
        """Return top-``limit`` conversations ordered by cost desc."""
        stmt = (
            select(
                CopilotLlmCallModel.conversation_id.label("conversation_id"),
                func.count().label("call_count"),
                func.count(func.distinct(CopilotLlmCallModel.turn_id)).label("turn_count"),
                func.coalesce(func.sum(CopilotLlmCallModel.cost_usd), 0).label("cost_usd"),
                func.max(CopilotLlmCallModel.started_at).label("last_seen"),
            )
            .where(
                CopilotLlmCallModel.tenant_id == tenant_id,
                CopilotLlmCallModel.started_at >= _start_dt(start),
                CopilotLlmCallModel.started_at < _end_dt(end),
                CopilotLlmCallModel.conversation_id.is_not(None),
            )
            .group_by(CopilotLlmCallModel.conversation_id)
            .order_by(func.sum(CopilotLlmCallModel.cost_usd).desc())
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

    def daily_series(
        self,
        *,
        tenant_id: UUID,
        start: dt.date,
        end: dt.date,
    ) -> list[DailyCostPoint]:
        """Return per-day cost points for the line chart."""
        day_expr = func.date(CopilotLlmCallModel.started_at).label("day")
        stmt = (
            select(
                day_expr,
                func.coalesce(func.sum(CopilotLlmCallModel.cost_usd), 0).label("cost_usd"),
                func.count().label("call_count"),
            )
            .where(
                CopilotLlmCallModel.tenant_id == tenant_id,
                CopilotLlmCallModel.started_at >= _start_dt(start),
                CopilotLlmCallModel.started_at < _end_dt(end),
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


__all__ = [
    "ConversationCostRow",
    "CostAggregator",
    "DailyCostPoint",
    "ModelCostRow",
    "TenantCostRow",
    "TenantDetailRow",
]
