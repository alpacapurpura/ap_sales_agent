"""Per-tenant cross-agent cost alert service.

Iterates every tenant in ``tenant_billing_config`` that has a
``cost_alert_threshold_usd`` set, computes the **cross-agent** cycle
cost via :class:`CrossAgentCostAggregator`, and emits a structlog
``warning`` whenever the combined cost exceeds the threshold. The log
event carries the per-agent breakdown so dashboards can render which
agent burned how much.

Email/Slack delivery is deferred — the structlog row is the alerting
primitive today; downstream alerting infra (Sentry, Slack via webhook)
can subscribe to that event.

S2 evolution: the prior copilot-only service summed ``copilot_llm_call``
in isolation. Cross-agent rollup uses the same threshold but adds
``breakdown_usd_by_agent`` so a tenant whose sales_agent is the cost
driver gets that signal in the alert payload itself.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select

from src.shared.agent_observability.persistence.models.tenant_billing_config_model import (
    TenantBillingConfigModel,
)
from src.shared.agent_observability.reporting.billing_cycle_service import (
    BillingCycleService,
)
from src.shared.agent_observability.reporting.cost_aggregator import (
    CrossAgentCostAggregator,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def _today() -> dt.date:
    return dt.datetime.now(tz=dt.UTC).date()


def check_cost_alerts(db: Session) -> dict[str, Any]:
    """Walk configured tenants, alert when cross-agent cycle cost is over budget."""
    rows = (
        db.execute(
            select(TenantBillingConfigModel).where(
                TenantBillingConfigModel.cost_alert_threshold_usd.is_not(None),
            ),
        )
        .scalars()
        .all()
    )

    svc = BillingCycleService(db)
    cross = CrossAgentCostAggregator(db)

    today = _today()
    tenants_checked = 0
    alerts_emitted = 0

    for cfg in rows:
        if cfg.cost_alert_threshold_usd is None:  # pragma: no cover — query already filters
            continue
        tenants_checked += 1

        start, end = svc.compute_window(cfg.tenant_id, today)
        breakdown = cross.tenant_breakdown(
            tenant_id=cfg.tenant_id,
            start=start,
            end=end,
        )

        cost_usd = Decimal(str(breakdown.cost_usd or 0))
        threshold = Decimal(str(cfg.cost_alert_threshold_usd))
        if cost_usd > threshold:
            alerts_emitted += 1
            logger.warning(
                "cost_alert_threshold_exceeded",
                tenant_id=str(cfg.tenant_id),
                cycle_start=start.isoformat(),
                cycle_end=end.isoformat(),
                cost_usd=str(cost_usd),
                threshold_usd=str(threshold),
                billing_currency=cfg.billing_currency,
                breakdown_usd_by_agent={bd.agent_kind: str(bd.cost_usd) for bd in breakdown.by_agent},
            )

    return {
        "tenants_checked": tenants_checked,
        "alerts_emitted": alerts_emitted,
    }


__all__ = ["check_cost_alerts"]
