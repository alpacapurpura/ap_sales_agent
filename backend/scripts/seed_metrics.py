"""Seed script for ETL metrics tables with realistic test data.

Populates staging_metrics, official_metrics, and metric_aggregations
with 7 days of data for Meta Ads, Google Analytics, and Instagram.

Idempotent: clears and re-seeds on each run.

Usage:
    python -m scripts.seed_metrics
    python scripts/seed_metrics.py
"""

import random
import uuid
from datetime import date, timedelta

from sqlalchemy import delete

# Fixed seed tenant ID for consistency across runs
SEED_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# Metric definitions per provider with realistic ranges
PROVIDER_METRICS = {
    "meta": {
        "channel_slug": "meta-ads",
        "metrics": {
            "impressions": {"min": 5000, "max": 15000, "unit": "count"},
            "clicks": {"min": 100, "max": 500, "unit": "count"},
            "spend": {"min": 50, "max": 200, "unit": "currency", "currency": "USD"},
            "reach": {"min": 3000, "max": 10000, "unit": "count"},
        },
    },
    "google_analytics": {
        "channel_slug": "google-organic",
        "metrics": {
            "sessions": {"min": 200, "max": 1000, "unit": "count"},
            "pageviews": {"min": 500, "max": 3000, "unit": "count"},
            "bounce_rate": {"min": 30, "max": 70, "unit": "percentage"},
        },
    },
    "instagram": {
        "channel_slug": "ig-organic",
        "metrics": {
            "reach": {"min": 1000, "max": 5000, "unit": "count"},
            "impressions": {"min": 2000, "max": 8000, "unit": "count"},
            "profile_views": {"min": 100, "max": 500, "unit": "count"},
        },
    },
}


def seed_data(db) -> dict:
    """Seed all ETL tables with test data.

    Args:
        db: SQLAlchemy session.

    Returns:
        dict with counts of seeded rows.
    """
    from luana_core_analytics_engine.infrastructure.models.metric_aggregation_model import (
        MetricAggregationModel,
    )
    from luana_core_analytics_engine.infrastructure.models.official_metrics_model import (
        OfficialMetricModel,
    )
    from luana_core_analytics_engine.infrastructure.models.staging_metrics_model import (
        StagingMetricModel,
    )

    # --- Idempotent: clear existing seed data ---
    db.execute(delete(StagingMetricModel).where(StagingMetricModel.tenant_id == SEED_TENANT_ID))
    db.execute(delete(OfficialMetricModel).where(OfficialMetricModel.tenant_id == SEED_TENANT_ID))
    db.execute(delete(MetricAggregationModel).where(MetricAggregationModel.tenant_id == SEED_TENANT_ID))

    today = date.today()
    staging_rows = []
    official_rows = []
    aggregation_rows = []

    random.seed(42)  # Deterministic random for reproducible seeds

    # --- Generate 7 days of data per provider ---
    for day_offset in range(1, 8):  # Yesterday back to 7 days ago
        metric_date = today - timedelta(days=day_offset)

        for provider_name, provider_config in PROVIDER_METRICS.items():
            channel_slug = provider_config["channel_slug"]

            for metric_name, metric_def in provider_config["metrics"].items():
                value = round(random.uniform(metric_def["min"], metric_def["max"]), 2)
                unit = metric_def["unit"]
                currency = metric_def.get("currency")

                # Spend value for monetary metrics
                spend_value = {"amount": value, "currency": currency} if unit == "currency" else None

                staging_row = StagingMetricModel(
                    id=uuid.uuid4(),
                    tenant_id=SEED_TENANT_ID,
                    provider=provider_name,
                    channel_slug=channel_slug,
                    metric_name=metric_name,
                    value=value,
                    unit=unit,
                    currency=currency,
                    metric_date=metric_date,
                    spend=spend_value,
                )
                staging_rows.append(staging_row)

                # Official metrics mirror staging (transformed)
                official_row = OfficialMetricModel(
                    id=uuid.uuid4(),
                    tenant_id=SEED_TENANT_ID,
                    provider=provider_name,
                    channel_slug=channel_slug,
                    metric_name=metric_name,
                    value=value,
                    unit=unit,
                    currency=currency,
                    metric_date=metric_date,
                    spend=spend_value,
                    cost_type="investment" if provider_name == "meta" else "neutral",
                )
                official_rows.append(official_row)

    db.add_all(staging_rows)
    db.add_all(official_rows)

    # --- Generate aggregations: daily entries + monthly rollup ---
    for provider_name, provider_config in PROVIDER_METRICS.items():
        channel_slug = provider_config["channel_slug"]

        for metric_name, metric_def in provider_config["metrics"].items():
            # Daily aggregations (one per day for 7 days)
            for day_offset in range(1, 8):
                metric_date = today - timedelta(days=day_offset)
                value = round(random.uniform(metric_def["min"], metric_def["max"]), 2)

                agg_row = MetricAggregationModel(
                    id=uuid.uuid4(),
                    tenant_id=SEED_TENANT_ID,
                    channel_slug=channel_slug,
                    metric_name=metric_name,
                    period_type="daily",
                    period_start=metric_date,
                    period_end=metric_date,
                    value=value,
                    unit=metric_def["unit"],
                    currency=metric_def.get("currency"),
                    cost_type="investment" if provider_name == "meta" else "neutral",
                )
                aggregation_rows.append(agg_row)

            # Monthly rollup
            month_start = today.replace(day=1)
            monthly_value = round(random.uniform(metric_def["min"] * 20, metric_def["max"] * 30), 2)
            monthly_agg = MetricAggregationModel(
                id=uuid.uuid4(),
                tenant_id=SEED_TENANT_ID,
                channel_slug=channel_slug,
                metric_name=metric_name,
                period_type="monthly",
                period_start=month_start,
                period_end=today,
                value=monthly_value,
                unit=metric_def["unit"],
                currency=metric_def.get("currency"),
                cost_type="investment" if provider_name == "meta" else "neutral",
            )
            aggregation_rows.append(monthly_agg)

    db.add_all(aggregation_rows)
    db.commit()

    counts = {
        "staging": len(staging_rows),
        "official": len(official_rows),
        "aggregations": len(aggregation_rows),
    }
    return counts


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")

    from luana_core_platform.core.database import SessionLocal

    db = SessionLocal()
    try:
        counts = seed_data(db)
        print(
            f"Seeded {counts['staging']} staging, {counts['official']} official, "
            f"{counts['aggregations']} aggregation rows for tenant {SEED_TENANT_ID}"
        )
    finally:
        db.close()
