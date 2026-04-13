"""Tick-based scheduler that evaluates which tenants are due for extraction.

Runs every minute via ARQ cron. For each active tenant, checks if the
current UTC time corresponds to 3:00 AM in the tenant's local timezone.
Enqueues extraction jobs ordered by extraction_priority (higher first).

Also detects period boundaries (week/month/quarter end) and enqueues
period extraction jobs for NON_AGGREGABLE metrics.
"""

import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from src.modules.analytics.application.config import CacheConfig, ETLConfig
from src.modules.analytics.domain.period_config import TenantPeriodConfig

logger = logging.getLogger(__name__)


async def run_tick_scheduler(ctx: dict) -> None:
    """Evaluate all tenants and enqueue extractions for those at 3am local time."""
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel

    db_factory = ctx["db_factory"]
    db = db_factory()
    enqueued = 0
    period_enqueued = 0

    try:
        # Query tenants ordered by extraction_priority DESC (premium first)
        stmt = (
            select(TenantModel).where(TenantModel.is_active.is_(True)).order_by(TenantModel.extraction_priority.desc())
        )
        result = db.execute(stmt)
        tenants = result.scalars().all()

        now_utc = datetime.now(UTC)

        for tenant in tenants:
            tz_name = tenant.timezone or "UTC"
            try:
                tz = ZoneInfo(tz_name)
            except (KeyError, ValueError):
                logger.warning(
                    "Invalid timezone %s for tenant %s, skipping",
                    tz_name,
                    tenant.id,
                )
                continue

            local_time = now_utc.astimezone(tz)

            # Check if it's extraction time in the tenant's local timezone
            if local_time.hour == ETLConfig.DAILY_EXTRACTION_HOUR_LOCAL and local_time.minute == 0:
                redis = ctx.get("redis")
                if not redis:
                    continue

                # Enqueue daily extraction job via ARQ
                await redis.enqueue_job(
                    "run_tenant_extraction",
                    str(tenant.id),
                    "all",
                )

                # Enqueue campaign hierarchy sync (campaigns, ad sets, ads)
                await redis.enqueue_job(
                    "run_campaign_sync",
                    str(tenant.id),
                    "meta",
                )
                enqueued += 1

                # ── Period boundary detection ──
                yesterday = local_time.date() - timedelta(days=1)
                config = TenantPeriodConfig(
                    weekly_start_day=tenant.weekly_start_day or 0,
                    fiscal_year_start_month=tenant.fiscal_year_start_month or 1,
                    fiscal_year_start_day=tenant.fiscal_year_start_day or 1,
                )

                # Weekly: if yesterday was the last day of a week
                if config.is_period_boundary(yesterday, "weekly"):
                    ws, we = config.get_week_boundaries(yesterday)
                    await redis.enqueue_job(
                        "run_period_extraction",
                        str(tenant.id),
                        "weekly",
                        ws.isoformat(),
                        we.isoformat(),
                    )
                    period_enqueued += 1

                # Monthly: if yesterday was the last day of a month
                if config.is_period_boundary(yesterday, "monthly"):
                    ms, me = config.get_month_boundaries(yesterday)
                    await redis.enqueue_job(
                        "run_period_extraction",
                        str(tenant.id),
                        "monthly",
                        ms.isoformat(),
                        me.isoformat(),
                    )
                    period_enqueued += 1

                # Quarterly: if yesterday was the last day of a quarter
                if config.is_period_boundary(yesterday, "quarterly"):
                    qs, qe = config.get_quarter_boundaries(yesterday)
                    await redis.enqueue_job(
                        "run_period_extraction",
                        str(tenant.id),
                        "quarterly",
                        qs.isoformat(),
                        qe.isoformat(),
                    )
                    period_enqueued += 1

        logger.info(
            "Scheduler tick: checked %d tenants, enqueued %d extractions, %d period extractions",
            len(tenants),
            enqueued,
            period_enqueued,
        )

        # Heartbeat: /health reads this key to confirm scheduler is alive (TTL 5 min)
        redis_cache = ctx.get("redis_cache")
        if redis_cache:
            redis_cache.setex("scheduler:last_tick", CacheConfig.DETAIL_STAGE_TTL, "1")
    finally:
        db.close()
