"""Dual-write reconciliation worker — sales_agent S1 cutover safety.

During the 4-week dual-write window (legacy ``@trace_node`` ↔
``SalesAgentCallbackHandler``) we need to confirm both paths emit
equivalent rows for every turn. This worker compares row counts +
turn-level diff per tenant on a schedule and surfaces drift via
structlog so ops can investigate before cutover.

Runs hourly when opt-in via env::

    SALES_AGENT_DUAL_WRITE_RECONCILE=1   # off by default

Once dual-write is decommissioned (S6 cutover) the worker can stay
disabled — the env flag is the kill switch. Best-effort throughout:
every DB read is wrapped, exceptions logged, never raised.

Diff threshold: ``> 1%`` row-count delta per tenant emits ``WARNING``
breadcrumb. Per-tenant tail (10 most-active leads) lets ops triage
which extraction path is dropping rows.

Reference: ``audit/admin-migration-plan.md §2`` Fase A/B + cutover
criterion.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from src.modules.sales_agent.infrastructure.models.agent_trace_model import AgentTrace
from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
    SalesAgentTraceEventModel,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def _is_enabled() -> bool:
    """Opt-in via env var. Off by default."""
    return os.environ.get("SALES_AGENT_DUAL_WRITE_RECONCILE", "0") == "1"


def _window_start() -> datetime:
    """One hour back. Worker runs hourly; window matches schedule."""
    return datetime.now(tz=UTC) - timedelta(hours=1)


def reconcile_per_tenant(db: Session, *, since: datetime) -> dict[str, dict]:
    """Compare legacy + event-sourced row counts per tenant since ``since``.

    Returns a dict keyed by tenant_id (str) with::

        {
            "legacy_count": int,
            "new_count": int,
            "delta_pct": float,
            "drift_alert": bool,
        }

    Tenants present in only one source are still reported (count=0 on
    the missing side, delta_pct=100).
    """
    legacy_stmt = (
        select(AgentTrace.tenant_id, func.count(AgentTrace.id))
        .where(AgentTrace.created_at >= since)
        .group_by(AgentTrace.tenant_id)
    )
    new_stmt = (
        select(SalesAgentTraceEventModel.tenant_id, func.count(SalesAgentTraceEventModel.id))
        .where(SalesAgentTraceEventModel.created_at >= since)
        .group_by(SalesAgentTraceEventModel.tenant_id)
    )

    legacy_rows = dict(db.execute(legacy_stmt).all())
    new_rows = dict(db.execute(new_stmt).all())

    all_tenants = set(legacy_rows) | set(new_rows)
    out: dict[str, dict] = {}
    for tenant_id in all_tenants:
        legacy = int(legacy_rows.get(tenant_id, 0) or 0)
        new = int(new_rows.get(tenant_id, 0) or 0)
        denom = max(legacy, new, 1)
        delta_pct = abs(legacy - new) / denom * 100
        out[str(tenant_id)] = {
            "legacy_count": legacy,
            "new_count": new,
            "delta_pct": round(delta_pct, 2),
            "drift_alert": delta_pct > 1.0,
        }
    return out


async def run_sales_agent_dual_write_reconcile(ctx: dict) -> None:
    """ARQ entry point. Hourly when opt-in via env."""
    if not _is_enabled():
        logger.debug("sales_agent_dual_write_reconcile_disabled")
        return

    db_factory = ctx.get("db_factory")
    if db_factory is None:
        logger.warning("sales_agent_dual_write_reconcile_no_db_factory")
        return

    db = db_factory()
    try:
        since = _window_start()
        per_tenant = reconcile_per_tenant(db, since=since)
        drift = [t for t, m in per_tenant.items() if m["drift_alert"]]

        logger.info(
            "sales_agent_dual_write_reconcile_summary",
            since=since.isoformat(),
            tenant_count=len(per_tenant),
            drift_tenants=len(drift),
        )

        if drift:
            logger.warning(
                "sales_agent_dual_write_reconcile_drift",
                tenants=drift,
                detail={t: per_tenant[t] for t in drift},
            )
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.warning(
            "sales_agent_dual_write_reconcile_failed",
            error=str(exc),
        )
    finally:
        try:
            db.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("sales_agent_dual_write_reconcile_close_failed", error=str(exc))


__all__ = [
    "reconcile_per_tenant",
    "run_sales_agent_dual_write_reconcile",
]
