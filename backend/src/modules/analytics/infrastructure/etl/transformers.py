"""ETL transformers — maps staging metrics to official metrics format.

Applies cost_type classification and prepares data for the
official_metrics table after validation.
"""

import logging
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def transform_staging_to_official(
    staging_rows,
    cost_type_fn: Callable[[str, str], Optional[str]],
    extraction_run_id=None,
    stage_slug: str = "attraction",
) -> List[Dict]:
    """Transform staging metrics into official metrics format.

    Args:
        staging_rows: List of StagingMetricModel instances.
        cost_type_fn: Callable(channel_slug, stage_slug) -> Optional[CostType value].
        extraction_run_id: UUID of the current extraction run.
        stage_slug: The funnel stage this extraction covers (default: "attraction").

    Returns:
        List of dicts ready for OfficialMetricsRepository.upsert_from_staging().
    """
    official_rows = []

    for row in staging_rows:
        cost_type = cost_type_fn(row.channel_slug, stage_slug)

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
        }
        official_rows.append(official_dict)

    logger.info(
        "Transformed %d staging rows to official format",
        len(official_rows),
    )
    return official_rows
