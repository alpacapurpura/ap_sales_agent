"""Tick-based scheduler that evaluates which tenants are due for extraction.

Runs every minute via ARQ cron. For each active tenant, checks if the
current UTC time corresponds to 3:00 AM in the tenant's local timezone.
Enqueues extraction jobs ordered by extraction_priority (higher first).
"""

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

logger = logging.getLogger(__name__)


async def run_tick_scheduler(ctx: dict) -> None:
    """Evaluate all tenants and enqueue extractions for those at 3am local time."""
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel

    db_factory = ctx["db_factory"]
    db = db_factory()
    enqueued = 0

    try:
        # Query tenants ordered by extraction_priority DESC (premium first)
        stmt = (
            select(TenantModel)
            .where(TenantModel.is_active.is_(True))
            .order_by(TenantModel.extraction_priority.desc())
        )
        result = db.execute(stmt)
        tenants = result.scalars().all()

        now_utc = datetime.now(timezone.utc)

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

            # Check if it's 3:00 AM in the tenant's local timezone (hour=3, minute=0)
            if local_time.hour == 3 and local_time.minute == 0:
                # Enqueue extraction job via ARQ
                redis = ctx.get("redis")
                if redis:
                    await redis.enqueue_job(
                        "run_tenant_extraction",
                        str(tenant.id),
                        "all",  # provider: extract from all connected providers
                    )
                enqueued += 1

        logger.info(
            "Scheduler tick: checked %d tenants, enqueued %d extractions",
            len(tenants),
            enqueued,
        )
    finally:
        db.close()
