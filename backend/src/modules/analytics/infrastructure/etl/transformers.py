"""ETL transformers — maps staging metrics to official metrics format.

Applies cost_type classification and computes period key columns
for the official_metrics table after validation.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.modules.analytics.domain.period_config import TenantPeriodConfig

logger = logging.getLogger(__name__)


def transform_staging_to_official(
    staging_rows,
    cost_type_fn: Callable[[str, str], str | None],
    extraction_run_id=None,
    stage_slug: str = "attraction",
    period_config: TenantPeriodConfig | None = None,
) -> list[dict]:
    """Transform staging metrics into official metrics format.

    Args:
        staging_rows: List of StagingMetricModel instances.
        cost_type_fn: Callable(channel_slug, stage_slug) -> Optional[CostType value].
        extraction_run_id: UUID of the current extraction run.
        stage_slug: The funnel stage this extraction covers (default: "attraction").
        period_config: Tenant period config for computing period key columns.

    Returns:
        List of dicts ready for OfficialMetricsRepository.upsert_from_staging().
    """
    if period_config is None:
        from src.modules.analytics.domain.period_config import TenantPeriodConfig

        period_config = TenantPeriodConfig()

    official_rows = []

    for row in staging_rows:
        cost_type = cost_type_fn(row.channel_slug, stage_slug)

        metric_date = row.metric_date
        if isinstance(metric_date, str):
            metric_date = date.fromisoformat(metric_date)

        period_keys = period_config.compute_period_keys(metric_date)

        official_dict = {
            "tenant_id": row.tenant_id,
            "provider": row.provider,
            "channel_slug": row.channel_slug,
            "metric_name": row.metric_name,
            "value": row.value,
            "unit": row.unit,
            "currency": row.currency,
            "metric_date": row.metric_date,
            "spend": getattr(row, "spend", None),
            "revenue": getattr(row, "revenue", None),
            "campaign_id": row.campaign_id,
            "ad_set_id": row.ad_set_id,
            "ad_id": row.ad_id,
            "cost_type": cost_type.value if hasattr(cost_type, "value") else cost_type,
            "extra": getattr(row, "extra", {}) or {},
            "source_extraction_run_id": extraction_run_id,
            "iso_week_start": period_keys["iso_week_start"],
            "month_key": period_keys["month_key"],
            "quarter_key": period_keys["quarter_key"],
        }
        official_rows.append(official_dict)

    logger.info(
        "Transformed %d staging rows to official format",
        len(official_rows),
    )
    return official_rows
