"""Catalog-aware helpers for computing cross-channel metric totals.

Used by metrics_service.py to aggregate channel metrics into group totals.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import structlog
from luana_core_analytics_engine.domain.enums import AggregationType
from luana_core_analytics_engine.domain.metric_catalog import get_metric_def

if TYPE_CHECKING:
    from luana_core_analytics_engine.application.dto.attraction_dto import ChannelMetricDTO

logger = structlog.get_logger(__name__)


def compute_channel_totals(channels: list[ChannelMetricDTO]) -> dict[str, float]:
    """Compute totals across a list of channels, skipping non-additive metrics.

    For ADDITIVE metrics: sum values across channels (clicks, spend, sessions).
    For NON_AGGREGABLE, WEIGHTED_AVERAGE, DERIVED: skip from totals.
    Unknown metrics (not in catalog): sum with a warning.

    Args:
        channels: List of ChannelMetricDTO objects for a channel group.

    Returns:
        Dict mapping metric name to total value (ADDITIVE only).

    """
    totals: dict[str, float] = defaultdict(float)
    skipped: set[str] = set()

    for ch in channels:
        for m in ch.metrics:
            defn = get_metric_def(m.name)
            if defn is None:
                # Unknown metric: include with warning
                logger.warning(
                    "compute_channel_totals: metric '%s' not in METRIC_CATALOG — summing (backward compat)",
                    m.name,
                )
                totals[m.name] += m.value
            elif defn.aggregation == AggregationType.ADDITIVE:
                totals[m.name] += m.value
            else:
                # NON_AGGREGABLE, WEIGHTED_AVERAGE, DERIVED, SNAPSHOT — skip
                skipped.add(m.name)

    if skipped:
        logger.debug(
            "compute_channel_totals: skipped non-additive metrics from totals",
            metrics=sorted(skipped),
        )

    return dict(totals)
